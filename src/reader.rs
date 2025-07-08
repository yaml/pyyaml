use pyo3::prelude::*;
use pyo3::types::PyBytes;
use std::io::Read;
use std::fs::File;
use encoding_rs::{Encoding, UTF_8, UTF_16LE, UTF_16BE};

/// Error for advanced reading
#[derive(Debug)]
pub struct ReaderError {
    pub message: String,
    pub line: Option<usize>,
    pub column: Option<usize>,
}

impl std::fmt::Display for ReaderError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        if let (Some(line), Some(col)) = (self.line, self.column) {
            write!(f, "ReaderError at line {}, column {}: {}", line, col, self.message)
        } else {
            write!(f, "ReaderError: {}", self.message)
        }
    }
}

impl std::error::Error for ReaderError {}

/// Detected encoding information
#[derive(Debug, Clone)]
pub struct EncodingInfo {
    pub encoding: &'static Encoding,
    pub has_bom: bool,
    pub bom_length: usize,
    pub confidence: f32,
}

/// Advanced reader with automatic encoding detection
#[pyclass]
pub struct AdvancedReader {
    // Reading state
    content: String,
    position: usize,
    line: usize,
    column: usize,
    
    // Encoding information
    encoding_info: Option<EncodingInfo>,
    
    // Buffer for lookahead
    buffer: Vec<char>,
    buffer_position: usize,
    
    // Configuration
    detect_encoding: bool,
    strip_bom: bool,
    max_lookahead: usize,
}

impl Default for AdvancedReader {
    fn default() -> Self {
        Self {
            content: String::new(),
            position: 0,
            line: 1,
            column: 1,
            encoding_info: None,
            buffer: Vec::with_capacity(1024),
            buffer_position: 0,
            detect_encoding: true,
            strip_bom: true,
            max_lookahead: 1024,
        }
    }
}

#[pymethods]
impl AdvancedReader {
    #[new]
    pub fn new() -> Self {
        Self::default()
    }
    
    /// Configurar opciones del reader
    pub fn with_encoding_detection(&mut self, detect: bool) {
        self.detect_encoding = detect;
    }
    
    pub fn with_bom_stripping(&mut self, strip: bool) {
        self.strip_bom = strip;
    }
    
    pub fn with_max_lookahead(&mut self, max: usize) {
        self.max_lookahead = max;
    }
    
    /// Load content from different sources
    pub fn load_from_string(&mut self, content: &str) -> PyResult<()> {
        self.content = content.to_string();
        self.reset_position();
        Ok(())
    }
    
    pub fn load_from_bytes(&mut self, _py: Python, bytes: &Bound<PyBytes>) -> PyResult<()> {
        let raw_bytes = bytes.as_bytes();
        
        // Detect encoding and BOM
        let encoding_info = if self.detect_encoding {
            self.detect_encoding_from_bytes(raw_bytes)
        } else {
            EncodingInfo {
                encoding: UTF_8,
                has_bom: false,
                bom_length: 0,
                confidence: 1.0,
            }
        };
        
        // Decodificar contenido
        let start_pos = if self.strip_bom && encoding_info.has_bom {
            encoding_info.bom_length
        } else {
            0
        };
        
        let (decoded, _encoding_used, had_errors) = encoding_info.encoding.decode(&raw_bytes[start_pos..]);
        
        if had_errors {
            return Err(PyErr::new::<pyo3::exceptions::PyUnicodeDecodeError, _>(
                format!("Failed to decode content with encoding {}", encoding_info.encoding.name())
            ));
        }
        
        self.content = decoded.into_owned();
        self.encoding_info = Some(encoding_info);
        self.reset_position();
        Ok(())
    }
    
    pub fn load_from_file(&mut self, file_path: &str) -> PyResult<()> {
        let mut file = File::open(file_path)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;
        
        let mut buffer = Vec::new();
        file.read_to_end(&mut buffer)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;
        
        Python::with_gil(|py| {
            let py_bytes = PyBytes::new(py, &buffer);
            self.load_from_bytes(py, &py_bytes)
        })
    }
    
    /// Get encoding information
    pub fn get_encoding_info(&self) -> Option<String> {
        self.encoding_info.as_ref().map(|info| {
            format!("{} (BOM: {}, Confidence: {:.2})", 
                   info.encoding.name(), 
                   info.has_bom, 
                   info.confidence)
        })
    }
    
    /// Reading methods
    pub fn read_all(&self) -> String {
        self.content.clone()
    }
    
    pub fn peek(&mut self, count: usize) -> String {
        self.ensure_buffer(count);
        let end = std::cmp::min(self.buffer_position + count, self.buffer.len());
        self.buffer[self.buffer_position..end].iter().collect()
    }
    
    pub fn read_char(&mut self) -> Option<char> {
        self.ensure_buffer(1);
        if self.buffer_position < self.buffer.len() {
            let ch = self.buffer[self.buffer_position];
            self.buffer_position += 1;
            self.advance_position(ch);
            Some(ch)
        } else {
            None
        }
    }
    
    pub fn read_line(&mut self) -> Option<String> {
        let mut line = String::new();
        
        while let Some(ch) = self.read_char() {
            line.push(ch);
            if ch == '\n' {
                break;
            }
        }
        
        if line.is_empty() {
            None
        } else {
            Some(line)
        }
    }
    
    /// Get current position
    pub fn get_position(&self) -> (usize, usize) {
        (self.line, self.column)
    }
    
    pub fn get_byte_position(&self) -> usize {
        self.position
    }
}

impl AdvancedReader {
    /// Reset reading position
    fn reset_position(&mut self) {
        self.position = 0;
        self.line = 1;
        self.column = 1;
        self.buffer.clear();
        self.buffer_position = 0;
        
        // Llenar buffer inicial
        self.buffer.extend(self.content.chars());
    }
    
    /// Detect encoding from bytes
    fn detect_encoding_from_bytes(&self, bytes: &[u8]) -> EncodingInfo {
        // Check BOM first
        if let Some(bom_info) = self.detect_bom(bytes) {
            return bom_info;
        }
        
        // Heuristic detection
        self.detect_encoding_heuristic(bytes)
    }
    
    /// Detect BOM (Byte Order Mark)
    fn detect_bom(&self, bytes: &[u8]) -> Option<EncodingInfo> {
        if bytes.len() >= 3 {
            // UTF-8 BOM
            if bytes.starts_with(&[0xEF, 0xBB, 0xBF]) {
                return Some(EncodingInfo {
                    encoding: UTF_8,
                    has_bom: true,
                    bom_length: 3,
                    confidence: 1.0,
                });
            }
        }
        
        if bytes.len() >= 2 {
            // UTF-16 BOMs
            if bytes.starts_with(&[0xFE, 0xFF]) {
                return Some(EncodingInfo {
                    encoding: UTF_16BE,
                    has_bom: true,
                    bom_length: 2,
                    confidence: 1.0,
                });
            }
            if bytes.starts_with(&[0xFF, 0xFE]) {
                return Some(EncodingInfo {
                    encoding: UTF_16LE,
                    has_bom: true,
                    bom_length: 2,
                    confidence: 1.0,
                });
            }
        }
        
        None
    }
    
    /// Heuristic encoding detection
    fn detect_encoding_heuristic(&self, bytes: &[u8]) -> EncodingInfo {
        let sample_size = std::cmp::min(bytes.len(), 8192);
        let sample = &bytes[..sample_size];
        
        // Simple heuristic: assume UTF-8 if it's valid, otherwise fall back to UTF-8 with replacement
        if let Ok(_) = std::str::from_utf8(sample) {
            EncodingInfo {
                encoding: UTF_8,
                has_bom: false,
                bom_length: 0,
                confidence: 0.9,
            }
        } else {
            // Could implement more sophisticated detection here
            // For now, default to UTF-8 with replacement
            EncodingInfo {
                encoding: UTF_8,
                has_bom: false,
                bom_length: 0,
                confidence: 0.5,
            }
        }
    }
    
    /// Asegurar que el buffer tiene suficientes caracteres
    fn ensure_buffer(&mut self, _count: usize) {
        // Buffer is already full with all content in reset_position
        // Simplified implementation for this case
    }
    
    /// Advance position after reading a character
    fn advance_position(&mut self, ch: char) {
        self.position += ch.len_utf8();
        
        if ch == '\n' {
            self.line += 1;
            self.column = 1;
        } else {
            self.column += 1;
        }
    }
}

// === FUNCIONES PYTHON INTEGRATION ===

/// Create reader from different sources
#[pyfunction]
pub fn create_reader_from_string(content: &str) -> PyResult<AdvancedReader> {
    let mut reader = AdvancedReader::new();
    reader.load_from_string(content)?;
    Ok(reader)
}

#[pyfunction]
pub fn create_reader_from_bytes(py: Python, bytes: &Bound<PyBytes>) -> PyResult<AdvancedReader> {
    let mut reader = AdvancedReader::new();
    reader.load_from_bytes(py, bytes)?;
    Ok(reader)
}

#[pyfunction] 
pub fn create_reader_from_file(file_path: &str) -> PyResult<AdvancedReader> {
    let mut reader = AdvancedReader::new();
    reader.load_from_file(file_path)?;
    Ok(reader)
}

/// Detect encoding from bytes
#[pyfunction]
pub fn detect_encoding(bytes: &Bound<PyBytes>) -> String {
    let reader = AdvancedReader::new();
    let encoding_info = reader.detect_encoding_from_bytes(bytes.as_bytes());
    
    format!("{} (BOM: {}, Confidence: {:.2})", 
           encoding_info.encoding.name(), 
           encoding_info.has_bom, 
           encoding_info.confidence)
}

/// Check if bytes have BOM
#[pyfunction]
pub fn has_bom(bytes: &Bound<PyBytes>) -> bool {
    let reader = AdvancedReader::new();
    reader.detect_bom(bytes.as_bytes()).is_some()
}

/// Strips BOM de bytes si existe
#[pyfunction]
pub fn strip_bom(py: Python, bytes: &Bound<PyBytes>) -> PyResult<Py<PyBytes>> {
    let reader = AdvancedReader::new();
    let raw_bytes = bytes.as_bytes();
    
    if let Some(bom_info) = reader.detect_bom(raw_bytes) {
        let stripped = &raw_bytes[bom_info.bom_length..];
        Ok(PyBytes::new(py, stripped).into())
    } else {
        Ok(bytes.clone().unbind())
    }
} 