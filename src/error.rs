use pyo3::prelude::*;
use pyo3::exceptions::PyRuntimeError;
use crate::parser::Mark;

/// Specific YAML error types
#[derive(Debug, Clone)]
pub enum YamlErrorType {
    // Parsing errors
    ScannerError,
    ParserError, 
    ComposerError,
    ConstructorError,
    
    // Serialization errors
    RepresenterError,
    EmitterError,
    SerializerError,
    
    // IO and encoding errors
    ReaderError,
    EncodingError,
    
    // Semantic errors
    DuplicateAnchorError,
    UnknownAliasError,
    CircularReferenceError,
    InvalidTagError,
    TypeMismatchError,
    
    // Structure errors
    InvalidDocumentError,
    MalformedYamlError,
    UnexpectedTokenError,
    
    // Multi-document errors
    MultiDocumentError,
    
    // General errors
    InternalError,
    ConfigurationError,
}

impl YamlErrorType {
    /// Convert to appropriate Python exception
    pub fn to_python_exception_name(&self) -> &'static str {
        match self {
            YamlErrorType::ScannerError | 
            YamlErrorType::ParserError |
            YamlErrorType::MalformedYamlError |
            YamlErrorType::UnexpectedTokenError => "ValueError",
            
            YamlErrorType::TypeMismatchError |
            YamlErrorType::InvalidTagError => "TypeError",
            
            YamlErrorType::ReaderError |
            YamlErrorType::EncodingError => "IOError",
            
            _ => "RuntimeError",
        }
    }
}

/// Complete YAML error with detailed information
#[pyclass]
#[derive(Debug, Clone)]
pub struct YamlError {
    pub error_type: YamlErrorType,
    pub message: String,
    pub start_mark: Option<Mark>,
    pub end_mark: Option<Mark>,
    pub context: Option<String>,
    pub note: Option<String>,
    pub problem_mark: Option<Mark>,
    pub problem_value: Option<String>,
    pub yaml_path: Vec<String>, // Path to problematic element (e.g., ["root", "items", "0", "name"])
}

impl YamlError {
    /// Create basic error
    pub fn new(error_type: YamlErrorType, message: String) -> Self {
        Self {
            error_type,
            message,
            start_mark: None,
            end_mark: None,
            context: None,
            note: None,
            problem_mark: None,
            problem_value: None,
            yaml_path: Vec::new(),
        }
    }
    
    /// Create error with position
    pub fn with_mark(error_type: YamlErrorType, message: String, mark: Mark) -> Self {
        Self {
            error_type,
            message,
            start_mark: Some(mark.clone()),
            end_mark: Some(mark.clone()),
            context: None,
            note: None,
            problem_mark: Some(mark),
            problem_value: None,
            yaml_path: Vec::new(),
        }
    }
    
    /// Create error with range
    pub fn with_range(error_type: YamlErrorType, message: String, start: Mark, end: Mark) -> Self {
        Self {
            error_type,
            message,
            start_mark: Some(start.clone()),
            end_mark: Some(end),
            context: None,
            note: None,
            problem_mark: Some(start),
            problem_value: None,
            yaml_path: Vec::new(),
        }
    }
    
    /// Add context to the error
    pub fn with_context(mut self, context: String) -> Self {
        self.context = Some(context);
        self
    }
    
    /// Add explanatory note
    pub fn with_note(mut self, note: String) -> Self {
        self.note = Some(note);
        self
    }
    
    /// Add problematic value
    pub fn with_problem_value(mut self, value: String) -> Self {
        self.problem_value = Some(value);
        self
    }
    
    /// Add YAML path
    pub fn with_yaml_path(mut self, path: Vec<String>) -> Self {
        self.yaml_path = path;
        self
    }
    
    /// Generate complete and readable error message
    pub fn format_message(&self) -> String {
        let mut parts = Vec::new();
        
        // Error type and main message
        parts.push(format!("{:?}: {}", self.error_type, self.message));
        
        // Problem position
        if let Some(mark) = &self.problem_mark {
            parts.push(format!("  at line {}, column {}", mark.line + 1, mark.column + 1));
        }
        
        // YAML path if available
        if !self.yaml_path.is_empty() {
            parts.push(format!("  in {}", self.yaml_path.join(" -> ")));
        }
        
        // Problematic value
        if let Some(value) = &self.problem_value {
            if value.len() <= 100 {
                parts.push(format!("  problem value: \"{}\"", value));
            } else {
                parts.push(format!("  problem value: \"{}...\"", &value[..97]));
            }
        }
        
        // Contexto adicional
        if let Some(context) = &self.context {
            parts.push(format!("  context: {}", context));
        }
        
        // Nota explicativa
        if let Some(note) = &self.note {
            parts.push(format!("  note: {}", note));
        }
        
        parts.join("\n")
    }
    
    /// Convert to PyErr for Python
    pub fn to_pyerr(&self) -> PyErr {
        PyErr::new::<PyRuntimeError, _>(self.format_message())
    }
}

impl std::fmt::Display for YamlError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self.format_message())
    }
}

impl std::error::Error for YamlError {}

impl From<YamlError> for PyErr {
    fn from(err: YamlError) -> PyErr {
        err.to_pyerr()
    }
}

/// Resultado YAML personalizado
pub type YamlResult<T> = Result<T, YamlError>;

/// Builder to easily construct complex errors
pub struct YamlErrorBuilder {
    error: YamlError,
}

impl YamlErrorBuilder {
    pub fn new(error_type: YamlErrorType, message: String) -> Self {
        Self {
            error: YamlError::new(error_type, message),
        }
    }
    
    pub fn with_mark(mut self, mark: Mark) -> Self {
        self.error.start_mark = Some(mark.clone());
        self.error.end_mark = Some(mark.clone());
        self.error.problem_mark = Some(mark);
        self
    }
    
    pub fn with_range(mut self, start: Mark, end: Mark) -> Self {
        self.error.start_mark = Some(start.clone());
        self.error.end_mark = Some(end);
        self.error.problem_mark = Some(start);
        self
    }
    
    pub fn with_context(mut self, context: String) -> Self {
        self.error.context = Some(context);
        self
    }
    
    pub fn with_note(mut self, note: String) -> Self {
        self.error.note = Some(note);
        self
    }
    
    pub fn with_problem_value(mut self, value: String) -> Self {
        self.error.problem_value = Some(value);
        self
    }
    
    pub fn with_yaml_path(mut self, path: Vec<String>) -> Self {
        self.error.yaml_path = path;
        self
    }
    
    pub fn build(self) -> YamlError {
        self.error
    }
}

/// Pre-defined specific errors for common cases

/// Error de scanner
pub fn scanner_error(message: String, mark: Mark) -> YamlError {
    YamlErrorBuilder::new(YamlErrorType::ScannerError, message)
        .with_mark(mark)
        .with_note("Check for invalid characters or malformed tokens".to_string())
        .build()
}

/// Error de parser
pub fn parser_error(message: String, mark: Mark, context: Option<String>) -> YamlError {
    let mut builder = YamlErrorBuilder::new(YamlErrorType::ParserError, message)
        .with_mark(mark)
        .with_note("Check YAML syntax and structure".to_string());
    
    if let Some(ctx) = context {
        builder = builder.with_context(ctx);
    }
    
    builder.build()
}

/// Error de composer
pub fn composer_error(message: String, mark: Option<Mark>, yaml_path: Vec<String>) -> YamlError {
    let mut builder = YamlErrorBuilder::new(YamlErrorType::ComposerError, message)
        .with_yaml_path(yaml_path)
        .with_note("Check document structure and references".to_string());
    
    if let Some(mark) = mark {
        builder = builder.with_mark(mark);
    }
    
    builder.build()
}

/// Alias not found error
pub fn unknown_alias_error(alias_name: String, mark: Mark) -> YamlError {
    YamlErrorBuilder::new(YamlErrorType::UnknownAliasError, 
                         format!("Unknown alias: '{}'", alias_name))
        .with_mark(mark)
        .with_problem_value(alias_name.clone())
        .with_note(format!("Alias '{}' must be defined before use with &{}", alias_name, alias_name))
        .build()
}

/// Duplicate anchor error
pub fn duplicate_anchor_error(anchor_name: String, mark: Mark, previous_mark: Mark) -> YamlError {
    YamlErrorBuilder::new(YamlErrorType::DuplicateAnchorError,
                         format!("Duplicate anchor: '{}'", anchor_name))
        .with_mark(mark)
        .with_problem_value(anchor_name.clone())
        .with_context(format!("Previous definition at line {}, column {}", 
                            previous_mark.line + 1, previous_mark.column + 1))
        .with_note("Each anchor must be unique within a document".to_string())
        .build()
}

/// Circular reference error
pub fn circular_reference_error(path: Vec<String>, mark: Mark) -> YamlError {
    YamlErrorBuilder::new(YamlErrorType::CircularReferenceError,
                         "Circular reference detected".to_string())
        .with_mark(mark)
        .with_yaml_path(path.clone())
        .with_context(format!("Reference cycle: {}", path.join(" -> ")))
        .with_note("Remove circular references between anchors and aliases".to_string())
        .build()
}

    /// Invalid type error
pub fn type_mismatch_error(expected: String, found: String, mark: Mark) -> YamlError {
    YamlErrorBuilder::new(YamlErrorType::TypeMismatchError,
                         format!("Type mismatch: expected {}, found {}", expected, found))
        .with_mark(mark)
        .with_problem_value(found.clone())
        .with_note(format!("Value should be of type {}", expected))
        .build()
}

    /// Invalid document error
pub fn invalid_document_error(message: String, mark: Option<Mark>) -> YamlError {
    let mut builder = YamlErrorBuilder::new(YamlErrorType::InvalidDocumentError, message)
        .with_note("Check document structure and YAML version compatibility".to_string());
    
    if let Some(mark) = mark {
        builder = builder.with_mark(mark);
    }
    
    builder.build()
}

/// Error de encoding
pub fn encoding_error(message: String, encoding_name: String) -> YamlError {
    YamlErrorBuilder::new(YamlErrorType::EncodingError, message)
        .with_context(format!("Encoding: {}", encoding_name))
        .with_note("Try specifying the correct encoding or check for BOM".to_string())
        .build()
}

// === FUNCIONES PYTHON INTEGRATION ===

/// Create custom error from Python
#[pyfunction]
pub fn create_yaml_error(error_type: String, message: String, line: Option<usize>, column: Option<usize>) -> YamlError {
    let yaml_error_type = match error_type.as_str() {
        "scanner" => YamlErrorType::ScannerError,
        "parser" => YamlErrorType::ParserError,
        "composer" => YamlErrorType::ComposerError,
        "constructor" => YamlErrorType::ConstructorError,
        "representer" => YamlErrorType::RepresenterError,
        "emitter" => YamlErrorType::EmitterError,
        "serializer" => YamlErrorType::SerializerError,
        "reader" => YamlErrorType::ReaderError,
        "encoding" => YamlErrorType::EncodingError,
        "duplicate_anchor" => YamlErrorType::DuplicateAnchorError,
        "unknown_alias" => YamlErrorType::UnknownAliasError,
        "circular_reference" => YamlErrorType::CircularReferenceError,
        "invalid_tag" => YamlErrorType::InvalidTagError,
        "type_mismatch" => YamlErrorType::TypeMismatchError,
        "invalid_document" => YamlErrorType::InvalidDocumentError,
        "malformed_yaml" => YamlErrorType::MalformedYamlError,
        "unexpected_token" => YamlErrorType::UnexpectedTokenError,
        "multi_document" => YamlErrorType::MultiDocumentError,
        "configuration" => YamlErrorType::ConfigurationError,
        _ => YamlErrorType::InternalError,
    };
    
    let mut error = YamlError::new(yaml_error_type, message);
    
    if let (Some(line), Some(column)) = (line, column) {
        let mark = Mark::new(line, column, 0);
        error.start_mark = Some(mark.clone());
        error.end_mark = Some(mark.clone());
        error.problem_mark = Some(mark);
    }
    
    error
}

    /// Format error for display
#[pyfunction]
pub fn format_error(error: &YamlError) -> String {
    error.format_message()
} 