
__all__ = ['BaseConstructor', 'SafeConstructor', 'Constructor',
    'ConstructorError']

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
                    node.start_mark)
        return node.value

    def construct_sequence(self, node):
        if not isinstance(node, SequenceNode):
            raise ConstructorError(None, None,
                    "expected a sequence node, but found %s" % node.id,
                    node.start_mark)
        return [self.construct_object(child) for child in node.value]

    def construct_mapping(self, node):
        if not isinstance(node, MappingNode):
            raise ConstructorError(None, None,
                    "expected a mapping node, but found %s" % node.id,
                    node.start_mark)
        mapping = {}
        merge = None
        for key_node in node.value:
            if key_node.tag == u'tag:yaml.org,2002:merge':
                if merge is not None:
                    raise ConstructorError("while constructing a mapping", node.start_mark,
                            "found duplicate merge key", key_node.start_mark)
                value_node = node.value[key_node]
                if isinstance(value_node, MappingNode):
                    merge = [self.construct_mapping(value_node)]
                elif isinstance(value_node, SequenceNode):
                    merge = []
                    for subnode in value_node.value:
                        if not isinstance(subnode, MappingNode):
                            raise ConstructorError("while constructing a mapping",
                                    node.start_mark,
                                    "expected a mapping for merging, but found %s"
                                    % subnode.id, subnode.start_mark)
                        merge.append(self.construct_mapping(subnode))
                    merge.reverse()
                else:
                    raise ConstructorError("while constructing a mapping", node.start_mark,
                            "expected a mapping or list of mappings for merging, but found %s"
                            % value_node.id, value_node.start_mark)
            elif key_node.tag == u'tag:yaml.org,2002:value':
                if '=' in mapping:
                    raise ConstructorError("while construction a mapping", node.start_mark,
                            "found duplicate value key", key_node.start_mark)
                value = self.construct_object(node.value[key_node])
                mapping['='] = value
            else:
                key = self.construct_object(key_node)
                try:
                    duplicate_key = key in mapping
                except TypeError, exc:
                    raise ConstructorError("while constructing a mapping", node.start_mark,
                            "found unacceptable key (%s)" % exc, key_node.start_mark)
                if duplicate_key:
                    raise ConstructorError("while constructing a mapping", node.start_mark,
                            "found duplicate key", key_node.start_mark)
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
                    node.start_mark)
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

class SafeConstructor(BaseConstructor):

    def construct_yaml_null(self, node):
        self.construct_scalar(node)
        return None

    bool_values = {
        u'yes':     True,
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
            sign = -1
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
                (?:(?:[Tt]|[ \t]+)
                (?P<hour>[0-9][0-9]?)
                :(?P<minute>[0-9][0-9])
                :(?P<second>[0-9][0-9])
                (?:\.(?P<fraction>[0-9]*))?
                (?:[ \t]*(?:Z|(?P<tz_hour>[-+][0-9][0-9]?)
                (?::(?P<tz_minute>[0-9][0-9])?)?))?)?$''', re.X)

    def construct_yaml_timestamp(self, node):
        value = self.construct_scalar(node)
        match = self.timestamp_regexp.match(node.value)
        values = match.groupdict()
        for key in values:
            if values[key]:
                values[key] = int(values[key])
            else:
                values[key] = 0
        fraction = values['fraction']
        if fraction:
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
            raise ConstructorError("while constructing an ordered map", node.start_mark,
                    "expected a sequence, but found %s" % node.id, node.start_mark)
        omap = []
        for subnode in node.value:
            if not isinstance(subnode, MappingNode):
                raise ConstructorError("while constructing an ordered map", node.start_mark,
                        "expected a mapping of length 1, but found %s" % subnode.id,
                        subnode.start_mark)
            if len(subnode.value) != 1:
                raise ConstructorError("while constructing an ordered map", node.start_mark,
                        "expected a single mapping item, but found %d items" % len(subnode.value),
                        subnode.start_mark)
            key_node = subnode.value.keys()[0]
            key = self.construct_object(key_node)
            value = self.construct_object(subnode.value[key_node])
            omap.append((key, value))
        return omap

    def construct_yaml_pairs(self, node):
        # Note: the same code as `construct_yaml_omap`.
        if not isinstance(node, SequenceNode):
            raise ConstructorError("while constructing pairs", node.start_mark,
                    "expected a sequence, but found %s" % node.id, node.start_mark)
        pairs = []
        for subnode in node.value:
            if not isinstance(subnode, MappingNode):
                raise ConstructorError("while constructing pairs", node.start_mark,
                        "expected a mapping of length 1, but found %s" % subnode.id,
                        subnode.start_mark)
            if len(subnode.value) != 1:
                raise ConstructorError("while constructing pairs", node.start_mark,
                        "expected a single mapping item, but found %d items" % len(subnode.value),
                        subnode.start_mark)
            key_node = subnode.value.keys()[0]
            key = self.construct_object(key_node)
            value = self.construct_object(subnode.value[key_node])
            pairs.append((key, value))
        return pairs

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
                node.start_mark)

SafeConstructor.add_constructor(
        u'tag:yaml.org,2002:null',
        SafeConstructor.construct_yaml_null)

SafeConstructor.add_constructor(
        u'tag:yaml.org,2002:bool',
        SafeConstructor.construct_yaml_bool)

SafeConstructor.add_constructor(
        u'tag:yaml.org,2002:int',
        SafeConstructor.construct_yaml_int)

SafeConstructor.add_constructor(
        u'tag:yaml.org,2002:float',
        SafeConstructor.construct_yaml_float)

SafeConstructor.add_constructor(
        u'tag:yaml.org,2002:binary',
        SafeConstructor.construct_yaml_binary)

if datetime_available:
    SafeConstructor.add_constructor(
            u'tag:yaml.org,2002:timestamp',
            SafeConstructor.construct_yaml_timestamp)

SafeConstructor.add_constructor(
        u'tag:yaml.org,2002:omap',
        SafeConstructor.construct_yaml_omap)

SafeConstructor.add_constructor(
        u'tag:yaml.org,2002:pairs',
        SafeConstructor.construct_yaml_pairs)

SafeConstructor.add_constructor(
        u'tag:yaml.org,2002:set',
        SafeConstructor.construct_yaml_set)

SafeConstructor.add_constructor(
        u'tag:yaml.org,2002:str',
        SafeConstructor.construct_yaml_str)

SafeConstructor.add_constructor(
        u'tag:yaml.org,2002:seq',
        SafeConstructor.construct_yaml_seq)

SafeConstructor.add_constructor(
        u'tag:yaml.org,2002:map',
        SafeConstructor.construct_yaml_map)

SafeConstructor.add_constructor(None,
        SafeConstructor.construct_undefined)

class Constructor(SafeConstructor):
    pass

