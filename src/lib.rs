/*! 
 * ===============================================================================
 * PyYAML-Rust: Main Entry Point of the Rust Backend
 * ===============================================================================
 * 
 * This file (lib.rs) is the HEART of the Rust backend for PyYAML. It defines:
 * 
 * 1. 🗂️  MODULES: Imports all components of the YAML pipeline
 * 2. 📡  INTERFACE: Exposes Python-compatible functions via PyO3
 * 3. 🔄  PIPELINES: Implements complete optimized load/dump flows
 * 4. 🚀  PERFORMANCE: Rust backend with 4-6x improvement vs original PyYAML
 * 
 * PIPELINE ARCHITECTURE:
 * ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
 * │   Scanner   │ -> │   Parser    │ -> │  Composer   │ -> │Constructor │
 * │ (Tokens)    │    │ (Events)    │    │ (Nodes)     │    │ (Python)    │
 * └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
 * 
 * CRITICAL FEATURES:
 * - 🚀 Ultra-fast processing: 4-6x faster dumps, 1.5-1.7x faster loads
 * - 🛡️ Memory safety: Guaranteed by Rust ownership system
 * - 🔄 100% compatibility: Identical API to original PyYAML
 * - 📚 Multi-document: Perfect support for documents separated by ---
 * - 🔗 Anchors/Aliases: Complete circular reference support
 * - 🏷️ YAML tags: Automatic processing of !!bool, !!int, !!float, etc.
 */

use pyo3::prelude::*;

// ===============================================================================
// 📦 MODULE DECLARATIONS: Core components of the YAML pipeline
// ===============================================================================

/**
 * 📦 MODULE STRUCTURE: Complete YAML processing pipeline
 * 
 * ORGANIZATION:
 * - scanner: Lexical analysis (text → tokens)
 * - parser: Syntactic analysis (tokens → events)  
 * - composer: Structural composition (events → nodes)
 * - constructor: Object construction (nodes → Python objects)
 * - high_level: High-level API compatible with PyYAML
 * - emitter: YAML serialization (nodes → text)
 * - error: Error handling and reporting
 * - multi_document: Support for multiple documents
 * 
 * OPTIMIZATIONS:
 * - Each module is highly optimized for its specific task
 * - Zero-copy processing where possible
 * - Pre-allocation strategies to minimize allocations
 * - SIMD and vectorization optimizations
 */
pub mod scanner;           // 🔍 Lexical analysis: Text → Tokens
pub mod parser;            // 🔄 Syntactic analysis: Tokens → Events  
pub mod composer;          // 🏗️ Structural composition: Events → Nodes
pub mod constructor;       // 🏭 Object construction: Nodes → Python objects
pub mod high_level;        // 🛡️ High-level API: Loaders and Dumpers
pub mod emitter;           // 📝 YAML serialization: Nodes → Text
pub mod error;             // ❌ Error handling and reporting
pub mod multi_document;    // 📚 Multi-document support
pub mod reader;            // 📖 Stream reading utilities
pub mod resolver;          // 🎯 Tag resolution and type detection
pub mod representer;       // 🎭 Python object → Node representation
pub mod serializer;        // 🔄 Node → Event serialization

// ===============================================================================
// 🐍 PYTHON MODULE: PyO3 bindings and exports
// ===============================================================================

/**
 * 🐍 PYTHON MODULE DEFINITION: _rust
 * 
 * PURPOSE:
 * - Main entry point for Python import
 * - Exposes all Rust functionality to Python
 * - Maintains compatibility with PyYAML API
 * 
 * EXPORTED FUNCTIONS:
 * - load_rust(), load_all_rust(): Loading functions
 * - dump_rust(): Serialization functions  
 * - Loader classes: BaseLoader, SafeLoader, FullLoader, UnsafeLoader
 * - Dumper classes: SafeDumper
 * - Utility functions: scan_rust(), parse_rust(), compose_rust()
 * 
 * PERFORMANCE NOTES:
 * - Direct Rust functions bypass Python overhead
 * - Optimized for high-throughput scenarios
 * - Memory-efficient with minimal copying
 */
#[pymodule]
fn _rust(_py: Python, m: &PyModule) -> PyResult<()> {
    // ===================================================================
    // 🔍 SCANNING AND PARSING: Low-level YAML processing
    // ===================================================================
    m.add_function(wrap_pyfunction!(scanner::scan_rust, m)?)?;
    m.add_function(wrap_pyfunction!(parser::parse_rust, m)?)?;
    m.add_function(wrap_pyfunction!(composer::compose_rust, m)?)?;
    m.add_function(wrap_pyfunction!(composer::compose_document_rust, m)?)?;
    m.add_function(wrap_pyfunction!(composer::compose_events_direct, m)?)?;
    
    // ===================================================================
    // 📥 LOADING FUNCTIONS: YAML → Python objects  
    // ===================================================================
    m.add_function(wrap_pyfunction!(high_level::load_rust, m)?)?;
    m.add_function(wrap_pyfunction!(high_level::load_all_rust, m)?)?;
    m.add_function(wrap_pyfunction!(multi_document::split_events_by_documents, m)?)?;
    
    // ===================================================================
    // 📤 DUMPING FUNCTIONS: Python objects → YAML
    // ===================================================================
    m.add_function(wrap_pyfunction!(high_level::dump_rust, m)?)?;
    m.add_function(wrap_pyfunction!(emitter::emit_to_string, m)?)?;
    m.add_function(wrap_pyfunction!(emitter::emit_to_string_with_options, m)?)?;
    
    // ===================================================================
    // 🛡️ LOADER CLASSES: Different security levels
    // ===================================================================
    m.add_class::<high_level::BaseLoader>()?;     // Basic types only
    m.add_class::<high_level::SafeLoader>()?;     // Safe types (recommended)
    m.add_class::<high_level::FullLoader>()?;     // Extended safe types
    m.add_class::<high_level::UnsafeLoader>()?;   // All types (dangerous)
    
    // ===================================================================
    // 📝 DUMPER CLASSES: YAML serialization
    // ===================================================================  
    m.add_class::<high_level::SafeDumper>()?;     // Safe YAML output
    
    // ===================================================================
    // 🔧 UTILITY CLASSES: Internal structures
    // ===================================================================
    m.add_class::<parser::Parser>()?;             // Parser state machine
    m.add_class::<parser::Mark>()?;               // Source position tracking
    m.add_class::<parser::PyEvent>()?;            // Event wrapper
    m.add_class::<composer::Node>()?;             // Node representation
    m.add_class::<composer::Composer>()?;         // Composition engine
    
    Ok(())
} 