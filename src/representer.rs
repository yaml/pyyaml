use pyo3::prelude::*;
use pyo3::types::*;
use std::collections::{HashMap, HashSet};
use crate::composer::{Node, NodeValue};
use crate::parser::Mark;

/// Error for object representation
#[derive(Debug)]
pub struct RepresenterError {
    pub message: String,
}

impl std::fmt::Display for RepresenterError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "RepresenterError: {}", self.message)
    }
}

impl std::error::Error for RepresenterError {}

impl From<RepresenterError> for PyErr {
    fn from(err: RepresenterError) -> PyErr {
        PyErr::new::<pyo3::exceptions::PyValueError, _>(err.message)
    }
}

/// Represents Python objects as YAML nodes (safe)
#[derive(Debug, Default)]
pub struct SafeRepresenter {
    /// Cache of already represented objects to avoid duplication
    represented_objects: HashSet<usize>, // Direcciones de memoria como usize (thread-safe)
    
    /// Cache de nodos para objetos referenciados múltiples veces
    node_cache: HashMap<usize, Node>, // direccion_memoria -> Node
    
    /// Configuraciones
    default_flow_style: bool,
    sort_keys: bool,
    
    /// Contador de anchors para referencias múltiples
    anchor_counter: usize,
    /// Objetos que necesitan anchors (referenciados múltiples veces)
    objects_needing_anchors: HashMap<usize, String>, // direccion -> anchor_name
}

impl SafeRepresenter {
    pub fn new() -> Self {
        Self::default()
    }

    /// Main entry point - represents a Python object as YAML node
    pub fn represent_data(&mut self, py: Python, data: &Bound<'_, PyAny>) -> PyResult<Node> {
        // Limpiar estado para nueva representación
        self.represented_objects.clear();
        self.node_cache.clear();
        self.objects_needing_anchors.clear();
        self.anchor_counter = 0;

        // PASO 1: Pre-scan para detectar objetos que necesitan anchors
        self.prescan_for_anchors(py, data)?;
        
        // PASO 2: Limpiar estado de representación y representar el objeto
        self.represented_objects.clear();
        self.represent_object(py, data)
    }

    /// Pre-scan para detectar objetos referenciados múltiples veces
    fn prescan_for_anchors(&mut self, py: Python, data: &Bound<'_, PyAny>) -> PyResult<()> {
        // Obtener dirección de memoria del objeto
        let obj_addr = data.as_ptr() as usize;
        
        // Si ya hemos visto este objeto, marcar para anchor
        if self.represented_objects.contains(&obj_addr) {
            if !self.objects_needing_anchors.contains_key(&obj_addr) {
                let anchor_name = self.generate_anchor_name();
                self.objects_needing_anchors.insert(obj_addr, anchor_name);
            }
            return Ok(()); // ✅ DETENER RECURSIÓN AQUÍ
        }
        
        // Marcar como visto
        self.represented_objects.insert(obj_addr);
        
        // Recursivamente pre-scan para contenedores SOLO si no es circular
        if let Ok(list_val) = data.downcast::<PyList>() {
            for item in list_val.iter() {
                self.prescan_for_anchors(py, &item)?;
            }
        } else if let Ok(tuple_val) = data.downcast::<PyTuple>() {
            for item in tuple_val.iter() {
                self.prescan_for_anchors(py, &item)?;
            }
        } else if let Ok(dict_val) = data.downcast::<PyDict>() {
            for (key, value) in dict_val.iter() {
                self.prescan_for_anchors(py, &key)?;
                self.prescan_for_anchors(py, &value)?;
            }
        } else if let Ok(set_val) = data.downcast::<PySet>() {
            for item in set_val.iter() {
                self.prescan_for_anchors(py, &item)?;
            }
        } else if let Ok(frozenset_val) = data.downcast::<PyFrozenSet>() {
            for item in frozenset_val.iter() {
                self.prescan_for_anchors(py, &item)?;
            }
        }
        
        Ok(())
    }

    /// Generate unique anchor name
    fn generate_anchor_name(&mut self) -> String {
        self.anchor_counter += 1;
        format!("id{:03}", self.anchor_counter)
    }

    /// Represents a specific Python object - WITH CYCLE DETECTION
    fn represent_object(&mut self, py: Python, data: &Bound<'_, PyAny>) -> PyResult<Node> {
        let obj_addr = data.as_ptr() as usize;
        
        // Si este objeto ya fue representado, devolver alias o nodo cacheado
        if self.represented_objects.contains(&obj_addr) {
            if let Some(cached_node) = self.node_cache.get(&obj_addr) {
                return Ok(cached_node.clone());
            }
            
            // Si necesita anchor, crear nodo alias
            if let Some(anchor_name) = self.objects_needing_anchors.get(&obj_addr) {
                let mark = Mark::new(0, 0, 0);
                return Ok(Node::new_alias(anchor_name.clone(), mark.clone(), mark));
            }
        }
        
        // Marcar como siendo representado
        self.represented_objects.insert(obj_addr);
        
        let mark = Mark::new(0, 0, 0);

        // Detectar tipo y representar apropiadamente
        let mut node = if data.is_none() {
            self.represent_none()
        } else if let Ok(bool_val) = data.downcast::<PyBool>() {
            self.represent_bool(bool_val)?
        } else if let Ok(int_val) = data.downcast::<PyInt>() {
            self.represent_int(int_val)?
        } else if let Ok(float_val) = data.downcast::<PyFloat>() {
            self.represent_float(float_val)?
        } else if let Ok(str_val) = data.downcast::<PyString>() {
            self.represent_str(str_val)?
        } else if let Ok(list_val) = data.downcast::<PyList>() {
            self.represent_list(py, list_val)?
        } else if let Ok(tuple_val) = data.downcast::<PyTuple>() {
            self.represent_tuple(py, tuple_val)?
        } else if let Ok(dict_val) = data.downcast::<PyDict>() {
            self.represent_dict(py, dict_val)?
        } else if let Ok(set_val) = data.downcast::<PySet>() {
            self.represent_set(py, set_val)?
        } else if let Ok(frozenset_val) = data.downcast::<PyFrozenSet>() {
            self.represent_frozenset(py, frozenset_val)?
        } else {
            // Fallback: convertir a string
            let str_repr = data.str()?.extract::<String>()?;
            Node::new_scalar(
                "tag:yaml.org,2002:str".to_string(),
                str_repr,
                mark.clone(),
                mark,
                None
            )
        };
        
        // Si este objeto necesita anchor, asignarlo
        if let Some(anchor_name) = self.objects_needing_anchors.get(&obj_addr) {
            node.anchor = Some(anchor_name.clone());
        }
        
        // Cachear el nodo
        self.node_cache.insert(obj_addr, node.clone());
        
        Ok(node)
    }

    /// Represents None/null
    fn represent_none(&self) -> Node {
        let mark = Mark::new(0, 0, 0);
        Node::new_scalar(
            "tag:yaml.org,2002:null".to_string(),
            "null".to_string(),
            mark.clone(),
            mark,
            None
        )
    }

    /// Represents boolean
    fn represent_bool(&self, data: &Bound<'_, PyBool>) -> PyResult<Node> {
        let mark = Mark::new(0, 0, 0);
        let value = if data.is_true() { "true" } else { "false" };
        
        Ok(Node::new_scalar(
            "tag:yaml.org,2002:bool".to_string(),
            value.to_string(),
            mark.clone(),
            mark,
            None
        ))
    }

    /// Represents integer
    fn represent_int(&self, data: &Bound<'_, PyInt>) -> PyResult<Node> {
        let mark = Mark::new(0, 0, 0);
        let value = data.extract::<i64>()?;
        
        Ok(Node::new_scalar(
            "tag:yaml.org,2002:int".to_string(),
            value.to_string(),
            mark.clone(),
            mark,
            None
        ))
    }

    /// Represents float
    fn represent_float(&self, data: &Bound<'_, PyFloat>) -> PyResult<Node> {
        let mark = Mark::new(0, 0, 0);
        let value = data.extract::<f64>()?;
        
        let yaml_value = if value.is_nan() {
            ".nan".to_string()
        } else if value.is_infinite() {
            if value.is_sign_positive() {
                ".inf".to_string()
            } else {
                "-.inf".to_string()
            }
        } else {
            // Usar representación estándar, añadiendo .0 si es necesario
            let mut repr = format!("{}", value);
            if !repr.contains('.') && !repr.contains('e') && !repr.contains('E') {
                repr.push_str(".0");
            }
            repr
        };

        Ok(Node::new_scalar(
            "tag:yaml.org,2002:float".to_string(),
            yaml_value,
            mark.clone(),
            mark,
            None
        ))
    }

    /// Represents string
    fn represent_str(&self, data: &Bound<'_, PyString>) -> PyResult<Node> {
        let mark = Mark::new(0, 0, 0);
        let value = data.extract::<String>()?;
        
        Ok(Node::new_scalar(
            "tag:yaml.org,2002:str".to_string(),
            value,
            mark.clone(),
            mark,
            None
        ))
    }

    /// Represents list - FIXED to avoid infinite recursion
    fn represent_list(&mut self, py: Python, data: &Bound<'_, PyList>) -> PyResult<Node> {
        let mark = Mark::new(0, 0, 0);
        let mut items = Vec::new();

        for item in data.iter() {
            let node = self.represent_object(py, &item)?;
            items.push(node);
        }

        Ok(Node::new_sequence(
            "tag:yaml.org,2002:seq".to_string(),
            items,
            mark.clone(),
            mark,
            self.default_flow_style
        ))
    }

    /// Represents tuple (as sequence) - FIXED
    fn represent_tuple(&mut self, py: Python, data: &Bound<'_, PyTuple>) -> PyResult<Node> {
        let mark = Mark::new(0, 0, 0);
        let mut items = Vec::new();

        for item in data.iter() {
            let node = self.represent_object(py, &item)?;
            items.push(node);
        }

        Ok(Node::new_sequence(
            "tag:yaml.org,2002:seq".to_string(),
            items,
            mark.clone(),
            mark,
            self.default_flow_style
        ))
    }

    /// Represents dictionary - FIXED to avoid infinite recursion
    fn represent_dict(&mut self, py: Python, data: &Bound<'_, PyDict>) -> PyResult<Node> {
        let mark = Mark::new(0, 0, 0);
        let mut pairs = Vec::new();

        // Convertir items a vector para poder ordenar si es necesario
        let mut items: Vec<(Bound<PyAny>, Bound<PyAny>)> = Vec::new();
        for (key, value) in data.iter() {
            items.push((key, value));
        }

        // Ordenar claves si está habilitado (y es posible)
        if self.sort_keys {
            items.sort_by(|a, b| {
                // Intentar ordenar por string representation de las claves
                let key_a = a.0.str().map(|s| s.extract::<String>()).unwrap_or_else(|_| Ok("".to_string())).unwrap_or_default();
                let key_b = b.0.str().map(|s| s.extract::<String>()).unwrap_or_else(|_| Ok("".to_string())).unwrap_or_default();
                key_a.cmp(&key_b)
            });
        }

        for (key, value) in items {
            let key_node = self.represent_object(py, &key)?;
            let value_node = self.represent_object(py, &value)?;
            pairs.push((key_node, value_node));
        }

        Ok(Node::new_mapping(
            "tag:yaml.org,2002:map".to_string(),
            pairs,
            mark.clone(),
            mark,
            self.default_flow_style
        ))
    }

    /// Represents set - FIXED
    fn represent_set(&mut self, py: Python, data: &Bound<'_, PySet>) -> PyResult<Node> {
        let mark = Mark::new(0, 0, 0);
        let mut pairs = Vec::new();

        // Convertir set a mapping con valores None
        for item in data.iter() {
            let key_node = self.represent_object(py, &item)?;
            let value_node = self.represent_none();
            pairs.push((key_node, value_node));
        }

        Ok(Node::new_mapping(
            "tag:yaml.org,2002:set".to_string(),
            pairs,
            mark.clone(),
            mark,
            self.default_flow_style
        ))
    }

    /// Represents frozenset - FIXED
    fn represent_frozenset(&mut self, py: Python, data: &Bound<'_, PyFrozenSet>) -> PyResult<Node> {
        let mark = Mark::new(0, 0, 0);
        let mut pairs = Vec::new();

        // Convertir frozenset a mapping con valores None
        for item in data.iter() {
            let key_node = self.represent_object(py, &item)?;
            let value_node = self.represent_none();
            pairs.push((key_node, value_node));
        }

        Ok(Node::new_mapping(
            "tag:yaml.org,2002:set".to_string(),
            pairs,
            mark.clone(),
            mark,
            self.default_flow_style
        ))
    }

    /// Configurar estilo de flujo por defecto
    pub fn set_default_flow_style(&mut self, flow_style: bool) {
        self.default_flow_style = flow_style;
    }

    /// Configurar ordenación de claves
    pub fn set_sort_keys(&mut self, sort_keys: bool) {
        self.sort_keys = sort_keys;
    }
}

/// Main function to represent a Python object as YAML node
#[pyfunction]
pub fn represent_rust(py: Python, data: &Bound<'_, PyAny>) -> PyResult<Node> {
    let mut representer = SafeRepresenter::new();
    representer.represent_data(py, data)
}

/// Function to represent with options
#[pyfunction]
pub fn represent_with_options(
    py: Python,
    data: &Bound<'_, PyAny>,
    default_flow_style: Option<bool>,
    sort_keys: Option<bool>,
) -> PyResult<Node> {
    let mut representer = SafeRepresenter::new();
    
    if let Some(flow_style) = default_flow_style {
        representer.set_default_flow_style(flow_style);
    }
    
    if let Some(sort) = sort_keys {
        representer.set_sort_keys(sort);
    }
    
    representer.represent_data(py, data)
} 