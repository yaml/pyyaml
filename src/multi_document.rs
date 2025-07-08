use pyo3::prelude::*;
use pyo3::types::{PyAny, PyList};
use std::collections::VecDeque;
use crate::parser::{parse_rust, PyEvent};
use crate::composer::compose_rust;
use crate::constructor::construct_rust;

/// Error for multi-document
#[derive(Debug)]
pub struct MultiDocumentError {
    pub message: String,
    pub document_index: Option<usize>,
}

impl std::fmt::Display for MultiDocumentError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        if let Some(doc_idx) = self.document_index {
            write!(f, "MultiDocumentError in document {}: {}", doc_idx, self.message)
        } else {
            write!(f, "MultiDocumentError: {}", self.message)
        }
    }
}

impl std::error::Error for MultiDocumentError {}

/// YAML multiple documents processor
#[pyclass]
pub struct MultiDocumentProcessor {
    // Internal state
    current_document_index: usize,
    documents: Vec<Vec<PyEvent>>,
    
    // Configuration
    explicit_document_start: bool,
    explicit_document_end: bool,
    
    // Buffers for performance
    event_buffer: VecDeque<PyEvent>,
    separator_buffer: String,
}

impl Default for MultiDocumentProcessor {
    fn default() -> Self {
        Self {
            current_document_index: 0,
            documents: Vec::new(),
            explicit_document_start: false,
            explicit_document_end: false,
            event_buffer: VecDeque::with_capacity(128),
            separator_buffer: String::with_capacity(16),
        }
    }
}

#[pymethods]
impl MultiDocumentProcessor {
    #[new]
    pub fn new() -> Self {
        Self::default()
    }
    
    /// Configure explicit separators
    pub fn with_explicit_start(&mut self, explicit: bool) {
        self.explicit_document_start = explicit;
    }
    
    pub fn with_explicit_end(&mut self, explicit: bool) {
        self.explicit_document_end = explicit;
    }
    
    /// Clear state
    pub fn reset(&mut self) {
        self.current_document_index = 0;
        self.documents.clear();
        self.event_buffer.clear();
    }
}

impl MultiDocumentProcessor {
    /// Separate event stream into multiple documents
    pub fn split_events(&mut self, events: Vec<PyEvent>) -> Result<Vec<Vec<PyEvent>>, MultiDocumentError> {
        self.reset();
        
        let mut current_doc = Vec::new();
        let mut in_document = false;
        let mut stream_started = false;
        
        for event in &events {
            let event_repr = format!("{:?}", event);
            
            // Detect different types of events
            if event_repr.contains("StreamStart") {
                stream_started = true;
                continue;
            } else if event_repr.contains("StreamEnd") {
                // Finalize current document if it exists
                if !current_doc.is_empty() {
                    self.documents.push(current_doc.clone());
                }
                break;
            } else if event_repr.contains("DocumentStart") {
                // New document
                if in_document && !current_doc.is_empty() {
                    // Save previous document
                    self.documents.push(current_doc.clone());
                    current_doc.clear();
                }
                in_document = true;
                current_doc.push(event.clone());
            } else if event_repr.contains("DocumentEnd") {
                current_doc.push(event.clone());
                // Don't finalize here - there may be more events in the document
            } else {
                // Content events
                if stream_started {
                    current_doc.push(event.clone());
                }
            }
        }
        
        // Add last document if it exists
        if !current_doc.is_empty() {
            self.documents.push(current_doc);
        }
        
        // If there are no explicit documents, everything is one document
        if self.documents.is_empty() && !events.is_empty() {
            self.documents.push(events);
        }
        
        Ok(self.documents.clone())
    }
    
    /// Process YAML string with multiple documents
    pub fn parse_multi_document(&mut self, yaml_content: &str) -> Result<Vec<Vec<PyEvent>>, MultiDocumentError> {
        // Split by explicit separators first
        let document_strings = self.split_yaml_string(yaml_content);
        
        let mut all_documents = Vec::new();
        
        for (doc_index, doc_str) in document_strings.iter().enumerate() {
            if doc_str.trim().is_empty() {
                continue;
            }
            
            // Parse each document individually
            Python::with_gil(|py| {
                let io_module = py.import("io").map_err(|e| MultiDocumentError {
                    message: format!("Failed to import io module: {}", e),
                    document_index: Some(doc_index),
                })?;
                
                let py_string = doc_str.clone();
                let stream = io_module.getattr("StringIO")
                    .and_then(|stringio| stringio.call1((py_string,)))
                    .map_err(|e| MultiDocumentError {
                        message: format!("Failed to create StringIO: {}", e),
                        document_index: Some(doc_index),
                    })?;
                
                let events = parse_rust(py, stream).map_err(|e| MultiDocumentError {
                    message: format!("Failed to parse document: {}", e),
                    document_index: Some(doc_index),
                })?;
                
                all_documents.push(events);
                Ok::<(), MultiDocumentError>(())
            })?;
        }
        
        Ok(all_documents)
    }
    
    /// Split YAML string by document separators
    fn split_yaml_string(&self, yaml_content: &str) -> Vec<String> {
        let mut documents = Vec::new();
        let mut current_doc = String::new();
        let mut at_line_start = true;
        
        for line in yaml_content.lines() {
            let trimmed = line.trim();
            
            // Detect document separator
            if at_line_start && (trimmed == "---" || trimmed.starts_with("--- ")) {
                // Finalize previous document if exists
                if !current_doc.trim().is_empty() {
                    documents.push(current_doc.trim().to_string());
                    current_doc.clear();
                }
                at_line_start = true;
                continue;
            }
            
            // Detect end of document
            if trimmed == "..." {
                current_doc.push_str(line);
                current_doc.push('\n');
                documents.push(current_doc.trim().to_string());
                current_doc.clear();
                at_line_start = true;
                continue;
            }
            
            current_doc.push_str(line);
            current_doc.push('\n');
            at_line_start = trimmed.is_empty();
        }
        
        // Add last document
        if !current_doc.trim().is_empty() {
            documents.push(current_doc.trim().to_string());
        }
        
        // If there are no separate documents, return everything as one document
        if documents.is_empty() && !yaml_content.trim().is_empty() {
            documents.push(yaml_content.to_string());
        }
        
        documents
    }
    
    /// Combine multiple documents into a YAML string
    pub fn combine_documents(&self, document_strings: &[String]) -> String {
        if document_strings.is_empty() {
            return String::new();
        }
        
        if document_strings.len() == 1 {
            return document_strings[0].clone();
        }
        
        let mut result = String::new();
        
        for (i, doc) in document_strings.iter().enumerate() {
            if i > 0 {
                result.push_str("---\n");
            }
            result.push_str(doc.trim());
            result.push('\n');
        }
        
        result
    }
    
    /// Generate appropriate document separators
    pub fn format_document_separator(&self, explicit_start: bool, explicit_end: bool) -> String {
        let mut separator = String::new();
        
        if explicit_start {
            separator.push_str("---\n");
        }
        
        if explicit_end {
            separator.push_str("...\n");
        }
        
        separator
    }
}

// === FUNCIONES PYTHON INTEGRATION ===

/// Load multiple documents from a stream
#[pyfunction]
pub fn load_all_rust(py: Python, stream: Bound<PyAny>) -> PyResult<Vec<Option<PyObject>>> {
    // Read complete content
    let yaml_content = if let Ok(string_content) = stream.call_method0("read") {
        string_content.extract::<String>()?
    } else if let Ok(getvalue) = stream.call_method0("getvalue") {
        getvalue.extract::<String>()?
    } else {
        stream.extract::<String>()?
    };
    
    if yaml_content.trim().is_empty() {
        return Ok(vec![]);
    }
    
    // ✅ NEW LOGIC: Use improved parser that handles multiple documents
          // Create stream from content
    let io_module = py.import("io")?;
    let new_stream = io_module.getattr("StringIO")?.call1((yaml_content,))?;
    
    // Parse all content - the parser now detects multiple documents
    let all_events = parse_rust(py, new_stream)?;
    
    // Separate events by documents based on DocumentStart/DocumentEnd
    let document_event_groups = split_events_by_documents(all_events);
    
    let mut results = Vec::new();
    
    // Process each event group as a document
    for events in document_event_groups {
        if events.is_empty() {
            results.push(None);
            continue;
        }
        
        // Compose and construct each document
        let node_result = compose_rust(py, events)?;
        
        if let Some(node) = node_result {
            let py_object = construct_rust(py, &node)?;
            results.push(Some(py_object));
        } else {
            results.push(None);
        }
    }
    
    Ok(results)
}

/// ✅ NEW FUNCTION: Separate events into groups by document
fn split_events_by_documents(events: Vec<PyEvent>) -> Vec<Vec<PyEvent>> {
    let mut result = Vec::new();
    let mut current_doc = Vec::new();
    let mut in_document = false;
    let mut stream_start_seen = false;
    let mut document_finalized = false;
    
    for event in events {
        let event_repr = format!("{:?}", event);
        
        if event_repr.contains("StreamStart") {
            // Only add StreamStart once at the beginning
            if !stream_start_seen {
                stream_start_seen = true;
                current_doc.push(event);
            }
            continue;
        } else if event_repr.contains("StreamEnd") {
            // ✅ CORRECTION: Finalize current document AND mark as finalized
            if !current_doc.is_empty() && in_document && !document_finalized {
                current_doc.push(event);
                result.push(current_doc.clone());
                document_finalized = true;
            }
            break;
        } else if event_repr.contains("DocumentStart") {
            // New document
            if in_document && !current_doc.is_empty() {
                // Finalize previous document
                current_doc.push(PyEvent {
                    event: crate::parser::Event::StreamEnd {
                        start_mark: crate::parser::Mark::new(0, 0, 0),
                        end_mark: crate::parser::Mark::new(0, 0, 0),
                    }
                });
                result.push(current_doc.clone());
                
                // Reset for new document
                current_doc.clear();
                current_doc.push(PyEvent {
                    event: crate::parser::Event::StreamStart {
                        start_mark: crate::parser::Mark::new(0, 0, 0),
                        end_mark: crate::parser::Mark::new(0, 0, 0),
                        encoding: Some("utf-8".to_string()),
                    }
                });
            }
            in_document = true;
            current_doc.push(event);
        } else if event_repr.contains("DocumentEnd") {
            current_doc.push(event);
            // Don't finalize here - there may be more documents
        } else {
            // Eventos de contenido
            if in_document {
                current_doc.push(event);
            }
        }
    }
    
    // ✅ CORRECTION: Only add if NOT finalized by StreamEnd
    if !current_doc.is_empty() && in_document && !document_finalized {
        // Verificar que no sea solo StreamStart/DocumentStart
        let content_events = current_doc.iter().filter(|e| {
            let repr = format!("{:?}", e);
            !repr.contains("StreamStart") && !repr.contains("DocumentStart") && !repr.contains("DocumentEnd")
        }).count();
        
        if content_events > 0 {
            current_doc.push(PyEvent {
                event: crate::parser::Event::StreamEnd {
                    start_mark: crate::parser::Mark::new(0, 0, 0),
                    end_mark: crate::parser::Mark::new(0, 0, 0),
                }
            });
            result.push(current_doc);
        }
    }
    
    result
}

/// Serialize multiple documents to a stream
#[pyfunction]
pub fn dump_all_rust(py: Python, documents: Bound<PyList>) -> PyResult<String> {
    if documents.len() == 0 {
        return Ok(String::new());
    }
    
    let mut yaml_strings = Vec::new();
    
    // Process each document
    for data in documents.iter() {
        // Use normal dump pipeline
        let node = crate::representer::represent_rust(py, &data)?;
        let yaml_string = crate::emitter::emit_to_string(&node)?;
        yaml_strings.push(yaml_string);
    }
    
            // Combine with separators
    let processor = MultiDocumentProcessor::new();
    Ok(processor.combine_documents(&yaml_strings))
}

/// Dump multiple documents to stream
#[pyfunction]
pub fn dump_all_rust_to_stream(
    py: Python, 
    documents: Bound<PyList>,
    stream: &Bound<PyAny>
) -> PyResult<()> {
    let yaml_string = dump_all_rust(py, documents)?;
    stream.call_method1("write", (yaml_string,))?;
    Ok(())
}

/// Split YAML string into multiple documents
#[pyfunction]
pub fn split_yaml_documents(yaml_content: &str) -> Vec<String> {
    let processor = MultiDocumentProcessor::new();
    processor.split_yaml_string(yaml_content)
}

/// Check if YAML contains multiple documents
#[pyfunction]
pub fn is_multi_document(yaml_content: &str) -> bool {
    yaml_content.contains("---") || yaml_content.contains("...")
} 