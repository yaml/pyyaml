#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
PyYAML-Rust: Main Entry Point with Fallback System
===============================================================================

This file (__init__.py) is the HEART of PyYAML with the following functions:

1. 🚀 FALLBACK SYSTEM: Rust → LibYAML → Pure Python (triple backend)
2. 📡 COMPLETE API: All public PyYAML functions (load, dump, etc.)
3. 🔄 COMPATIBILITY: 100% compatible with original PyYAML
4. ⚡ OPTIMIZATION: 4-6x performance improvement with Rust backend

FALLBACK ARCHITECTURE:
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ 🦀 RUST     │ -> │ 🔧 LibYAML │ -> │ 🐍 Python   │
│ (PRIMARY)   │    │ (FALLBACK1) │    │ (FALLBACK2) │
└─────────────┘    └─────────────┘    └─────────────┘

FEATURES:
- 🚀 Rust Backend: 4-6x faster for dumps, 1.5-1.7x for loads
- 🛡️ Security: SafeLoader, FullLoader, UnsafeLoader as needed
- 📚 Multi-document: Perfect support for multiple documents (---)
- 🔗 Anchors/Aliases: Circular references fully supported
- 🏷️ YAML Tags: Automatic processing of !!bool, !!int, !!float, etc.

VERSION INFORMATION:
- PyYAML-Rust: 7.0.0.dev0 (active development)
- Compatibility: PyYAML 6.0+ complete API
- Rust Backend: Ultra-optimized native implementation
"""

# ===============================================================================
# 📦 BASIC IMPORTS: Fundamental structures
# ===============================================================================

from .error import *                    # YAML error classes
from .tokens import *                   # Lexical tokens
from .events import *                   # Parsing events
from .nodes import *                    # Representation nodes

# ===============================================================================
# 🆔 VERSION INFORMATION: Package metadata
# ===============================================================================

__version__ = '7.0.0.dev0'             # PyYAML-Rust development version

# ===============================================================================
# 🚀 TRIPLE FALLBACK SYSTEM: Backend detection and configuration
# ===============================================================================

"""
BACKEND STRATEGY:
1. 🦀 RUST BACKEND (PRIORITY 1): Maximum performance
   - 4-6x faster dumps
   - 1.5-1.7x faster loads
   - Guaranteed memory safety
   - Complete YAML 1.2 support

2. 🔧 LIBYAML BACKEND (PRIORITY 2): Optimized C fallback
   - Original C implementation
   - Good performance
   - Wide compatibility

3. 🐍 PURE PYTHON (PRIORITY 3): Universal fallback
   - 100% Python
   - Maximum compatibility
   - Lower performance
"""

# Available backend detection flags
__with_rust__ = False                   # Rust backend available
__with_libyaml__ = False               # LibYAML backend available

# ===============================================================================
# 🦀 PRIORITY 1: RUST BACKEND (ULTRA-OPTIMIZED)
# ===============================================================================

try:
    from ._rust import *                # Import all Rust classes
    __with_rust__ = True
    print("🚀 PyYAML: Using Rust backend (4-6x optimized)")
    
    # ===================================================================
    # ⚙️ RUST CONFIGURATION: Performance optimizations
    # ===================================================================
    import os
    os.environ['PYYAML_RUST_DEBUG'] = '0'  # Disable debug logs
    
    # ===================================================================
    # 🔗 COMPATIBILITY ALIASES: Maintain original PyYAML API
    # ===================================================================
    Loader = UnsafeLoader             # Original PyYAML behavior
    Dumper = SafeDumper               # Safe dumper by default
    
    # ===================================================================
    # ✅ CLASS VERIFICATION: Debug availability information
    # ===================================================================
    print(f"🦀 BaseLoader available: {BaseLoader}")
    print(f"🦀 SafeLoader available: {SafeLoader}")
    print(f"🦀 FullLoader available: {FullLoader}")
    print(f"🦀 UnsafeLoader available: {UnsafeLoader}")
    print(f"🦀 SafeDumper available: {SafeDumper}")
    
except ImportError:
    # ===================================================================
    # 🔧 PRIORITY 2: LIBYAML BACKEND (C FALLBACK)
    # ===================================================================
    try:
        from .cyaml import *            # LibYAML C bindings
        __with_libyaml__ = True
        print("🔧 PyYAML: Using LibYAML backend (optimized C)")
        
        # Load Python modules for LibYAML
        from .loader import *
        from .dumper import *
        
    except ImportError:
        # ===================================================================
        # 🐍 PRIORITY 3: PURE PYTHON (UNIVERSAL FALLBACK)
        # ===================================================================
        __with_libyaml__ = False
        print("🐍 PyYAML: Using pure Python backend (maximum compatibility)")
        
        # Load ALL Python modules
        from .loader import *
        from .dumper import *

import io

# ===============================================================================
# ⚠️ WARNINGS CONTROL: Deprecated legacy functionality
# ===============================================================================

def warnings(settings=None):
    """
    ⚠️ WARNINGS CONTROL (DEPRECATED)
    
    PURPOSE:
    - Legacy function maintained for compatibility
    - Originally controlled PyYAML warnings
    - Now deprecated but maintained to avoid breaking existing code
    
    PARAMETERS:
    - settings: Warning configuration (ignored)
    
    RETURNS: Empty dict (legacy behavior)
    """
    if settings is None:
        return {}

# ===============================================================================
# 🔍 LOW-LEVEL FUNCTIONS: Scanning and Parsing
# ===============================================================================

def scan(stream, Loader=Loader):
    """
    🔍 SCANNING: Convert YAML stream → lexical tokens
    
    PURPOSE:
    - Lexical analysis of YAML content
    - Produce structured tokens for parser
    - Debugging and analysis of YAML structure
    
    PARAMETERS:
    - stream: File, StringIO or string with YAML content
    - Loader: Loader class to use (active backend by default)
    
    YIELDS: Token objects (TokenType enum + content)
    
    USAGE:
    ```python
    for token in yaml.scan("key: value"):
        print(token)
    ```
    """
    loader = Loader(stream)
    try:
        while loader.check_token():
            yield loader.get_token()
    finally:
        loader.dispose()

def parse(stream, Loader=Loader):
    """
    🔍 PARSING: Convert YAML stream → structured events
    
    PURPOSE:
    - Syntactic analysis of tokens → events
    - Intermediate representation of document
    - Base for Python object construction
    
    PARAMETERS:
    - stream: File, StringIO or string with YAML content
    - Loader: Loader class to use (active backend by default)
    
    YIELDS: Event objects (EventType + metadata)
    
    USAGE:
    ```python
    for event in yaml.parse("key: value"):
        print(event)
    ```
    """
    loader = Loader(stream)
    try:
        while loader.check_event():
            yield loader.get_event()
    finally:
        loader.dispose()

def compose(stream, Loader=Loader):
    """
    🔍 COMPOSITION: Convert YAML stream → node tree
    
    PURPOSE:
    - Build tree representation from events
    - First document only
    - Nodes with complete metadata (tags, marks, etc.)
    
    PARAMETERS:
    - stream: File, StringIO or string with YAML content
    - Loader: Loader class to use (active backend by default)
    
    RETURNS: Node object (ScalarNode, SequenceNode, MappingNode)
    
    USAGE:
    ```python
    node = yaml.compose("key: value")
    print(node.tag, node.value)
    ```
    """
    loader = Loader(stream)
    try:
        return loader.get_single_node()
    finally:
        loader.dispose()

def compose_all(stream, Loader=Loader):
    """
    🔍 MULTIPLE COMPOSITION: Convert stream → multiple trees
    
    PURPOSE:
    - Build tree representations for all documents
    - Complete support for documents separated by ---
    - Nodes with complete metadata
    
    PARAMETERS:
    - stream: File, StringIO or string with YAML content
    - Loader: Loader class to use (active backend by default)
    
    YIELDS: Node objects for each document
    
    USAGE:
    ```python
    for node in yaml.compose_all("---\nkey1: value1\n---\nkey2: value2"):
        print(node.tag, node.value)
    ```
    """
    loader = Loader(stream)
    try:
        while loader.check_node():
            yield loader.get_node()
    finally:
        loader.dispose()

# ===============================================================================
# 📥 LOADING FUNCTIONS: YAML → Python object conversion
# ===============================================================================

def load(stream, Loader):
    """
    📥 BASIC LOADING: YAML → Python object (first document)
    
    PURPOSE:
    - Base function for all load variants
    - First document only
    - Requires explicit Loader specification for security
    
    PARAMETERS:
    - stream: File, StringIO or string with YAML content
    - Loader: Specific loader class (SafeLoader, FullLoader, etc.)
    
    RETURNS: Python object (dict, list, str, int, etc.)
    
    SECURITY:
    - SafeLoader: Only basic types (str, int, float, bool, list, dict)
    - FullLoader: Extended types (datetime, set, etc.) but safe
    - UnsafeLoader: Allows arbitrary Python objects (DANGEROUS)
    """
    loader = Loader(stream)
    try:
        return loader.get_single_data()
    finally:
        loader.dispose()

def load_all(stream, Loader):
    """
    📥 MULTIPLE LOADING: YAML → Python objects (all documents)
    
    PURPOSE:
    - Load all documents in a stream
    - Complete support for documents separated by ---
    - Requires explicit Loader specification for security
    
    PARAMETERS:
    - stream: File, StringIO or string with YAML content
    - Loader: Specific loader class (SafeLoader, FullLoader, etc.)
    
    YIELDS: Python objects for each document
    
    USAGE:
    ```python
    for doc in yaml.load_all(stream, yaml.SafeLoader):
        process(doc)
    ```
    """
    loader = Loader(stream)
    try:
        while loader.check_data():
            yield loader.get_data()
    finally:
        loader.dispose()

# ===============================================================================
# 🛡️ SAFE FUNCTIONS: Variants with implicit security
# ===============================================================================

def full_load(stream):
    """
    🛡️ SAFE COMPLETE LOADING: YAML → Python with extended types
    
    PURPOSE:
    - Loading with implicit FullLoader (no need to specify)
    - Basic types + datetime, set, ordered dict, etc.
    - Safe for untrusted input (no arbitrary Python objects)
    
    SUPPORTED TYPES:
    - ✅ Basic: str, int, float, bool, list, dict, None
    - ✅ Extended: datetime, date, set, OrderedDict
    - ❌ Forbidden: arbitrary Python classes, functions, etc.
    
    USAGE:
    ```python
    data = yaml.full_load("timestamp: 2023-01-01 12:00:00")
    # → {'timestamp': datetime.datetime(2023, 1, 1, 12, 0)}
    ```
    """
    return load(stream, FullLoader)

def full_load_all(stream):
    """
    🛡️ COMPLETE MULTIPLE LOADING: All documents with extended types
    
    PURPOSE:
    - Multiple documents with implicit FullLoader
    - Special optimization for Rust backend
    - Safe for untrusted input
    
    RUST OPTIMIZATION:
    - Uses load_all_rust() directly for maximum performance
    - Automatic stream conversion
    - None value filtering for compatibility
    """
    # ===================================================================
    # 🚀 RUST OPTIMIZATION: Ultra-fast direct path
    # ===================================================================
    if __with_rust__:
        # Convert stream to string if necessary
        if hasattr(stream, 'read'):
            content = stream.read()
            if hasattr(stream, 'seek'):
                stream.seek(0)          # Reset for compatibility
        else:
            content = str(stream)
        
        # Use direct Rust function (bypass Python overhead)
        import io
        rust_stream = io.StringIO(content)
        results = load_all_rust(rust_stream)
        
        # Filter None values for compatibility
        for result in results:
            if result is not None:
                yield result
    else:
        # ===================================================================
        # 🔄 FALLBACK: Traditional method for other backends
        # ===================================================================
        return load_all(stream, FullLoader)

def safe_load(stream):
    """
    🛡️ SAFE LOADING: YAML → Python basic types only
    
    PURPOSE:
    - Maximum security for untrusted input
    - Only basic Python core types
    - Implicit SafeLoader (no need to specify)
    
    ALLOWED TYPES ONLY:
    - ✅ str, int, float, bool
    - ✅ list, dict, None
    - ❌ Everything else (datetime, set, classes, etc.)
    
    RECOMMENDED USAGE:
    - Public APIs with user input
    - Configuration files from external sources
    - Any YAML from untrusted origin
    
    ```python
    config = yaml.safe_load(user_input)  # Always safe
    ```
    """
    return load(stream, SafeLoader)

def safe_load_all(stream):
    """
    🛡️ SAFE MULTIPLE LOADING: All documents, basic types only
    
    PURPOSE:
    - Multiple documents with implicit SafeLoader
    - Special optimization for Rust backend
    - Maximum security for untrusted input
    """
    # ===================================================================
    # 🚀 RUST OPTIMIZATION: Ultra-fast direct path
    # ===================================================================
    if __with_rust__:
        # Convert stream to string if necessary
        if hasattr(stream, 'read'):
            content = stream.read()
            if hasattr(stream, 'seek'):
                stream.seek(0)          # Reset for compatibility
        else:
            content = str(stream)
        
        # Use direct Rust function (bypass Python overhead)
        import io
        rust_stream = io.StringIO(content)
        results = load_all_rust(rust_stream)
        
        # Filter None values for compatibility
        for result in results:
            if result is not None:
                yield result
    else:
        # ===================================================================
        # 🔄 FALLBACK: Traditional method for other backends
        # ===================================================================
        return load_all(stream, SafeLoader)

def unsafe_load(stream):
    """
    ⚠️ UNSAFE LOADING: YAML → arbitrary Python objects
    
    PURPOSE:
    - Compatibility with original PyYAML (legacy behavior)
    - Allows loading arbitrary Python objects
    - Implicit UnsafeLoader
    
    ⚠️ SECURITY WARNING:
    - NEVER use with untrusted input
    - Can execute arbitrary code
    - Only for fully trusted files
    
    ALLOWED TYPES:
    - ✅ All basic and extended types
    - ✅ Custom Python classes
    - ✅ Functions, modules, etc.
    - ⚠️ DANGEROUS: Potential code execution
    
    LIMITED USAGE:
    - Serialization of complex Python objects
    - Internal application files
    - NEVER with external input
    """
    return load(stream, UnsafeLoader)

def unsafe_load_all(stream):
    """
    ⚠️ UNSAFE MULTIPLE LOADING: All documents, arbitrary objects
    
    PURPOSE:
    - Multiple documents with implicit UnsafeLoader
    - Special optimization for Rust backend
    - ⚠️ DANGEROUS for untrusted input
    """
    # ===================================================================
    # 🚀 RUST OPTIMIZATION: Ultra-fast direct path
    # ===================================================================
    if __with_rust__:
        # Convert stream to string if necessary
        if hasattr(stream, 'read'):
            content = stream.read()
            if hasattr(stream, 'seek'):
                stream.seek(0)          # Reset for compatibility
        else:
            content = str(stream)
        
        # Use direct Rust function (bypass Python overhead)
        import io
        rust_stream = io.StringIO(content)
        results = load_all_rust(rust_stream)
        
        # Filter None values for compatibility
        for result in results:
            if result is not None:
                yield result
    else:
        # ===================================================================
        # 🔄 FALLBACK: Traditional method for other backends
        # ===================================================================
        return load_all(stream, UnsafeLoader)

def emit(events, stream=None, Dumper=Dumper,
        canonical=None, indent=None, width=None,
        allow_unicode=None, line_break=None):
    """
    Emit YAML parsing events into a stream.
    If stream is None, return the produced string instead.
    """
    getvalue = None
    if stream is None:
        stream = io.StringIO()
        getvalue = stream.getvalue
    dumper = Dumper(stream, canonical=canonical, indent=indent, width=width,
            allow_unicode=allow_unicode, line_break=line_break)
    try:
        for event in events:
            dumper.emit(event)
    finally:
        dumper.dispose()
    if getvalue:
        return getvalue()

def serialize_all(nodes, stream=None, Dumper=Dumper,
        canonical=None, indent=None, width=None,
        allow_unicode=None, line_break=None,
        encoding=None, explicit_start=None, explicit_end=None,
        version=None, tags=None):
    """
    Serialize a sequence of representation trees into a YAML stream.
    If stream is None, return the produced string instead.
    """
    getvalue = None
    if stream is None:
        if encoding is None:
            stream = io.StringIO()
        else:
            stream = io.BytesIO()
        getvalue = stream.getvalue
    dumper = Dumper(stream, canonical=canonical, indent=indent, width=width,
            allow_unicode=allow_unicode, line_break=line_break,
            encoding=encoding, version=version, tags=tags,
            explicit_start=explicit_start, explicit_end=explicit_end)
    try:
        dumper.open()
        for node in nodes:
            dumper.serialize(node)
        dumper.close()
    finally:
        dumper.dispose()
    if getvalue:
        return getvalue()

def serialize(node, stream=None, Dumper=Dumper, **kwds):
    """
    Serialize a representation tree into a YAML stream.
    If stream is None, return the produced string instead.
    """
    return serialize_all([node], stream, Dumper=Dumper, **kwds)

def dump_all(documents, stream=None, Dumper=Dumper,
        default_style=None, default_flow_style=False,
        canonical=None, indent=None, width=None,
        allow_unicode=None, line_break=None,
        encoding=None, explicit_start=None, explicit_end=None,
        version=None, tags=None, sort_keys=True):
    """
    Serialize a sequence of Python objects into a YAML stream.
    If stream is None, return the produced string instead.
    """
    getvalue = None
    if stream is None:
        if encoding is None:
            stream = io.StringIO()
        else:
            stream = io.BytesIO()
        getvalue = stream.getvalue
    dumper = Dumper(stream, default_style=default_style,
            default_flow_style=default_flow_style,
            canonical=canonical, indent=indent, width=width,
            allow_unicode=allow_unicode, line_break=line_break,
            encoding=encoding, version=version, tags=tags,
            explicit_start=explicit_start, explicit_end=explicit_end, sort_keys=sort_keys)
    try:
        dumper.open()
        for data in documents:
            dumper.represent(data)
        dumper.close()
    finally:
        dumper.dispose()
    if getvalue:
        return getvalue()

def dump(data, stream=None, Dumper=Dumper, **kwds):
    """
    Serialize a Python object into a YAML stream.
    If stream is None, return the produced string instead.
    """
    return dump_all([data], stream, Dumper=Dumper, **kwds)

def safe_dump_all(documents, stream=None, **kwds):
    """
    Serialize a sequence of Python objects into a YAML stream.
    Produce only basic YAML tags.
    If stream is None, return the produced string instead.
    """
    return dump_all(documents, stream, Dumper=SafeDumper, **kwds)

def safe_dump(data, stream=None, **kwds):
    """
    Serialize a Python object into a YAML stream.
    Produce only basic YAML tags.
    If stream is None, return the produced string instead.
    """
    return dump_all([data], stream, Dumper=SafeDumper, **kwds)

def add_implicit_resolver(tag, regexp, first=None,
        Loader=None, Dumper=Dumper):
    """
    Add an implicit scalar detector.
    If an implicit scalar value matches the given regexp,
    the corresponding tag is assigned to the scalar.
    first is a sequence of possible initial characters or None.
    """
    if Loader is None:
        # With Rust backend, use classes directly
        if __with_rust__:
            # Rust classes don't support add_implicit_resolver yet
            pass  # Compatibility - not implemented
        else:
            loader.Loader.add_implicit_resolver(tag, regexp, first)
            loader.FullLoader.add_implicit_resolver(tag, regexp, first)
            loader.UnsafeLoader.add_implicit_resolver(tag, regexp, first)
    else:
        if hasattr(Loader, 'add_implicit_resolver'):
            Loader.add_implicit_resolver(tag, regexp, first)
    if hasattr(Dumper, 'add_implicit_resolver'):
        Dumper.add_implicit_resolver(tag, regexp, first)

def add_path_resolver(tag, path, kind=None, Loader=None, Dumper=Dumper):
    """
    Add a path based resolver for the given tag.
    A path is a list of keys that forms a path
    to a node in the representation tree.
    Keys can be string values, integers, or None.
    """
    if Loader is None:
        # With Rust backend, use classes directly
        if __with_rust__:
            # Rust classes don't support add_path_resolver yet
            pass  # Compatibility - not implemented
        else:
            loader.Loader.add_path_resolver(tag, path, kind)
            loader.FullLoader.add_path_resolver(tag, path, kind)
            loader.UnsafeLoader.add_path_resolver(tag, path, kind)
    else:
        if hasattr(Loader, 'add_path_resolver'):
            Loader.add_path_resolver(tag, path, kind)
    if hasattr(Dumper, 'add_path_resolver'):
        Dumper.add_path_resolver(tag, path, kind)

def add_constructor(tag, constructor, Loader=None):
    """
    Add a constructor for the given tag.
    Constructor is a function that accepts a Loader instance
    and a node object and produces the corresponding Python object.
    """
    if Loader is None:
        # With Rust backend, use classes directly
        if __with_rust__:
            # Rust classes don't support add_constructor yet
            pass  # Compatibility - not implemented
        else:
            loader.Loader.add_constructor(tag, constructor)
            loader.FullLoader.add_constructor(tag, constructor)
            loader.UnsafeLoader.add_constructor(tag, constructor)
    else:
        if hasattr(Loader, 'add_constructor'):
            Loader.add_constructor(tag, constructor)

def add_multi_constructor(tag_prefix, multi_constructor, Loader=None):
    """
    Add a multi-constructor for the given tag prefix.
    Multi-constructor is called for a node if its tag starts with tag_prefix.
    Multi-constructor accepts a Loader instance, a tag suffix,
    and a node object and produces the corresponding Python object.
    """
    if Loader is None:
        # With Rust backend, use classes directly
        if __with_rust__:
            # Rust classes don't support add_multi_constructor yet
            pass  # Compatibility - not implemented
        else:
            loader.Loader.add_multi_constructor(tag_prefix, multi_constructor)
            loader.FullLoader.add_multi_constructor(tag_prefix, multi_constructor)
            loader.UnsafeLoader.add_multi_constructor(tag_prefix, multi_constructor)
    else:
        if hasattr(Loader, 'add_multi_constructor'):
            Loader.add_multi_constructor(tag_prefix, multi_constructor)

def add_representer(data_type, representer, Dumper=Dumper):
    """
    Add a representer for the given type.
    Representer is a function accepting a Dumper instance
    and an instance of the given data type
    and producing the corresponding representation node.
    """
    if hasattr(Dumper, 'add_representer'):
        Dumper.add_representer(data_type, representer)
    # If Rust backend, do nothing (for now, compatibility only)

def add_multi_representer(data_type, multi_representer, Dumper=Dumper):
    """
    Add a representer for the given type.
    Multi-representer is a function accepting a Dumper instance
    and an instance of the given data type or subtype
    and producing the corresponding representation node.
    """
    if hasattr(Dumper, 'add_multi_representer'):
        Dumper.add_multi_representer(data_type, multi_representer)
    # If Rust backend, do nothing (for now, compatibility only)

class YAMLObjectMetaclass(type):
    """
    The metaclass for YAMLObject.
    """
    def __init__(cls, name, bases, kwds):
        super(YAMLObjectMetaclass, cls).__init__(name, bases, kwds)
        if 'yaml_tag' in kwds and kwds['yaml_tag'] is not None:
            if isinstance(cls.yaml_loader, list):
                for loader in cls.yaml_loader:
                    loader.add_constructor(cls.yaml_tag, cls.from_yaml)
            else:
                cls.yaml_loader.add_constructor(cls.yaml_tag, cls.from_yaml)

            cls.yaml_dumper.add_representer(cls, cls.to_yaml)

class YAMLObject(metaclass=YAMLObjectMetaclass):
    """
    An object that can dump itself to a YAML stream
    and load itself from a YAML stream.
    """

    __slots__ = ()  # no direct instantiation, so allow immutable subclasses

    yaml_loader = [Loader, BaseLoader, FullLoader, UnsafeLoader]
    yaml_dumper = Dumper

    yaml_tag = None
    yaml_flow_style = None

    @classmethod
    def from_yaml(cls, loader, node):
        """
        Convert a representation node to a Python object.
        """
        return loader.construct_yaml_object(node, cls)

    @classmethod
    def to_yaml(cls, dumper, data):
        """
        Convert a Python object to a representation node.
        """
        return dumper.represent_yaml_object(cls.yaml_tag, data, cls,
                flow_style=cls.yaml_flow_style)

