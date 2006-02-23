
from error import *
from nodes import *

try:
    import datetime
    datetime_available = True
except ImportError:
    datetime_available = False

try:
    set
except NameError:
    from sets import Set as set

import binascii

class ConstructorError(MarkedYAMLError):
    pass

class BaseConstructor:

    def __init__(self, resolver):
        self.resolver = resolver
        self.constructed_objects = {}

    def check(self):
        # If there are more documents available?
        return self.resolver.check()

    def get(self):
        # Construct and return the next document.
        if self.resolver.check():
            return self.construct_document(self.resolver.get())

    def __iter__(self):
        # Iterator protocol.
        while self.resolver.check():
            yield self.construct_document(self.resolver.get())

    def construct_document(self, node):
        native = self.construct_object(node)
        self.constructed_objects = {}
        return native

    def construct_object(self, node):
        if node in self.constructed_objects:
            return self.constructed_objects[node]
        if node.tag in self.yaml_constructors:
            native = self.yaml_constructors[node.tag](self, node)
        elif None in self.yaml_constructors:
            native = self.yaml_constructors[None](self, node)
        elif isinstance(node, ScalarNode):
            native = self.construct_scalar(node)
        elif isinstance(node, SequenceNode):
            native = self.construct_sequence(node)
        elif isinstance(node, MappingNode):
            native = self.construct_mapping(node)
        self.constructed_objects[node] = native
        return native

    def construct_scalar(self, node):
        if not isinstance(node, ScalarNode):
            if isinstance(node, MappingNode):
                for key_node in node.value:
                    if key_node.tag == u'tag:yaml.org,2002:value':
                        return self.construct_scalar(node.value[key_node])
            raise ConstructorError(None, None,
                    "expected a scalar node, but found %s" % node.id,
                    node.start_marker)
        return node.value

    def construct_sequence(self, node):
        if not isinstance(node, SequenceNode):
            raise ConstructorError(None, None,
                    "expected a sequence node, but found %s" % node.id,
                    node.start_marker)
        return [self.construct_object(child) for child in node.value]

    def construct_mapping(self, node):
        if not isinstance(node, MappingNode):
            raise ConstructorError(None, None,
                    "expected a mapping node, but found %s" % node.id,
                    node.start_marker)
        mapping = {}
        for key_node in node.value:
            key = self.construct_object(key_node)
            try:
                duplicate_key = key in mapping
            except TypeError, exc:
                raise ConstructorError("while constructing a mapping", node.start_marker,
                        "found unacceptable key (%s)" % exc, key_node.start_marker)
            if duplicate_key:
                raise ConstructorError("while constructing a mapping", node.start_marker,
                        "found duplicate key", key_node.start_marker)
            value = self.construct_object(node.value[key_node])
            mapping[key] = value
        return mapping

    def construct_pairs(self, node):
        if not isinstance(node, MappingNode):
            raise ConstructorError(None, None,
                    "expected a mapping node, but found %s" % node.id,
                    node.start_marker)
        pairs = []
        for key_node in node.value:
            key = self.construct_object(key_node)
            value = self.construct_object(node.value[key_node])
            pairs.append((key, value))
        return pairs

    def add_constructor(cls, tag, constructor):
        if not 'yaml_constructors' in cls.__dict__:
            cls.yaml_constructors = cls.yaml_constructors.copy()
        cls.yaml_constructors[tag] = constructor
    add_constructor = classmethod(add_constructor)

    yaml_constructors = {}

class Constructor(BaseConstructor):

    def construct_yaml_null(self, node):
        self.construct_scalar(node)
        return None

    bool_values = {
        u'y':       True,
        u'yes':     True,
        u'n':       False,
        u'no':      False,
        u'true':    True,
        u'false':   False,
        u'on':      True,
        u'off':     False,
    }

    def construct_yaml_bool(self, node):
        value = self.construct_scalar(node)
        return self.bool_values[value.lower()]

    def construct_yaml_int(self, node):
        value = str(self.construct_scalar(node))
        value = value.replace('_', '')
        sign = +1
        if value[0] == '-':
            sign = -1
        if value[0] in '+-':
            value = value[1:]
        if value == '0':
            return 0
        elif value.startswith('0b'):
            return sign*int(value[2:], 2)
        elif value.startswith('0x'):
            return sign*int(value[2:], 16)
        elif value[0] == '0':
            return sign*int(value, 8)
        elif ':' in value:
            digits = [int(part) for part in value.split(':')]
            digits.reverse()
            base = 1
            value = 0
            for digit in digits:
                value += digit*base
                base *= 60
            return sign*value
        else:
            return sign*int(value)

    inf_value = 1e300000
    nan_value = inf_value/inf_value

    def construct_yaml_float(self, node):
        value = str(self.construct_scalar(node))
        value = value.replace('_', '')
        sign = +1
        if value[0] == '-':
            value = -1
        if value[0] in '+-':
            value = value[1:]
        if value.lower() == '.inf':
            return sign*self.inf_value
        elif value.lower() == '.nan':
            return self.nan_value
        elif ':' in value:
            digits = [float(part) for part in value.split(':')]
            digits.reverse()
            base = 1
            value = 0.0
            for digit in digits:
                value += digit*base
                base *= 60
            return sign*value
        else:
            return float(value)

    def construct_yaml_binary(self, node):
        value = self.construct_scalar(node)
        try:
            return str(value).decode('base64')
        except (binascii.Error, UnicodeEncodeError), exc:
            raise ConstructorError(None, None,
                    "failed to decode base64 data: %s" % exc, node.start_mark) 

    def construct_yaml_str(self, node):
        value = self.construct_scalar(node)
        try:
            return str(value)
        except UnicodeEncodeError:
            return value

Constructor.add_constructor(
        u'tag:yaml.org,2002:null',
        Constructor.construct_yaml_null)

Constructor.add_constructor(
        u'tag:yaml.org,2002:bool',
        Constructor.construct_yaml_bool)

Constructor.add_constructor(
        u'tag:yaml.org,2002:int',
        Constructor.construct_yaml_int)

Constructor.add_constructor(
        u'tag:yaml.org,2002:float',
        Constructor.construct_yaml_float)

Constructor.add_constructor(
        u'tag:yaml.org,2002:str',
        Constructor.construct_yaml_str)

class YAMLObjectMetaclass(type):

    def __init__(cls, name, bases, kwds):
        super(YAMLObjectMetaclass, cls).__init__(name, bases, kwds)
        if 'yaml_tag' in kwds and kwds['yaml_tag'] is not None:
            cls.yaml_constructor_class.add_constructor(cls.yaml_tag, cls.from_yaml)

class YAMLObject(object):

    __metaclass__ = YAMLObjectMetaclass

    yaml_constructor_class = Constructor

    yaml_tag = None

    def from_yaml(cls, constructor, node):
        raise ConstructorError(None, None,
                "found undefined constructor for the tag %r"
                % node.tag.encode('utf-8'), node.start_marker)
    from_yaml = classmethod(from_yaml)

    def to_yaml(self):
        assert False    # needs dumper

