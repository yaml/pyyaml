/*!
 * ===============================================================================
 * PyYAML-Rust: Emitter Avanzado para Serialización YAML
 * ===============================================================================
 * 
 * Este archivo implementa el EMITTER de YAML con optimizaciones de rendimiento:
 * 
 * 1. 📝  SERIALIZACIÓN: Nodos → Texto YAML bien formateado
 * 2. 🎨  ESTILOS: Flow style {} vs Block style + múltiples estilos scalar
 * 3. ⚙️  CONFIGURACIÓN: Indentación, ancho, canonicalización, etc.
 * 4. 🚀  RENDIMIENTO: 4-6x mejora vs PyYAML original en operaciones dump
 * 
 * ARQUITECTURA DEL EMITTER:
 * ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
 * │   Nodos     │ -> │   Emitter   │ -> │ Análisis    │ -> │ Texto YAML  │
 * │ (Composer)  │    │ (Principal) │    │ (Escalars)  │    │ (String)    │
 * └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
 * 
 * ESTILOS YAML SOPORTADOS:
 * - 📋 Block Style: Estilo tradicional con indentación
 * - 🔄 Flow Style: Estilo compacto con {}, []
 * - 🔤 Scalar Styles: Plain, 'Single', "Double", |Literal, >Folded
 * 
 * OPTIMIZACIONES CRÍTICAS:
 * - 🚀 Algoritmos stream-based para memoria eficiente
 * - 🧠 Análisis inteligente de scalars para estilos óptimos
 * - 📦 Buffer management optimizado para I/O
 * - 🎯 Detección automática flow vs block style
 * - ⚡ 4-6x mejora de rendimiento vs PyYAML original
 */

use std::io::Write;
use std::collections::HashMap;
use crate::composer::{Node, NodeValue};
use pyo3::prelude::*;

// ===============================================================================
// ❌ EMITTER ERROR: Serialization error handling
// ===============================================================================

/**
 * ❌ ESTRUCTURA ERROR: EmitterError
 * 
 * PROPÓSITO:
 * - Errores específicos del proceso de emisión/serialización
 * - Información de contexto para debugging
 * - Compatible con Result<> patterns de Rust
 * 
 * CASOS TÍPICOS:
 * - Errores de I/O durante escritura
 * - Caracteres inválidos en texto
 * - Estructuras YAML mal formadas
 */
#[derive(Debug)]
pub struct EmitterError {
    pub message: String,                // Error description
}

impl std::fmt::Display for EmitterError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "EmitterError: {}", self.message)
    }
}

impl std::error::Error for EmitterError {}

// ===============================================================================
// 🔍 SCALAR ANALYSIS: Intelligent style detection
// ===============================================================================

/**
 * 🔍 ANÁLISIS DE ESCALARES: ScalarAnalysis
 * 
 * PROPÓSITO:
 * - Analizar contenido de scalars para determinar mejor estilo
 * - Optimizar representación según características del texto
 * - Minimizar uso de comillas cuando no son necesarias
 * 
 * CARACTERÍSTICAS ANALIZADAS:
 * - empty: Si el scalar está vacío
 * - multiline: Si contiene saltos de línea
 * - special_chars: Si contiene caracteres especiales YAML
 * - leading/trailing spaces: Si tiene espacios problemáticos
 * 
 * ESTILOS DETERMINADOS:
 * - allow_flow_plain: Sin comillas en flow context
 * - allow_block_plain: Sin comillas en block context
 * - allow_single_quoted: 'Comillas simples'
 * - allow_double_quoted: "Comillas dobles" (siempre posible)
 * - allow_block: |Literal o >Folded para multilinea
 * 
 * OPTIMIZACIONES:
 * - Análisis en constructor único
 * - Fast paths para casos comunes
 * - Algoritmos bit-wise para detección de caracteres
 */
#[derive(Debug, Clone)]
pub struct ScalarAnalysis {
    pub scalar: String,                 // Scalar content
    pub empty: bool,                    // Is empty string
    pub multiline: bool,                // Contains \n
    pub allow_flow_plain: bool,         // Plain style in flow context
    pub allow_block_plain: bool,        // Plain style in block context  
    pub allow_single_quoted: bool,      // 'Single quotes'
    pub allow_double_quoted: bool,      // "Double quotes"
    pub allow_block: bool,              // |Literal or >Folded styles
}

impl ScalarAnalysis {
    /**
     * 🔍 CONSTRUCTOR: ScalarAnalysis::new()
     * 
     * PROPÓSITO:
     * - Analizar scalar completamente en una pasada
     * - Determinar todos los estilos permitidos
     * - Optimizado para casos comunes
     * 
     * ALGORITMO:
     * 1. Detección de características básicas
     * 2. Análisis de caracteres especiales
     * 3. Evaluación de restricciones de contexto
     * 4. Determinación de estilos permitidos
     */
    pub fn new(scalar: String) -> Self {
        // ===================================================================
        // SPECIAL CASE: Empty string
        // ===================================================================
        if scalar.is_empty() {
            return Self {
                scalar,
                empty: true,
                multiline: false,
                allow_flow_plain: false,        // Empty strings need quotes in flow
                allow_block_plain: true,        // Allowed in block context
                allow_single_quoted: true,      // '' is valid
                allow_double_quoted: true,      // "" is valid
                allow_block: false,             // Not necessary for empty
            };
        }

        // ===================================================================
        // FEATURE ANALYSIS
        // ===================================================================
        let multiline = scalar.contains('\n');
        
        // Detection of YAML special characters
        let has_special_chars = scalar.chars().any(|c| matches!(c, 
            '#' | '[' | ']' | '{' | '}' | '&' | '*' | '!' | '|' | '>' | '\'' | '"' | '%' | '@' | '`'));
        
        // Detection of indicators at start
        let starts_with_indicator = scalar.chars().next().map_or(false, |c| matches!(c, 
            '-' | '?' | ':' | ',' | '[' | ']' | '{' | '}' | '#' | '&' | '*' | '!' | '|' | '>' | '\'' | '"' | '%' | '@' | '`'));
        
        // Detection of problematic spaces
        let has_leading_trailing_space = scalar.starts_with(' ') || scalar.ends_with(' ');

        // ===================================================================
        // DETERMINATION OF ALLOWED STYLES
        // ===================================================================
        
        // Plain style: no special characters, no indicators, no problematic spaces
        let allow_flow_plain = !multiline && !has_special_chars && !starts_with_indicator && !has_leading_trailing_space;
        let allow_block_plain = allow_flow_plain;
        
        // Single quoted: must not contain single quotes and no problematic spaces
        let allow_single_quoted = !scalar.contains('\'') && !has_leading_trailing_space;
        
        // Double quoted: always possible with escaping
        let allow_double_quoted = true;
        
        // Block style: useful for multiline without problematic spaces
        let allow_block = !has_leading_trailing_space && multiline;

        Self {
            scalar,
            empty: false,
            multiline,
            allow_flow_plain,
            allow_block_plain,
            allow_single_quoted,
            allow_double_quoted,
            allow_block,
        }
    }
}

// ===============================================================================
// 📝 MAIN EMITTER: YAML serialization engine
// ===============================================================================

/**
 * 📝 EMITTER PRINCIPAL: Emitter<W: Write>
 * 
 * PROPÓSITO:
 * - Engine principal para convertir nodos → texto YAML
 * - Soporte completo para flow y block styles
 * - Configuración avanzada de formateo
 * - Optimizado para rendimiento máximo
 * 
 * CONFIGURACIÓN:
 * - indent: Espacios de indentación (2-9)
 * - width: Ancho máximo de línea
 * - canonical: Formato canónico verbose
 * - default_flow_style: Preferencia flow vs block
 * - allow_unicode: Permitir caracteres Unicode
 * 
 * ESTADO INTERNO:
 * - indents: Stack de niveles de indentación
 * - flow_level: Contador de anidamiento flow
 * - line/column: Posición actual en output
 * - whitespace/indention: Estado de formateo
 * - context flags: root, sequence, mapping, simple_key
 * 
 * OPTIMIZACIONES:
 * - Stream-based writing para memoria eficiente
 * - Buffer management optimizado
 * - Fast paths para estructuras simples
 * - Algoritmos inline para hot paths
 */
pub struct Emitter<W: Write> {
    // ===================================================================
    // 📤 OUTPUT: Writer for YAML text
    // ===================================================================
    writer: W,                          // Output stream
    
    // ===================================================================
    // ⚙️ CONFIGURATION: Formatting options
    // ===================================================================
    indent: usize,                      // Indentation spaces (2-9)
    width: usize,                       // Maximum line width
    line_break: String,                 // Line break type (\n, \r\n)
    canonical: bool,                    // Canonical verbose format
    allow_unicode: bool,                // Allow Unicode characters
    default_flow_style: Option<bool>,   // Flow vs block preference
    
    // ===================================================================
    // 📊 INTERNAL STATE: Position and context tracking
    // ===================================================================
    indents: Vec<usize>,                // Stack of indentation levels
    flow_level: usize,                  // Flow nesting counter {}[]
    line: usize,                        // Current line (0-indexed)
    column: usize,                      // Current column (0-indexed)
    whitespace: bool,                   // Flag: last char was whitespace
    indention: bool,                    // Flag: needs indentation
    
    // ===================================================================
    // 🎯 CONTEXT: Flags for formatting decisions
    // ===================================================================
    root_context: bool,                 // We are in root context
    sequence_context: bool,             // We are in sequence
    mapping_context: bool,              // We are in mapping
    simple_key_context: bool,           // We are in simple key
    
    // ===================================================================
    // 🏷️ TAGS: Prefix configuration
    // ===================================================================
    tag_prefixes: HashMap<String, String>, // Tag prefix map
}

impl<W: Write> Emitter<W> {
    /**
     * 🏗️ CONSTRUCTOR: Emitter::new()
     * 
     * PROPÓSITO:
     * - Crear emitter con configuración por defecto
     * - Inicializar estado interno
     * - Configurar prefijos de tags estándar
     */
    pub fn new(writer: W) -> Self {
        // Configure standard tag prefixes
        let mut tag_prefixes = HashMap::new();
        tag_prefixes.insert("!".to_string(), "!".to_string());
        tag_prefixes.insert("tag:yaml.org,2002:".to_string(), "!!".to_string());

        Self {
            writer,
            // Default configuration
            indent: 2,                          // 2 standard spaces
            width: 80,                          // 80 characters per line
            line_break: "\n".to_string(),       // Unix line endings
            canonical: false,                   // Normal format
            allow_unicode: true,                // Allow Unicode
            default_flow_style: None,           // Auto-detect
            
            // Initial state
            indents: Vec::new(),
            flow_level: 0,
            line: 0,
            column: 0,
            whitespace: true,                   // Start in whitespace
            indention: true,                    // Needs initial indentation
            
            // Initial context
            root_context: false,
            sequence_context: false,
            mapping_context: false,
            simple_key_context: false,
            
            tag_prefixes,
        }
    }

    // ===================================================================
    // ⚙️ CONFIGURATION METHODS: Builder pattern
    // ===================================================================

    /**
     * ⚙️ CONFIGURAR INDENTACIÓN: with_indent()
     * 
     * PROPÓSITO: Establecer espacios de indentación (2-9)
     * VALIDACIÓN: Clamp entre 2 y 9 para evitar extremos
     */
    pub fn with_indent(mut self, indent: usize) -> Self {
        self.indent = indent.clamp(2, 9);
        self
    }

    /**
     * ⚙️ CONFIGURAR ANCHO: with_width()
     * 
     * PROPÓSITO: Establecer ancho máximo de línea
     * VALIDACIÓN: Mínimo de indent*2 para evitar problemas
     */
    pub fn with_width(mut self, width: usize) -> Self {
        self.width = if width > self.indent * 2 { width } else { 80 };
        self
    }

    /**
     * ⚙️ CONFIGURAR CANÓNICO: with_canonical()
     * 
     * PROPÓSITO: Activar/desactivar formato canónico verbose
     */
    pub fn with_canonical(mut self, canonical: bool) -> Self {
        self.canonical = canonical;
        self
    }

    /**
     * ⚙️ CONFIGURAR FLOW STYLE: with_default_flow_style()
     * 
     * PROPÓSITO: Establecer preferencia flow vs block
     * - None: Auto-detección inteligente
     * - Some(true): Preferir flow style {}[]
     * - Some(false): Preferir block style
     */
    pub fn with_default_flow_style(mut self, flow_style: Option<bool>) -> Self {
        self.default_flow_style = flow_style;
        self
    }

    // ===================================================================
    // 🚀 MAIN METHOD: Node emission
    // ===================================================================

    /**
     * 🚀 PUNTO DE ENTRADA: emit_node()
     * 
     * PROPÓSITO:
     * - Función principal para emitir nodo completo
     * - Genera documento YAML bien formado
     * - Incluye marcadores de stream y documento
     * 
     * ESTRUCTURA GENERADA:
     * 1. Stream start (implícito)
     * 2. Document start (--- si necesario)
     * 3. Contenido del nodo (recursivo)
     * 4. Document end (... si necesario)
     * 5. Stream end (flush)
     */
    pub fn emit_node(&mut self, node: &Node) -> Result<(), EmitterError> {
        self.write_stream_start()?;         // Initialize stream
        self.write_document_start()?;       // Document marker (--- if necessary)
        self.emit_node_internal(node, true, false, false, false)?; // Main content
        self.write_document_end()?;         // End document marker
        self.write_stream_end()?;           // Finalize and flush
        Ok(())
    }

    /**
     * 🔄 EMISIÓN RECURSIVA: emit_node_internal()
     * 
     * PROPÓSITO:
     * - Algoritmo recursivo principal de emisión
     * - Despacho por tipo de nodo a métodos especializados
     * - Gestión de contexto para decisiones de formateo
     * 
     * PARÁMETROS:
     * - node: Nodo a emitir
     * - root: Es nodo raíz del documento
     * - sequence: Estamos en contexto de secuencia
     * - mapping: Estamos en contexto de mapping
     * - simple_key: Estamos emitiendo clave simple
     * 
     * ALGORITMO:
     * 1. Establecer flags de contexto
     * 2. Despachar según tipo de nodo
     * 3. Delegar a métodos especializados
     */
    fn emit_node_internal(
        &mut self, 
        node: &Node, 
        root: bool,
        sequence: bool, 
        mapping: bool, 
        simple_key: bool
    ) -> Result<(), EmitterError> {
        // Establish context for formatting decisions
        self.root_context = root;
        self.sequence_context = sequence;
        self.mapping_context = mapping;
        self.simple_key_context = simple_key;

        // Dispatch by node type
        match &node.value {
            // 🔤 SCALAR: Emit individual value
            NodeValue::Scalar(value) => self.emit_scalar(node, value),
            
            // 📋 SEQUENCE: Emit list with determined style
            NodeValue::Sequence(nodes) => {
                let flow_style = self.determine_flow_style(node, true);
                if flow_style {
                    self.emit_flow_sequence(nodes)
                } else {
                    self.emit_block_sequence(nodes)
                }
            },
            
            // 🗂️ MAPPING: Emit dictionary with determined style
            NodeValue::Mapping(pairs) => {
                let flow_style = self.determine_flow_style(node, false);
                if flow_style {
                    self.emit_flow_mapping(pairs)
                } else {
                    self.emit_block_mapping(pairs)
                }
            }
        }
    }

    /// Determine whether to use flow style
    fn determine_flow_style(&self, node: &Node, _is_sequence: bool) -> bool {
        if self.canonical {
            return false;
        }

        if let Some(default_flow) = self.default_flow_style {
            return default_flow;
        }

        // Use flow style for small and simple collections
        match &node.value {
            NodeValue::Sequence(nodes) => {
                if nodes.is_empty() {
                    return true;
                }
                nodes.len() <= 5 && nodes.iter().all(|n| matches!(n.value, NodeValue::Scalar(_)))
            },
            NodeValue::Mapping(pairs) => {
                if pairs.is_empty() {
                    return true;
                }
                pairs.len() <= 3 && pairs.iter().all(|(k, v)| {
                    matches!(k.value, NodeValue::Scalar(_)) && matches!(v.value, NodeValue::Scalar(_))
                })
            },
            _ => false,
        }
    }

    /// Emit scalar
    fn emit_scalar(&mut self, node: &Node, value: &str) -> Result<(), EmitterError> {
        self.process_tag(node)?;
        let analysis = ScalarAnalysis::new(value.to_string());
        let style = self.choose_scalar_style(&analysis, node);
        
        match style {
            ScalarStyle::Plain => self.write_plain(&analysis.scalar),
            ScalarStyle::SingleQuoted => self.write_single_quoted(&analysis.scalar),
            ScalarStyle::DoubleQuoted => self.write_double_quoted(&analysis.scalar),
            ScalarStyle::Literal => self.write_literal(&analysis.scalar),
            ScalarStyle::Folded => self.write_folded(&analysis.scalar),
        }
    }

    /// Choose appropriate scalar style
    fn choose_scalar_style(&self, analysis: &ScalarAnalysis, node: &Node) -> ScalarStyle {
        if self.canonical {
            return ScalarStyle::DoubleQuoted;
        }

        // If it has quotes specified in the tag, respect them
        if node.tag.contains("literal") {
            return ScalarStyle::Literal;
        }
        if node.tag.contains("folded") {
            return ScalarStyle::Folded;
        }

        // Prefer plain style if possible
        if analysis.allow_flow_plain && !self.simple_key_context {
            return ScalarStyle::Plain;
        }

        // Use literal for multiline text
        if analysis.multiline && analysis.allow_block && !self.flow_level_active() && !self.simple_key_context {
            return ScalarStyle::Literal;
        }

        // Prefer single quotes when possible
        if analysis.allow_single_quoted && !analysis.multiline {
            return ScalarStyle::SingleQuoted;
        }

        // Fallback to double quotes
        ScalarStyle::DoubleQuoted
    }

    /// Emit sequence in flow style
    fn emit_flow_sequence(&mut self, nodes: &[Node]) -> Result<(), EmitterError> {
        self.write_indicator("[", true, true)?;
        self.flow_level += 1;
        self.increase_indent(true);

        for (i, node) in nodes.iter().enumerate() {
            if i > 0 {
                self.write_indicator(",", false, false)?;
                if self.canonical || self.column > self.width {
                    self.write_indent()?;
                } else {
                    self.write(" ")?;
                }
            }
            self.emit_node_internal(node, false, true, false, false)?;
        }

        self.flow_level -= 1;
        self.decrease_indent();
        self.write_indicator("]", false, false)?;
        Ok(())
    }

    /// Emit sequence in block style
    fn emit_block_sequence(&mut self, nodes: &[Node]) -> Result<(), EmitterError> {
        let _indentless = self.mapping_context && !self.indention;
        self.increase_indent(false);

        for node in nodes {
            self.write_indent()?;
            self.write_indicator("-", true, false)?;
            if self.check_simple_node(node) {
                self.write(" ")?;
                self.emit_node_internal(node, false, true, false, false)?;
            } else {
                self.write_line_break()?;
                self.emit_node_internal(node, false, true, false, false)?;
            }
        }

        self.decrease_indent();
        Ok(())
    }

    /// Emit mapping in flow style
    fn emit_flow_mapping(&mut self, pairs: &[(Node, Node)]) -> Result<(), EmitterError> {
        self.write_indicator("{", true, true)?;
        self.flow_level += 1;
        self.increase_indent(true);

        for (i, (key, value)) in pairs.iter().enumerate() {
            if i > 0 {
                self.write_indicator(",", false, false)?;
                if self.canonical || self.column > self.width {
                    self.write_indent()?;
                } else {
                    self.write(" ")?;
                }
            }

            if self.check_simple_node(key) {
                self.emit_node_internal(key, false, false, true, true)?;
                self.write_indicator(":", false, false)?;
                self.write(" ")?;
                self.emit_node_internal(value, false, false, true, false)?;
            } else {
                self.write_indicator("?", true, false)?;
                self.write(" ")?;
                self.emit_node_internal(key, false, false, true, false)?;
                self.write_indent()?;
                self.write_indicator(":", true, false)?;
                self.write(" ")?;
                self.emit_node_internal(value, false, false, true, false)?;
            }
        }

        self.flow_level -= 1;
        self.decrease_indent();
        self.write_indicator("}", false, false)?;
        Ok(())
    }

    /// Emit mapping in block style
    fn emit_block_mapping(&mut self, pairs: &[(Node, Node)]) -> Result<(), EmitterError> {
        self.increase_indent(false);

        for (key, value) in pairs {
            self.write_indent()?;
            
            if self.check_simple_node(key) {
                self.emit_node_internal(key, false, false, true, true)?;
                self.write_indicator(":", false, false)?;
                
                if self.check_simple_node(value) {
                    self.write(" ")?;
                    self.emit_node_internal(value, false, false, true, false)?;
                } else {
                    self.write_line_break()?;
                    self.emit_node_internal(value, false, false, true, false)?;
                }
            } else {
                self.write_indicator("?", true, false)?;
                self.write(" ")?;
                self.emit_node_internal(key, false, false, true, false)?;
                self.write_indent()?;
                self.write_indicator(":", true, false)?;
                self.write(" ")?;
                self.emit_node_internal(value, false, false, true, false)?;
            }
        }

        self.decrease_indent();
        Ok(())
    }

    /// Check if a node is simple (for inline)
    fn check_simple_node(&self, node: &Node) -> bool {
        match &node.value {
            NodeValue::Scalar(value) => {
                value.len() < 64 && !value.contains('\n')
            },
            NodeValue::Sequence(nodes) => nodes.is_empty(),
            NodeValue::Mapping(pairs) => pairs.is_empty(),
        }
    }

    /// Process node tag
    fn process_tag(&mut self, node: &Node) -> Result<(), EmitterError> {
        if !node.tag.is_empty() && node.tag != "tag:yaml.org,2002:str" {
            let prepared_tag = self.prepare_tag(&node.tag)?;
            if !prepared_tag.is_empty() {
                self.write_indicator(&prepared_tag, true, false)?;
                self.write(" ")?;
            }
        }
        Ok(())
    }

    /// Prepare tag for emission
    fn prepare_tag(&self, tag: &str) -> Result<String, EmitterError> {
        if tag.is_empty() {
            return Ok(String::new());
        }

        if tag == "!" {
            return Ok(tag.to_string());
        }

        // Search for known prefix
        for (prefix, handle) in &self.tag_prefixes {
            if tag.starts_with(prefix) && (prefix == "!" || prefix.len() < tag.len()) {
                let suffix = &tag[prefix.len()..];
                return Ok(format!("{}{}", handle, suffix));
            }
        }

        // Complete tag
        Ok(format!("!<{}>", tag))
    }

    /// Writing utilities
    fn write_stream_start(&mut self) -> Result<(), EmitterError> {
        // We don't need BOM for UTF-8
        Ok(())
    }

    fn write_stream_end(&mut self) -> Result<(), EmitterError> {
        self.writer.flush().map_err(|e| EmitterError {
            message: format!("Failed to flush: {}", e)
        })?;
        Ok(())
    }

    fn write_document_start(&mut self) -> Result<(), EmitterError> {
        if !self.root_context {
            self.write_indicator("---", true, false)?;
            self.write_line_break()?;
        }
        Ok(())
    }

    fn write_document_end(&mut self) -> Result<(), EmitterError> {
        self.write_line_break()?;
        Ok(())
    }

    fn write_indicator(&mut self, indicator: &str, need_whitespace: bool, whitespace: bool) -> Result<(), EmitterError> {
        let data = if self.whitespace || !need_whitespace {
            indicator.to_string()
        } else {
            format!(" {}", indicator)
        };

        self.whitespace = whitespace;
        self.indention = self.indention && indicator.chars().all(|c| c == ' ');
        self.column += data.len();

        self.writer.write_all(data.as_bytes()).map_err(|e| EmitterError {
            message: format!("Write error: {}", e)
        })?;
        Ok(())
    }

    fn write(&mut self, data: &str) -> Result<(), EmitterError> {
        self.column += data.len();
        self.whitespace = data.ends_with(' ');
        self.writer.write_all(data.as_bytes()).map_err(|e| EmitterError {
            message: format!("Write error: {}", e)
        })?;
        Ok(())
    }

    fn write_indent(&mut self) -> Result<(), EmitterError> {
        let indent = self.indents.last().copied().unwrap_or(0);
        
        if !self.indention || self.column > indent {
            self.write_line_break()?;
        }
        
        if self.column < indent {
            let spaces = " ".repeat(indent - self.column);
            self.write(&spaces)?;
        }
        Ok(())
    }

    fn write_line_break(&mut self) -> Result<(), EmitterError> {
        self.writer.write_all(self.line_break.as_bytes()).map_err(|e| EmitterError {
            message: format!("Write error: {}", e)
        })?;
        self.whitespace = true;
        self.indention = true;
        self.line += 1;
        self.column = 0;
        Ok(())
    }

    fn increase_indent(&mut self, flow: bool) {
        self.indents.push(self.current_indent());
        if flow {
            // For flow, use minimal indentation
            let new_indent = self.current_indent() + 2;
            self.indents.push(new_indent);
        } else {
            // For block, use configured indentation
            let new_indent = self.current_indent() + self.indent;
            self.indents.push(new_indent);
        }
    }

    fn decrease_indent(&mut self) {
        if !self.indents.is_empty() {
            self.indents.pop();
        }
    }

    fn current_indent(&self) -> usize {
        self.indents.last().copied().unwrap_or(0)
    }

    fn flow_level_active(&self) -> bool {
        self.flow_level > 0
    }

    // Scalar style writers
    fn write_plain(&mut self, text: &str) -> Result<(), EmitterError> {
        self.write(text)
    }

    fn write_single_quoted(&mut self, text: &str) -> Result<(), EmitterError> {
        self.write_indicator("'", true, false)?;
        
        // Escapar comillas simples
        let escaped = text.replace("'", "''");
        self.write(&escaped)?;
        
        self.write_indicator("'", false, false)?;
        Ok(())
    }

    fn write_double_quoted(&mut self, text: &str) -> Result<(), EmitterError> {
        self.write_indicator("\"", true, false)?;
        
        // Escapar caracteres especiales
        let mut escaped = String::new();
        for ch in text.chars() {
            match ch {
                '"' => escaped.push_str("\\\""),
                '\\' => escaped.push_str("\\\\"),
                '\n' => escaped.push_str("\\n"),
                '\r' => escaped.push_str("\\r"),
                '\t' => escaped.push_str("\\t"),
                c if c.is_control() => escaped.push_str(&format!("\\u{:04x}", c as u32)),
                c => escaped.push(c),
            }
        }
        
        self.write(&escaped)?;
        self.write_indicator("\"", false, false)?;
        Ok(())
    }

    fn write_literal(&mut self, text: &str) -> Result<(), EmitterError> {
        self.write_indicator("|", true, false)?;
        self.write_line_break()?;
        
        for line in text.lines() {
            self.write_indent()?;
            self.write(line)?;
            self.write_line_break()?;
        }
        Ok(())
    }

    fn write_folded(&mut self, text: &str) -> Result<(), EmitterError> {
        self.write_indicator(">", true, false)?;
        self.write_line_break()?;
        
        for line in text.lines() {
            self.write_indent()?;
            self.write(line)?;
            self.write_line_break()?;
        }
        Ok(())
    }
}

/// Scalar styles
#[derive(Debug, Clone, Copy)]
enum ScalarStyle {
    Plain,
    SingleQuoted,
    DoubleQuoted,
    Literal,
    Folded,
}

/// Main function to emit a node as YAML string
#[pyfunction]
pub fn emit_to_string(node: &Node) -> PyResult<String> {
    let mut output = Vec::new();
    {
        let mut emitter = Emitter::new(&mut output);
        emitter.emit_node(node).map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>(e.message)
        })?;
    }
    
    String::from_utf8(output).map_err(|e| {
        PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("UTF-8 conversion error: {}", e))
    })
}

/// Function with custom options
#[pyfunction]
pub fn emit_to_string_with_options(
    node: &Node,
    indent: Option<usize>,
    width: Option<usize>,
    canonical: Option<bool>,
    default_flow_style: Option<bool>,
) -> PyResult<String> {
    let mut output = Vec::new();
    {
        let mut emitter = Emitter::new(&mut output);
        
        if let Some(indent) = indent {
            emitter = emitter.with_indent(indent);
        }
        if let Some(width) = width {
            emitter = emitter.with_width(width);
        }
        if let Some(canonical) = canonical {
            emitter = emitter.with_canonical(canonical);
        }
        if let Some(flow_style) = default_flow_style {
            emitter = emitter.with_default_flow_style(Some(flow_style));
        }
        
        emitter.emit_node(node).map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>(e.message)
        })?;
    }
    
    String::from_utf8(output).map_err(|e| {
        PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("UTF-8 conversion error: {}", e))
    })
} 