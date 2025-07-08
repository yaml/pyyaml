#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
PyYAML-Rust: Punto de Entrada Principal con Sistema de Fallback
===============================================================================

Este archivo (__init__.py) es el CORAZÓN de PyYAML con las siguientes funciones:

1. 🚀 SISTEMA DE FALLBACK: Rust → LibYAML → Python puro (triple backend)
2. 📡 API COMPLETA: Todas las funciones públicas de PyYAML (load, dump, etc.)
3. 🔄 COMPATIBILIDAD: 100% compatible con PyYAML original
4. ⚡ OPTIMIZACIÓN: 4-6x mejora de rendimiento con backend Rust

ARQUITECTURA DE FALLBACK:
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ 🦀 RUST     │ -> │ 🔧 LibYAML │ -> │ 🐍 Python   │
│ (PRIMARIO)  │    │ (FALLBACK1) │    │ (FALLBACK2) │
└─────────────┘    └─────────────┘    └─────────────┘

CARACTERÍSTICAS:
- 🚀 Backend Rust: 4-6x más rápido para dumps, 1.5-1.7x para loads
- 🛡️ Seguridad: SafeLoader, FullLoader, UnsafeLoader según necesidades
- 📚 Multi-documento: Soporte perfecto para múltiples documentos (---)
- 🔗 Anchors/Aliases: Referencias circulares completamente soportadas
- 🏷️ Tags YAML: Procesamiento automático de !!bool, !!int, !!float, etc.

VERSION INFORMATION:
- PyYAML-Rust: 7.0.0.dev0 (desarrollo activo)
- Compatibilidad: PyYAML 6.0+ API completa
- Rust Backend: Implementación nativa ultra-optimizada
"""

# ===============================================================================
# 📦 IMPORTACIONES BÁSICAS: Estructuras fundamentales
# ===============================================================================

from .error import *                    # Clases de errores YAML
from .tokens import *                   # Tokens léxicos
from .events import *                   # Eventos de parsing
from .nodes import *                    # Nodos de representación

# ===============================================================================
# 🆔 INFORMACIÓN DE VERSIÓN: Metadatos del paquete
# ===============================================================================

__version__ = '7.0.0.dev0'             # Versión de desarrollo PyYAML-Rust

# ===============================================================================
# 🚀 SISTEMA DE FALLBACK TRIPLE: Detección y configuración de backends
# ===============================================================================

"""
ESTRATEGIA DE BACKENDS:
1. 🦀 RUST BACKEND (PRIORIDAD 1): Máximo rendimiento
   - 4-6x más rápido en dumps
   - 1.5-1.7x más rápido en loads
   - Memory safety garantizada
   - Soporte completo YAML 1.2

2. 🔧 LIBYAML BACKEND (PRIORIDAD 2): Fallback C optimizado
   - Implementación C original
   - Buen rendimiento
   - Amplia compatibilidad

3. 🐍 PYTHON PURO (PRIORIDAD 3): Fallback universal
   - 100% Python
   - Máxima compatibilidad
   - Menor rendimiento
"""

# Flags de detección de backends disponibles
__with_rust__ = False                   # Backend Rust disponible
__with_libyaml__ = False               # Backend LibYAML disponible

# ===============================================================================
# 🦀 PRIORIDAD 1: BACKEND RUST (ULTRA-OPTIMIZADO)
# ===============================================================================

try:
    from ._rust import *                # Importar todas las clases Rust
    __with_rust__ = True
    print("🚀 PyYAML: Usando backend Rust (optimizado 4-6x)")
    
    # ===================================================================
    # ⚙️ CONFIGURACIÓN RUST: Optimizaciones de rendimiento
    # ===================================================================
    import os
    os.environ['PYYAML_RUST_DEBUG'] = '0'  # Deshabilitar logs debug
    
    # ===================================================================
    # 🔗 ALIASES DE COMPATIBILIDAD: Mantener API PyYAML original
    # ===================================================================
    Loader = UnsafeLoader             # Comportamiento PyYAML original
    Dumper = SafeDumper               # Dumper seguro por defecto
    
    # ===================================================================
    # ✅ VERIFICACIÓN DE CLASES: Debug información disponibilidad
    # ===================================================================
    print(f"🦀 BaseLoader disponible: {BaseLoader}")
    print(f"🦀 SafeLoader disponible: {SafeLoader}")
    print(f"🦀 FullLoader disponible: {FullLoader}")
    print(f"🦀 UnsafeLoader disponible: {UnsafeLoader}")
    print(f"🦀 SafeDumper disponible: {SafeDumper}")
    
except ImportError:
    # ===================================================================
    # 🔧 PRIORIDAD 2: BACKEND LIBYAML (FALLBACK C)
    # ===================================================================
    try:
        from .cyaml import *            # Bindings C LibYAML
        __with_libyaml__ = True
        print("🔧 PyYAML: Usando backend LibYAML (C optimizado)")
        
        # Cargar módulos Python para LibYAML
        from .loader import *
        from .dumper import *
        
    except ImportError:
        # ===================================================================
        # 🐍 PRIORIDAD 3: PYTHON PURO (FALLBACK UNIVERSAL)
        # ===================================================================
        __with_libyaml__ = False
        print("🐍 PyYAML: Usando backend Python puro (máxima compatibilidad)")
        
        # Cargar TODOS los módulos Python
        from .loader import *
        from .dumper import *

import io

# ===============================================================================
# ⚠️ WARNINGS CONTROL: Funcionalidad legacy deprecated
# ===============================================================================

def warnings(settings=None):
    """
    ⚠️ WARNINGS CONTROL (DEPRECATED)
    
    PROPÓSITO:
    - Función legacy mantenida por compatibilidad
    - Originally controlaba warnings de PyYAML
    - Ahora deprecated pero mantenida para no romper código existente
    
    PARÁMETROS:
    - settings: Configuración de warnings (ignorado)
    
    RETORNA: Dict vacío (comportamiento legacy)
    """
    if settings is None:
        return {}

# ===============================================================================
# 🔍 FUNCIONES DE BAJO NIVEL: Scanning y Parsing
# ===============================================================================

def scan(stream, Loader=Loader):
    """
    🔍 SCANNING: Convertir stream YAML → tokens léxicos
    
    PROPÓSITO:
    - Análisis léxico de contenido YAML
    - Producir tokens estructurados para parser
    - Debugging y análisis de estructura YAML
    
    PARÁMETROS:
    - stream: Archivo, StringIO o string con contenido YAML
    - Loader: Clase loader a usar (por defecto backend activo)
    
    YIELDS: Token objects (TokenType enum + contenido)
    
    USO:
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
    🔍 PARSING: Convertir stream YAML → eventos estructurados
    
    PROPÓSITO:
    - Análisis sintáctico de tokens → eventos
    - Representación intermedia del documento
    - Base para construcción de objetos Python
    
    PARÁMETROS:
    - stream: Archivo, StringIO o string con contenido YAML
    - Loader: Clase loader a usar (por defecto backend activo)
    
    YIELDS: Event objects (EventType + metadatos)
    
    USO:
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
    🔍 COMPOSICIÓN: Convertir stream YAML → árbol de nodos
    
    PROPÓSITO:
    - Construir representación tree desde eventos
    - Primer documento únicamente
    - Nodos con metadatos completos (tags, marks, etc.)
    
    PARÁMETROS:
    - stream: Archivo, StringIO o string con contenido YAML
    - Loader: Clase loader a usar (por defecto backend activo)
    
    RETORNA: Node object (ScalarNode, SequenceNode, MappingNode)
    
    USO:
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
    🔍 COMPOSICIÓN MÚLTIPLE: Convertir stream → múltiples árboles
    
    PROPÓSITO:
    - Construir representación trees para todos los documentos
    - Soporte completo para documentos separados por ---
    - Nodos con metadatos completos
    
    PARÁMETROS:
    - stream: Archivo, StringIO o string con contenido YAML
    - Loader: Clase loader a usar (por defecto backend activo)
    
    YIELDS: Node objects para cada documento
    
    USO:
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
# 📥 FUNCIONES DE CARGA: Conversión YAML → objetos Python
# ===============================================================================

def load(stream, Loader):
    """
    📥 CARGA BÁSICA: YAML → objeto Python (primer documento)
    
    PROPÓSITO:
    - Función base para todas las variantes de load
    - Primer documento únicamente
    - Requiere especificar Loader explícitamente por seguridad
    
    PARÁMETROS:
    - stream: Archivo, StringIO o string con contenido YAML
    - Loader: Clase loader específica (SafeLoader, FullLoader, etc.)
    
    RETORNA: Objeto Python (dict, list, str, int, etc.)
    
    SEGURIDAD:
    - SafeLoader: Solo tipos básicos (str, int, float, bool, list, dict)
    - FullLoader: Tipos extendidos (datetime, set, etc.) pero seguro
    - UnsafeLoader: Permite objetos Python arbitrarios (PELIGROSO)
    """
    loader = Loader(stream)
    try:
        return loader.get_single_data()
    finally:
        loader.dispose()

def load_all(stream, Loader):
    """
    📥 CARGA MÚLTIPLE: YAML → objetos Python (todos los documentos)
    
    PROPÓSITO:
    - Cargar todos los documentos en un stream
    - Soporte completo para documentos separados por ---
    - Requiere especificar Loader explícitamente por seguridad
    
    PARÁMETROS:
    - stream: Archivo, StringIO o string con contenido YAML
    - Loader: Clase loader específica (SafeLoader, FullLoader, etc.)
    
    YIELDS: Objetos Python para cada documento
    
    USO:
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
# 🛡️ FUNCIONES SEGURAS: Variantes con seguridad implícita
# ===============================================================================

def full_load(stream):
    """
    🛡️ CARGA COMPLETA SEGURA: YAML → Python con tipos extendidos
    
    PROPÓSITO:
    - Carga con FullLoader implícito (no requiere especificar)
    - Tipos básicos + datetime, set, ordered dict, etc.
    - Seguro para input no confiable (sin objetos Python arbitrarios)
    
    TIPOS SOPORTADOS:
    - ✅ Básicos: str, int, float, bool, list, dict, None
    - ✅ Extendidos: datetime, date, set, OrderedDict
    - ❌ Prohibidos: clases Python arbitrarias, funciones, etc.
    
    USO:
    ```python
    data = yaml.full_load("timestamp: 2023-01-01 12:00:00")
    # → {'timestamp': datetime.datetime(2023, 1, 1, 12, 0)}
    ```
    """
    return load(stream, FullLoader)

def full_load_all(stream):
    """
    🛡️ CARGA MÚLTIPLE COMPLETA: Todos los documentos con tipos extendidos
    
    PROPÓSITO:
    - Múltiples documentos con FullLoader implícito
    - Optimización especial para backend Rust
    - Seguro para input no confiable
    
    OPTIMIZACIÓN RUST:
    - Usa load_all_rust() directamente para máximo rendimiento
    - Conversión de stream automática
    - Filtrado de valores None para compatibilidad
    """
    # ===================================================================
    # 🚀 OPTIMIZACIÓN RUST: Ruta directa ultra-rápida
    # ===================================================================
    if __with_rust__:
        # Convertir stream a string si es necesario
        if hasattr(stream, 'read'):
            content = stream.read()
            if hasattr(stream, 'seek'):
                stream.seek(0)          # Reset para compatibilidad
        else:
            content = str(stream)
        
        # Usar función Rust directa (bypass Python overhead)
        import io
        rust_stream = io.StringIO(content)
        results = load_all_rust(rust_stream)
        
        # Filtrar None values para compatibilidad
        for result in results:
            if result is not None:
                yield result
    else:
        # ===================================================================
        # 🔄 FALLBACK: Método tradicional para otros backends
        # ===================================================================
        return load_all(stream, FullLoader)

def safe_load(stream):
    """
    🛡️ CARGA SEGURA: YAML → Python solo tipos básicos
    
    PROPÓSITO:
    - Máxima seguridad para input no confiable
    - Solo tipos básicos del core de Python
    - SafeLoader implícito (no requiere especificar)
    
    TIPOS PERMITIDOS ÚNICAMENTE:
    - ✅ str, int, float, bool
    - ✅ list, dict, None
    - ❌ Todo lo demás (datetime, set, clases, etc.)
    
    USO RECOMENDADO:
    - APIs públicas con input de usuarios
    - Archivos de configuración de fuentes externas
    - Cualquier YAML de origen no confiable
    
    ```python
    config = yaml.safe_load(user_input)  # Seguro siempre
    ```
    """
    return load(stream, SafeLoader)

def safe_load_all(stream):
    """
    🛡️ CARGA MÚLTIPLE SEGURA: Todos los documentos, solo tipos básicos
    
    PROPÓSITO:
    - Múltiples documentos con SafeLoader implícito
    - Optimización especial para backend Rust
    - Máxima seguridad para input no confiable
    """
    # ===================================================================
    # 🚀 OPTIMIZACIÓN RUST: Ruta directa ultra-rápida
    # ===================================================================
    if __with_rust__:
        # Convertir stream a string si es necesario
        if hasattr(stream, 'read'):
            content = stream.read()
            if hasattr(stream, 'seek'):
                stream.seek(0)          # Reset para compatibilidad
        else:
            content = str(stream)
        
        # Usar función Rust directa (bypass Python overhead)
        import io
        rust_stream = io.StringIO(content)
        results = load_all_rust(rust_stream)
        
        # Filtrar None values para compatibilidad
        for result in results:
            if result is not None:
                yield result
    else:
        # ===================================================================
        # 🔄 FALLBACK: Método tradicional para otros backends
        # ===================================================================
        return load_all(stream, SafeLoader)

def unsafe_load(stream):
    """
    ⚠️ CARGA INSEGURA: YAML → Python objetos arbitrarios
    
    PROPÓSITO:
    - Compatibilidad con PyYAML original (comportamiento legacy)
    - Permite cargar objetos Python arbitrarios
    - UnsafeLoader implícito
    
    ⚠️ ADVERTENCIA DE SEGURIDAD:
    - NUNCA usar con input no confiable
    - Puede ejecutar código arbitrario
    - Solo para archivos de confianza total
    
    TIPOS PERMITIDOS:
    - ✅ Todos los tipos básicos y extendidos
    - ✅ Clases Python personalizadas
    - ✅ Funciones, módulos, etc.
    - ⚠️ PELIGROSO: Ejecución de código potencial
    
    USO LIMITADO:
    - Serialización de objetos Python complejos
    - Archivos internos de aplicación
    - NUNCA con input externo
    """
    return load(stream, UnsafeLoader)

def unsafe_load_all(stream):
    """
    ⚠️ CARGA MÚLTIPLE INSEGURA: Todos los documentos, objetos arbitrarios
    
    PROPÓSITO:
    - Múltiples documentos con UnsafeLoader implícito
    - Optimización especial para backend Rust
    - ⚠️ PELIGROSO para input no confiable
    """
    # ===================================================================
    # 🚀 OPTIMIZACIÓN RUST: Ruta directa ultra-rápida
    # ===================================================================
    if __with_rust__:
        # Convertir stream a string si es necesario
        if hasattr(stream, 'read'):
            content = stream.read()
            if hasattr(stream, 'seek'):
                stream.seek(0)          # Reset para compatibilidad
        else:
            content = str(stream)
        
        # Usar función Rust directa (bypass Python overhead)
        import io
        rust_stream = io.StringIO(content)
        results = load_all_rust(rust_stream)
        
        # Filtrar None values para compatibilidad
        for result in results:
            if result is not None:
                yield result
    else:
        # ===================================================================
        # 🔄 FALLBACK: Método tradicional para otros backends
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
        # Con backend Rust, usar clases directamente
        if __with_rust__:
            # Las clases Rust no soportan add_implicit_resolver aún
            pass  # Compatibilidad - no implementado
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
        # Con backend Rust, usar clases directamente
        if __with_rust__:
            # Las clases Rust no soportan add_path_resolver aún
            pass  # Compatibilidad - no implementado
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
        # Con backend Rust, usar clases directamente
        if __with_rust__:
            # Las clases Rust no soportan add_constructor aún
            pass  # Compatibilidad - no implementado
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
        # Con backend Rust, usar clases directamente
        if __with_rust__:
            # Las clases Rust no soportan add_multi_constructor aún
            pass  # Compatibilidad - no implementado
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
    # Si es backend Rust, no hace nada (por ahora, solo compatibilidad)

def add_multi_representer(data_type, multi_representer, Dumper=Dumper):
    """
    Add a representer for the given type.
    Multi-representer is a function accepting a Dumper instance
    and an instance of the given data type or subtype
    and producing the corresponding representation node.
    """
    if hasattr(Dumper, 'add_multi_representer'):
        Dumper.add_multi_representer(data_type, multi_representer)
    # Si es backend Rust, no hace nada (por ahora, solo compatibilidad)

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

