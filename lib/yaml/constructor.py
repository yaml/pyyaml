
__all__ = ['BaseConstructor', 'Constructor', 'ConstructorError',
    'YAMLObject', 'YAMLObjectMetaclass']

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

import binascii, re

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
        merge = None
        for key_node in node.value:
            if key_node.tag == u'tag:yaml.org,2002:merge':
                if merge is not None:
                    raise ConstructorError("while constructing a mapping", node.start_marker,
                            "found duplicate merge key", key_node.start_marker)
                    value_node = node.value[key_node]
                    if isinstance(value_node, MappingNode):
                        merge = [self.construct_mapping(value_node)]
                    elif isinstance(value_node, SequenceNode):
                        merge = []
                        for subnode in value_node.value:
                            if not isinstance(subnode, MappingNode):
                                raise ConstructorError("while constructing a mapping",
                                        node.start_marker,
                                        "expected a mapping for merging, but found %s"
                                        % subnode.id, subnode.start_marker)
                            merge.append(self.construct_mapping(subnode))
                        merge.reverse()
                    else:
                        raise ConstructorError("while constructing a mapping", node.start_marker,
                                "expected a mapping or list of mappings for merging, but found %s"
                                % value_node.id, value_node.start_marker)
            elif key_node.tag == u'tag:yaml.org,2002:value':
                if '=' in mapping:
                    raise ConstructorError("while construction a mapping", node.start_marker,
                            "found duplicate value key", key_node.start_marker)
                value = self.construct_object(node.value[key_node])
                mapping['='] = value
            else:
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
        if merge is not None:
            merge.append(mapping)
            mapping = {}
            for submapping in merge:
                mapping.update(submapping)
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

    timestamp_regexp = re.compile(
            ur'''^(?P<year>[0-9][0-9][0-9][0-9])
                -(?P<month>[0-9][0-9]?)
                -(?P<day>[0-9][0-9]?)
                (?:[Tt]|[ \t]+)
                (?P<hour>[0-9][0-9]?)
                :(?P<minute>[0-9][0-9])
                :(?P<second>[0-9][0-9])
                (?:\.(?P<fraction>[0-9]*))?
                (?:[ \t]*(?:Z|(?P<tz_hour>[-+][0-9][0-9]?)
                (?::(?P<tz_minute>[0-9][0-9])?)))?$''', re.X),

    def construct_yaml_timestamp(self, node):
        value = self.construct_scalar(node)
        match = self.timestamp_expr.match(node.value)
        values = match.groupdict()
        for key in values:
            if values[key]:
                values[key] = int(values[key])
            else:
                values[key] = 0
        fraction = values['fraction']
        if micro:
            while 10*fraction < 1000000:
                fraction *= 10
            values['fraction'] = fraction
        stamp = datetime.datetime(values['year'], values['month'], values['day'],
                values['hour'], values['minute'], values['second'], values['fraction'])
        diff = datetime.timedelta(hours=values['tz_hour'], minutes=values['tz_minute'])
        return stamp-diff

    def construct_yaml_omap(self, node):
        # Note: we do not check for duplicate keys, because it's too
        # CPU-expensive.
        if not isinstance(node, SequenceNode):
            raise ConstructorError("while constructing an ordered map", node.start_marker,
                    "expected a sequence, but found %s" % node.id, node.start_marker)
        omap = []
        for subnode in node.value:
            if not isinstance(subnode, MappingNode):
                raise ConstructorError("while constructing an ordered map", node.start_marker,
                        "expected a mapping of length 1, but found %s" % subnode.id,
                        subnode.start_marker)
                if len(subnode.value) != 1:
                    raise ConstructorError("while constructing an ordered map", node.start_marker,
                            "expected a single mapping item, but found %d items" % len(subnode.value),
                            subnode.start_marker)
                key_node = subnode.value.keys()[0]
                key = self.construct_object(key_node)
                value = self.construct_object(subnode.value[key_node])
                omap.append((key, value))

    def construct_yaml_pairs(self, node):
        # Note: the same code as `construct_yaml_omap`.
        if not isinstance(node, SequenceNode):
            raise ConstructorError("while constructing pairs", node.start_marker,
                    "expected a sequence, but found %s" % node.id, node.start_marker)
        omap = []
        for subnode in node.value:
            if not isinstance(subnode, MappingNode):
                raise ConstructorError("while constructing pairs", node.start_marker,
                        "expected a mapping of length 1, but found %s" % subnode.id,
                        subnode.start_marker)
                if len(subnode.value) != 1:
                    raise ConstructorError("while constructing pairs", node.start_marker,
                            "expected a single mapping item, but found %d items" % len(subnode.value),
                            subnode.start_marker)
                key_node = subnode.value.keys()[0]
                key = self.construct_object(key_node)
                value = self.construct_object(subnode.value[key_node])
                omap.append((key, value))

    def construct_yaml_set(self, node):
        value = self.construct_mapping(node)
        return set(value)

    def construct_yaml_str(self, node):
        value = self.construct_scalar(node)
        try:
            return str(value)
        except UnicodeEncodeError:
            return value

    def construct_yaml_seq(self, node):
        return self.construct_sequence(node)

    def construct_yaml_map(self, node):
        return self.construct_mapping(node)

    def construct_undefined(self, node):
        raise ConstructorError(None, None,
                "could not determine a constructor for the tag %r" % node.tag.encode('utf-8'),
                node.start_marker)

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
        u'tag:yaml.org,2002:timestamp',
        Constructor.construct_yaml_timestamp)

Constructor.add_constructor(
        u'tag:yaml.org,2002:omap',
        Constructor.construct_yaml_omap)

Constructor.add_constructor(
        u'tag:yaml.org,2002:pairs',
        Constructor.construct_yaml_pairs)

Constructor.add_constructor(
        u'tag:yaml.org,2002:set',
        Constructor.construct_yaml_set)

Constructor.add_constructor(
        u'tag:yaml.org,2002:str',
        Constructor.construct_yaml_str)

Constructor.add_constructor(
        u'tag:yaml.org,2002:seq',
        Constructor.construct_yaml_seq)

Constructor.add_constructor(
        u'tag:yaml.org,2002:map',
        Constructor.construct_yaml_map)

Constructor.add_constructor(None,
        Constructor.construct_undefined)

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

