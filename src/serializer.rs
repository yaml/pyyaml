use pyo3::prelude::*;
use std::collections::{HashMap, HashSet};
use crate::parser::{Event, Mark, PyEvent};
use crate::composer::{Node, NodeValue};

/// Error for node serialization
#[derive(Debug)]
pub struct SerializerError {
    pub message: String,
    pub mark: Option<Mark>,
}

impl std::fmt::Display for SerializerError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "SerializerError: {}", self.message)
    }
}

impl std::error::Error for SerializerError {}

/// Serializer ultra-optimizado - convierte nodos YAML en eventos
/// Es el INVERSO del composer: Nodos → Eventos
#[pyclass]
pub struct Serializer {
    // Internal state to detect circular references - THREAD-SAFE
    node_addresses: HashSet<usize>, // Direcciones de memoria como usize (thread-safe)
    anchor_counter: usize,
    assigned_anchors: HashMap<usize, String>, // direccion_memoria -> anchor_name
    serialized_nodes: HashMap<usize, bool>, // direccion_memoria -> is_serialized
    
    // Configurations
    canonical: bool,
    version: Option<(u8, u8)>,
    tags: Option<HashMap<String, String>>,
    explicit_start: bool,
    explicit_end: bool,
    
    // Pre-allocated buffers for performance
    event_buffer: Vec<Event>,
}

impl Default for Serializer {
    fn default() -> Self {
        Self {
            node_addresses: HashSet::new(),
            anchor_counter: 0,
            assigned_anchors: HashMap::new(),
            serialized_nodes: HashMap::new(),
            canonical: false,
            version: Some((1, 2)),
            tags: None,
            explicit_start: false,
            explicit_end: false,
            event_buffer: Vec::with_capacity(64),
        }
    }
}

#[pymethods]
impl Serializer {
    #[new]
    pub fn new() -> Self {
        Self::default()
    }
    
    /// Configurar opciones del serializer
    pub fn with_canonical(&mut self, canonical: bool) {
        self.canonical = canonical;
    }
    
    pub fn with_version(&mut self, version: (u8, u8)) {
        self.version = Some(version);
    }
    
    pub fn with_explicit_start(&mut self, explicit: bool) {
        self.explicit_start = explicit;
    }
    
    pub fn with_explicit_end(&mut self, explicit: bool) {
        self.explicit_end = explicit;
    }
    
    /// Clear state for new serialization
    pub fn reset(&mut self) {
        self.node_addresses.clear();
        self.assigned_anchors.clear();
        self.serialized_nodes.clear();
        self.anchor_counter = 0;
        self.event_buffer.clear();
    }
}

impl Serializer {
    /// Serialize a node into events - main entry point
    pub fn serialize_node(&mut self, node: &Node) -> Result<Vec<Event>, SerializerError> {
        self.reset();
        
        // STEP 1: Pre-scan to detect multiple references and assign anchors
        self.prescan_node(node)?;
        
        // STEP 2: Serialize events
        self.event_buffer.clear();
        
        // Stream start
        self.emit_stream_start();
        
        // Document start  
        self.emit_document_start();
        
        // Serialize the main node
        self.serialize_node_internal(node)?;
        
        // Document end
        self.emit_document_end();
        
        // Stream end
        self.emit_stream_end();
        
        Ok(self.event_buffer.clone())
    }
    
    /// Pre-scan to detect nodes that need anchors - THREAD-SAFE CORRECTED
    fn prescan_node(&mut self, node: &Node) -> Result<(), SerializerError> {
        // Get memory address of node as usize (thread-safe)
        let node_addr = node as *const Node as usize;
        
                    // If we've already seen this node (circular reference), assign anchor
        if self.node_addresses.contains(&node_addr) {
            if !self.assigned_anchors.contains_key(&node_addr) {
                let anchor_name = self.generate_anchor_name();
                self.assigned_anchors.insert(node_addr, anchor_name);
            }
            return Ok(()); // ✅ STOP RECURSION HERE
        }
        
        // Mark as seen
        self.node_addresses.insert(node_addr);
        self.serialized_nodes.insert(node_addr, false);
        
        // Recursivamente pre-scan children SOLO si no es circular
        match &node.value {
            NodeValue::Sequence(items) => {
                for item in items.iter() {
                    self.prescan_node(item)?;
                }
            },
            NodeValue::Mapping(pairs) => {
                for (key, value) in pairs.iter() {
                    self.prescan_node(key)?;
                    self.prescan_node(value)?;
                }
            },
            NodeValue::Scalar(_) => {
                // Scalars are safe
            }
        }
        
        Ok(())
    }
    
    /// Serialize internal node recursively - THREAD-SAFE CORRECTED
    fn serialize_node_internal(&mut self, node: &Node) -> Result<(), SerializerError> {
        let node_addr = node as *const Node as usize;
        
        // Check if this node was already serialized (alias handling)
        if let Some(already_serialized) = self.serialized_nodes.get(&node_addr) {
            if *already_serialized {
                // Emit alias
                if let Some(anchor_name) = self.assigned_anchors.get(&node_addr) {
                    self.emit_alias(anchor_name.clone());
                    return Ok(());
                }
            }
        }
        
        // Mark as serialized
        self.serialized_nodes.insert(node_addr, true);
        
        // Get anchor if exists
        let anchor = self.assigned_anchors.get(&node_addr).cloned();
        
        match &node.value {
            NodeValue::Scalar(value) => {
                self.emit_scalar(value.clone(), anchor, &node.tag, node.style);
            },
            NodeValue::Sequence(items) => {
                self.emit_sequence_start(anchor, &node.tag, node.flow_style.unwrap_or(false));
                
                // Serialize items
                for item in items.iter() {
                    self.serialize_node_internal(item)?;
                }
                
                self.emit_sequence_end();
            },
            NodeValue::Mapping(pairs) => {
                self.emit_mapping_start(anchor, &node.tag, node.flow_style.unwrap_or(false));
                
                // Serialize pairs
                for (key, value) in pairs.iter() {
                    self.serialize_node_internal(key)?;
                    self.serialize_node_internal(value)?;
                }
                
                self.emit_mapping_end();
            }
        }
        
        Ok(())
    }
    
    /// Generate unique anchor name
    fn generate_anchor_name(&mut self) -> String {
        self.anchor_counter += 1;
        format!("id{:03}", self.anchor_counter)
    }
    
    // === EMISORES DE EVENTOS ===
    
    fn emit_stream_start(&mut self) {
        let mark = Mark::new(0, 0, 0);
        self.event_buffer.push(Event::StreamStart {
            start_mark: mark.clone(),
            end_mark: mark,
            encoding: Some("utf-8".to_string()),
        });
    }
    
    fn emit_stream_end(&mut self) {
        let mark = Mark::new(0, 0, 0);
        self.event_buffer.push(Event::StreamEnd {
            start_mark: mark.clone(),
            end_mark: mark,
        });
    }
    
    fn emit_document_start(&mut self) {
        let mark = Mark::new(0, 0, 0);
        self.event_buffer.push(Event::DocumentStart {
            start_mark: mark.clone(),
            end_mark: mark,
            explicit: self.explicit_start,
            version: self.version,
            tags: self.tags.clone(),
        });
    }
    
    fn emit_document_end(&mut self) {
        let mark = Mark::new(0, 0, 0);
        self.event_buffer.push(Event::DocumentEnd {
            start_mark: mark.clone(),
            end_mark: mark,
            explicit: self.explicit_end,
        });
    }
    
    fn emit_scalar(&mut self, value: String, anchor: Option<String>, tag: &str, style: Option<char>) {
        let mark = Mark::new(0, 0, 0);
        
        // Determine implicit tag
        let tag_implicit = if tag == "tag:yaml.org,2002:str" && !self.canonical {
            (true, false)
        } else {
            (false, true)
        };
        
        self.event_buffer.push(Event::Scalar {
            anchor,
            tag: if self.canonical || tag != "tag:yaml.org,2002:str" { 
                Some(tag.to_string()) 
            } else { 
                None 
            },
            implicit: tag_implicit,
            value,
            start_mark: mark.clone(),
            end_mark: mark,
            style,
        });
    }
    
    fn emit_sequence_start(&mut self, anchor: Option<String>, tag: &str, flow_style: bool) {
        let mark = Mark::new(0, 0, 0);
        self.event_buffer.push(Event::SequenceStart {
            anchor,
            tag: if self.canonical || tag != "tag:yaml.org,2002:seq" { 
                Some(tag.to_string()) 
            } else { 
                None 
            },
            implicit: !self.canonical && tag == "tag:yaml.org,2002:seq",
            start_mark: mark.clone(),
            end_mark: mark,
            flow_style,
        });
    }
    
    fn emit_sequence_end(&mut self) {
        let mark = Mark::new(0, 0, 0);
        self.event_buffer.push(Event::SequenceEnd {
            start_mark: mark.clone(),
            end_mark: mark,
        });
    }
    
    fn emit_mapping_start(&mut self, anchor: Option<String>, tag: &str, flow_style: bool) {
        let mark = Mark::new(0, 0, 0);
        self.event_buffer.push(Event::MappingStart {
            anchor,
            tag: if self.canonical || tag != "tag:yaml.org,2002:map" { 
                Some(tag.to_string()) 
            } else { 
                None 
            },
            implicit: !self.canonical && tag == "tag:yaml.org,2002:map",
            start_mark: mark.clone(),
            end_mark: mark,
            flow_style,
        });
    }
    
    fn emit_mapping_end(&mut self) {
        let mark = Mark::new(0, 0, 0);
        self.event_buffer.push(Event::MappingEnd {
            start_mark: mark.clone(),
            end_mark: mark,
        });
    }
    
    fn emit_alias(&mut self, anchor: String) {
        let mark = Mark::new(0, 0, 0);
        self.event_buffer.push(Event::Alias {
            anchor,
            start_mark: mark.clone(),
            end_mark: mark,
        });
    }
}

// === FUNCIONES PYTHON INTEGRATION ===

/// Main function to serialize node to events
#[pyfunction]
pub fn serialize_rust(node: &Node) -> PyResult<Vec<PyEvent>> {
    let mut serializer = Serializer::new();
    
    match serializer.serialize_node(node) {
        Ok(events) => {
            let py_events = events.into_iter()
                .map(|event| PyEvent::from_event(event))
                .collect();
            Ok(py_events)
        },
        Err(e) => Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(e.message)),
    }
}

/// Function with options
#[pyfunction]
pub fn serialize_with_options(
    node: &Node,
    canonical: Option<bool>,
    version: Option<(u8, u8)>,
    explicit_start: Option<bool>,
    explicit_end: Option<bool>,
) -> PyResult<Vec<PyEvent>> {
    let mut serializer = Serializer::new();
    
    if let Some(canonical) = canonical {
        serializer.with_canonical(canonical);
    }
    if let Some(version) = version {
        serializer.with_version(version);
    }
    if let Some(explicit_start) = explicit_start {
        serializer.with_explicit_start(explicit_start);
    }
    if let Some(explicit_end) = explicit_end {
        serializer.with_explicit_end(explicit_end);
    }
    
    match serializer.serialize_node(node) {
        Ok(events) => {
            let py_events = events.into_iter()
                .map(|event| PyEvent::from_event(event))
                .collect();
            Ok(py_events)
        },
        Err(e) => Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(e.message)),
    }
}

        // Extension for PyEvent
impl PyEvent {
    pub fn from_event(event: Event) -> Self {
        Self { event }
    }
} 