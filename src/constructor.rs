use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyString, PyFloat, PyInt};
use crate::composer::{Node, NodeValue};



/// Simple static constructor - stateless
pub struct SimpleConstructor;

impl SimpleConstructor {
    /// Build Python object from node (main function)
    pub fn construct_node(py: Python, node: &Node) -> PyResult<PyObject> {
        match &node.value {
            NodeValue::Scalar(value) => Self::construct_scalar(py, node, value),
            NodeValue::Sequence(nodes) => Self::construct_sequence(py, nodes),
            NodeValue::Mapping(pairs) => Self::construct_mapping(py, pairs),
        }
    }
    
    /// Build scalar with automatic type detection
    fn construct_scalar(py: Python, node: &Node, value: &str) -> PyResult<PyObject> {
        // Use tag if available, otherwise detect type automatically
        let tag = node.tag.as_str();
        
        match tag {
            "tag:yaml.org,2002:null" => Ok(py.None()),
            "tag:yaml.org,2002:bool" => Self::construct_bool(py, value),
            "tag:yaml.org,2002:int" => Self::construct_int(py, value),
            "tag:yaml.org,2002:float" => Self::construct_float(py, value),
            "tag:yaml.org,2002:str" => Ok(PyString::new(py, value).unbind().into()),
            _ => Self::auto_detect_type(py, value),
        }
    }
    
    /// Auto-detect type based on content
    fn auto_detect_type(py: Python, value: &str) -> PyResult<PyObject> {
        // Null
        if value == "null" || value == "~" || value.is_empty() {
            return Ok(py.None());
        }
        
        // Boolean
        if ["true", "false", "yes", "no", "on", "off"].contains(&value.to_lowercase().as_str()) {
            return Self::construct_bool(py, value);
        }
        
        // Integer
        if let Ok(_) = value.parse::<i64>() {
            return Self::construct_int(py, value);
        }
        
        // Float
        if let Ok(_) = value.parse::<f64>() {
            return Self::construct_float(py, value);
        }
        
        // String by default
        Ok(PyString::new(py, value).unbind().into())
    }
    
    /// Build boolean
    fn construct_bool(py: Python, value: &str) -> PyResult<PyObject> {
        let bool_val = match value.to_lowercase().as_str() {
            "true" | "yes" | "on" => 1,
            "false" | "no" | "off" => 0,
            _ => return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                format!("Invalid boolean value: {}", value)
            )),
        };
        Ok(PyInt::new(py, bool_val).unbind().into())
    }
    
    /// Build integer
    fn construct_int(py: Python, value: &str) -> PyResult<PyObject> {
        let mut val = value.replace('_', "");
        let sign = if val.starts_with('-') {
            val = val[1..].to_string();
            -1
        } else if val.starts_with('+') {
            val = val[1..].to_string();
            1
        } else {
            1
        };
        
        let int_val = if val == "0" {
            0
        } else if val.starts_with("0b") {
            i64::from_str_radix(&val[2..], 2).map_err(|e| 
                PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("Invalid binary: {}", e)))?
        } else if val.starts_with("0x") {
            i64::from_str_radix(&val[2..], 16).map_err(|e| 
                PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("Invalid hex: {}", e)))?
        } else if val.starts_with('0') && val.len() > 1 {
            i64::from_str_radix(&val, 8).map_err(|e| 
                PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("Invalid octal: {}", e)))?
        } else {
            val.parse::<i64>().map_err(|e| 
                PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("Invalid integer: {}", e)))?
        };
        
        Ok(PyInt::new(py, sign * int_val).unbind().into())
    }
    
    /// Build float
    fn construct_float(py: Python, value: &str) -> PyResult<PyObject> {
        let mut val = value.replace('_', "").to_lowercase();
        let sign = if val.starts_with('-') {
            val = val[1..].to_string();
            -1.0
        } else if val.starts_with('+') {
            val = val[1..].to_string();
            1.0
        } else {
            1.0
        };
        
        let float_val = if val == ".inf" {
            f64::INFINITY
        } else if val == ".nan" {
            f64::NAN
        } else {
            val.parse::<f64>().map_err(|e| 
                PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("Invalid float: {}", e)))?
        };
        
        Ok(PyFloat::new(py, sign * float_val).unbind().into())
    }
    
    /// Build sequence
    fn construct_sequence(py: Python, nodes: &[Node]) -> PyResult<PyObject> {
        let list = PyList::empty(py);
        for node in nodes {
            let obj = Self::construct_node(py, node)?;
            list.append(obj)?;
        }
        Ok(list.unbind().into())
    }
    
    /// Build mapping
    fn construct_mapping(py: Python, pairs: &[(Node, Node)]) -> PyResult<PyObject> {
        let dict = PyDict::new(py);
        for (key_node, value_node) in pairs {
            let key = Self::construct_node(py, key_node)?;
            let value = Self::construct_node(py, value_node)?;
            dict.set_item(key, value)?;
        }
        Ok(dict.unbind().into())
    }
}

/// Main function to build Python object from node
#[pyfunction]
pub fn construct_rust(py: Python, node: &Node) -> PyResult<PyObject> {
    SimpleConstructor::construct_node(py, node)
}

 