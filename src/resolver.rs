use pyo3::prelude::*;
use pyo3::types::{PyBytes, PyString, PyInt, PyFloat, PyBool};
use std::collections::HashMap;
use regex::Regex;
use chrono::{DateTime, NaiveDate, Utc, Datelike, Timelike};
use base64::{Engine as _, engine::general_purpose};

/// Error for type resolution
#[derive(Debug)]
pub struct ResolverError {
    pub message: String,
}

impl std::fmt::Display for ResolverError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "ResolverError: {}", self.message)
    }
}

impl std::error::Error for ResolverError {}

/// Ultra-advanced resolver for complex YAML types
/// Incluye fechas, timestamps, binary data, merge keys, etc.
#[pyclass]
pub struct AdvancedResolver {
    // Tag resolvers mapping
    tag_resolvers: HashMap<String, TagResolver>,
    
    // Compiled regex patterns for performance
    int_patterns: Vec<Regex>,
    float_patterns: Vec<Regex>, 
    bool_patterns: Vec<Regex>,
    null_patterns: Vec<Regex>,
    timestamp_patterns: Vec<Regex>,
    merge_patterns: Vec<Regex>,
    
    // Cache for frequently used patterns
    pattern_cache: HashMap<String, String>,
}

/// Type of resolver for each tag
#[derive(Debug, Clone)]
enum TagResolver {
    Scalar(fn(&str) -> Option<String>),
    Sequence,
    Mapping,
}

impl Default for AdvancedResolver {
    fn default() -> Self {
        let mut resolver = Self {
            tag_resolvers: HashMap::new(),
            int_patterns: Vec::new(),
            float_patterns: Vec::new(),
            bool_patterns: Vec::new(),
            null_patterns: Vec::new(),
            timestamp_patterns: Vec::new(),
            merge_patterns: Vec::new(),
            pattern_cache: HashMap::with_capacity(64),
        };
        
        resolver.initialize_patterns();
        resolver.initialize_tag_resolvers();
        resolver
    }
}

#[pymethods]
impl AdvancedResolver {
    #[new]
    pub fn new() -> Self {
        Self::default()
    }
    
    /// Main resolver - determine correct YAML tag for a value
    pub fn resolve(&mut self, value: &str, implicit: bool) -> String {
        // Cache check primero
        if let Some(cached_tag) = self.pattern_cache.get(value) {
            return cached_tag.clone();
        }
        
        let tag = if implicit {
            self.resolve_implicit(value)
        } else {
            "tag:yaml.org,2002:str".to_string()
        };
        
        // Cache the result
        self.pattern_cache.insert(value.to_string(), tag.clone());
        tag
    }
    
    /// Resolver for specific tags
    pub fn resolve_tag(&self, tag: &str, value: &str) -> PyResult<PyObject> {
        Python::with_gil(|py| {
            match tag {
                "tag:yaml.org,2002:timestamp" => self.construct_timestamp(py, value),
                "tag:yaml.org,2002:binary" => self.construct_binary(py, value),
                "tag:yaml.org,2002:merge" => self.construct_merge(py, value),
                "tag:yaml.org,2002:int" => self.construct_int(py, value),
                "tag:yaml.org,2002:float" => self.construct_float(py, value),
                "tag:yaml.org,2002:bool" => self.construct_bool(py, value),
                "tag:yaml.org,2002:null" => self.construct_null(py),
                "tag:yaml.org,2002:str" => Ok(PyString::new(py, value).into()),
                _ => Ok(PyString::new(py, value).into()), // Default to string
            }
        })
    }
}

impl AdvancedResolver {
    /// Initialize compiled patterns for performance
    fn initialize_patterns(&mut self) {
        // Integer patterns (base 2, 8, 10, 16)
        self.int_patterns = vec![
            Regex::new(r"^[-+]?[0-9]+$").unwrap(),                    // Decimal
            Regex::new(r"^0b[01_]+$").unwrap(),                       // Binary
            Regex::new(r"^0[0-7_]+$").unwrap(),                       // Octal
            Regex::new(r"^0x[0-9a-fA-F_]+$").unwrap(),               // Hexadecimal
            Regex::new(r"^[-+]?[1-9][0-9_]*$").unwrap(),             // Decimal with underscores
        ];
        
        // Float patterns
        self.float_patterns = vec![
            Regex::new(r"^[-+]?(\.[0-9]+|[0-9]+\.[0-9]*)([eE][-+]?[0-9]+)?$").unwrap(),
            Regex::new(r"^[-+]?[0-9][0-9_]*\.[0-9_]*([eE][-+]?[0-9]+)?$").unwrap(),
            Regex::new(r"^[-+]?\.(inf|Inf|INF)$").unwrap(),          // Infinity
            Regex::new(r"^\.nan|\.NaN|\.NAN$").unwrap(),             // NaN
        ];
        
        // Boolean patterns
        self.bool_patterns = vec![
            Regex::new(r"^(true|True|TRUE|yes|Yes|YES|on|On|ON)$").unwrap(),
            Regex::new(r"^(false|False|FALSE|no|No|NO|off|Off|OFF)$").unwrap(),
        ];
        
        // Null patterns
        self.null_patterns = vec![
            Regex::new(r"^(null|Null|NULL|~|)$").unwrap(),
        ];
        
        // Timestamp patterns (ISO 8601 y variants)
        self.timestamp_patterns = vec![
            // Complete ISO 8601: 2001-12-15T02:59:43.1Z
            Regex::new(r"^[0-9]{4}-[0-9]{1,2}-[0-9]{1,2}[Tt]([0-9]{1,2}:[0-9]{2}:[0-9]{2}(\.[0-9]*)?)?([Zz]|[+-][0-9]{1,2}:[0-9]{2})?$").unwrap(),
            // Date only: 2002-12-14
            Regex::new(r"^[0-9]{4}-[0-9]{1,2}-[0-9]{1,2}$").unwrap(),
            // Canonical timestamp: 2001-12-14 21:59:43.10 -5
            Regex::new(r"^[0-9]{4}-[0-9]{1,2}-[0-9]{1,2} [0-9]{1,2}:[0-9]{2}:[0-9]{2}(\.[0-9]*)? ?([+-][0-9]{1,2})?$").unwrap(),
        ];
        
        // Merge patterns
        self.merge_patterns = vec![
            Regex::new(r"^<<$").unwrap(),
        ];
    }
    
    /// Initialize specific resolvers by tag
    fn initialize_tag_resolvers(&mut self) {
        // Basic tags ya manejados en composer
        self.tag_resolvers.insert("tag:yaml.org,2002:int".to_string(), TagResolver::Scalar(|_| None));
        self.tag_resolvers.insert("tag:yaml.org,2002:float".to_string(), TagResolver::Scalar(|_| None));
        self.tag_resolvers.insert("tag:yaml.org,2002:bool".to_string(), TagResolver::Scalar(|_| None));
        self.tag_resolvers.insert("tag:yaml.org,2002:null".to_string(), TagResolver::Scalar(|_| None));
        self.tag_resolvers.insert("tag:yaml.org,2002:str".to_string(), TagResolver::Scalar(|_| None));
        
        // Advanced tags
        self.tag_resolvers.insert("tag:yaml.org,2002:timestamp".to_string(), TagResolver::Scalar(|_| None));
        self.tag_resolvers.insert("tag:yaml.org,2002:binary".to_string(), TagResolver::Scalar(|_| None));
        self.tag_resolvers.insert("tag:yaml.org,2002:merge".to_string(), TagResolver::Scalar(|_| None));
    }
    
    /// Implicit type resolution
    fn resolve_implicit(&self, value: &str) -> String {
        // Trim whitespace for checking
        let trimmed = value.trim();
        
        // Check null first (most common)
        if self.is_null(trimmed) {
            return "tag:yaml.org,2002:null".to_string();
        }
        
        // Check boolean
        if self.is_bool(trimmed) {
            return "tag:yaml.org,2002:bool".to_string();
        }
        
        // Check timestamp (before int to capture dates)
        if self.is_timestamp(trimmed) {
            return "tag:yaml.org,2002:timestamp".to_string();
        }
        
        // Check integer
        if self.is_int(trimmed) {
            return "tag:yaml.org,2002:int".to_string();
        }
        
        // Check float
        if self.is_float(trimmed) {
            return "tag:yaml.org,2002:float".to_string();
        }
        
        // Check merge key
        if self.is_merge(trimmed) {
            return "tag:yaml.org,2002:merge".to_string();
        }
        
        // Default to string
        "tag:yaml.org,2002:str".to_string()
    }
    
    // === PATTERN CHECKERS ===
    
    fn is_null(&self, value: &str) -> bool {
        self.null_patterns.iter().any(|pattern| pattern.is_match(value))
    }
    
    fn is_bool(&self, value: &str) -> bool {
        self.bool_patterns.iter().any(|pattern| pattern.is_match(value))
    }
    
    fn is_int(&self, value: &str) -> bool {
        self.int_patterns.iter().any(|pattern| pattern.is_match(value))
    }
    
    fn is_float(&self, value: &str) -> bool {
        self.float_patterns.iter().any(|pattern| pattern.is_match(value))
    }
    
    fn is_timestamp(&self, value: &str) -> bool {
        self.timestamp_patterns.iter().any(|pattern| pattern.is_match(value))
    }
    
    fn is_merge(&self, value: &str) -> bool {
        self.merge_patterns.iter().any(|pattern| pattern.is_match(value))
    }
    
    // === CONSTRUCTORS AVANZADOS ===
    
    /// Build timestamp from string
    fn construct_timestamp(&self, py: Python, value: &str) -> PyResult<PyObject> {
        // Try different timestamp formats
        let trimmed = value.trim();
        
        // Format 1: ISO 8601 with timezone
        if let Ok(dt) = DateTime::parse_from_rfc3339(trimmed) {
            let datetime_mod = py.import("datetime")?;
            let dt_utc = dt.with_timezone(&Utc);
            return datetime_mod.call_method1("datetime", (
                dt_utc.year(),
                dt_utc.month(),
                dt_utc.day(),
                dt_utc.hour(),
                dt_utc.minute(),
                dt_utc.second(),
                dt_utc.nanosecond() / 1000, // microseconds
            ))?.extract();
        }
        
        // Format 2: Date only (YYYY-MM-DD)
        if let Ok(date) = NaiveDate::parse_from_str(trimmed, "%Y-%m-%d") {
            let datetime_mod = py.import("datetime")?;
            return datetime_mod.call_method1("date", (
                date.year(),
                date.month(),
                date.day(),
            ))?.extract();
        }
        
        // Format 3: Canonical format (2001-12-14 21:59:43.10 -5)
        if let Some(caps) = Regex::new(r"^([0-9]{4})-([0-9]{1,2})-([0-9]{1,2}) ([0-9]{1,2}):([0-9]{2}):([0-9]{2})(\.[0-9]*)? ?([+-][0-9]{1,2})?$").unwrap().captures(trimmed) {
            let year: i32 = caps[1].parse().unwrap_or(1970);
            let month: u32 = caps[2].parse().unwrap_or(1);
            let day: u32 = caps[3].parse().unwrap_or(1);
            let hour: u32 = caps[4].parse().unwrap_or(0);
            let minute: u32 = caps[5].parse().unwrap_or(0);
            let second: u32 = caps[6].parse().unwrap_or(0);
            
            let datetime_mod = py.import("datetime")?;
            return datetime_mod.call_method1("datetime", (
                year, month, day, hour, minute, second
            ))?.extract();
        }
        
        // Fallback: return as string
        Ok(PyString::new(py, value).into())
    }
    
    /// Build binary data from base64
    fn construct_binary(&self, py: Python, value: &str) -> PyResult<PyObject> {
        // Remove whitespace and decode base64
        let cleaned = value.chars()
            .filter(|c| !c.is_whitespace())
            .collect::<String>();
        
        match general_purpose::STANDARD.decode(&cleaned) {
            Ok(bytes) => Ok(PyBytes::new(py, &bytes).into()),
            Err(_) => {
                // If not valid base64, return as string
                Ok(PyString::new(py, value).into())
            }
        }
    }
    
    /// Build merge key
    fn construct_merge(&self, _py: Python, value: &str) -> PyResult<PyObject> {
        Python::with_gil(|py| {
            // Merge keys are special, return special value
            Ok(PyString::new(py, &format!("__MERGE_KEY__:{}", value)).into())
        })
    }
    
    /// Build integer with multiple bases
    fn construct_int(&self, py: Python, value: &str) -> PyResult<PyObject> {
        let trimmed = value.trim().replace('_', "");
        
        let parsed_value = if trimmed.starts_with("0b") {
            // Binary
            i64::from_str_radix(&trimmed[2..], 2)
        } else if trimmed.starts_with("0x") {
            // Hexadecimal
            i64::from_str_radix(&trimmed[2..], 16)
        } else if trimmed.starts_with('0') && trimmed.len() > 1 && !trimmed.contains('.') {
            // Octal
            i64::from_str_radix(&trimmed[1..], 8)
        } else {
            // Decimal
            trimmed.parse::<i64>()
        };
        
        match parsed_value {
            Ok(num) => Ok(PyInt::new(py, num).into()),
            Err(_) => Ok(PyString::new(py, value).into()), // Fallback to string
        }
    }
    
    /// Build float with special cases
    fn construct_float(&self, py: Python, value: &str) -> PyResult<PyObject> {
        let trimmed = value.trim().replace('_', "").to_lowercase();
        
        let float_val = if trimmed == ".inf" || trimmed == "+.inf" {
            f64::INFINITY
        } else if trimmed == "-.inf" {
            f64::NEG_INFINITY
        } else if trimmed == ".nan" {
            f64::NAN
        } else {
            trimmed.parse::<f64>().unwrap_or(0.0)
        };
        
        Ok(PyFloat::new(py, float_val).into())
    }
    
    /// Build boolean
    fn construct_bool(&self, py: Python, value: &str) -> PyResult<PyObject> {
        let trimmed = value.trim();
        let is_true = matches!(trimmed.to_lowercase().as_str(), 
            "true" | "yes" | "on" | "1"
        );
        Ok(PyBool::new(py, is_true).to_owned().into())
    }
    
    /// Build null
    fn construct_null(&self, py: Python) -> PyResult<PyObject> {
        Ok(py.None())
    }
}

// === FUNCIONES PYTHON INTEGRATION ===

/// Main function to resolve implicit tag
#[pyfunction]
pub fn resolve_implicit_tag(value: &str) -> String {
    let mut resolver = AdvancedResolver::new();
    resolver.resolve(value, true)
}

/// Function to resolve specific tag
#[pyfunction] 
pub fn resolve_tag_value(tag: &str, value: &str) -> PyResult<PyObject> {
    let resolver = AdvancedResolver::new();
    resolver.resolve_tag(tag, value)
}

/// Function to verify if value is of certain type
#[pyfunction]
pub fn check_type(value: &str, type_name: &str) -> bool {
    let resolver = AdvancedResolver::new();
    match type_name {
        "null" => resolver.is_null(value),
        "bool" => resolver.is_bool(value),
        "int" => resolver.is_int(value),
        "float" => resolver.is_float(value),
        "timestamp" => resolver.is_timestamp(value),
        "merge" => resolver.is_merge(value),
        _ => false,
    }
} 