
__all__ = ['BaseRepresenter', 'SafeRepresenter', 'Representer',
    'RepresenterError']

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

import sys

class RepresenterError(YAMLError):
    pass

class BaseRepresenter:

    yaml_representers = {}

    def __init__(self):
        self.represented_objects = {}

    def represent(self, data):
        node = self.represent_object(data)
        self.serialize(node)
        self.represented_objects = {}

    class C: pass
    c = C()
    def f(): pass
    classobj_type = type(C)
    instance_type = type(c)
    function_type = type(f)
    builtin_function_type = type(abs)
    module_type = type(sys)
    del C, c, f

    def get_classobj_bases(self, cls):
        bases = [cls]
        for base in cls.__bases__:
            bases.extend(self.get_classobj_bases(base))
        return bases

    def represent_object(self, data):
        if self.ignore_aliases(data):
            alias_key = None
        else:
            alias_key = id(data)
        if alias_key is not None:
            if alias_key in self.represented_objects:
                node = self.represented_objects[alias_key]
                if node is None:
                    raise RepresenterError("recursive objects are not allowed: %r" % data)
                return node
            self.represented_objects[alias_key] = None
        data_types = type(data).__mro__
        if type(data) is self.instance_type:
            data_types = self.get_classobj_bases(data.__class__)+data_types
        for data_type in data_types:
            if data_type in self.yaml_representers:
                node = self.yaml_representers[data_type](self, data)
                break
        else:
            if None in self.yaml_representers:
                node = self.yaml_representers[None](self, data)
            else:
                node = ScalarNode(None, unicode(data))
        if alias_key is not None:
            self.represented_objects[alias_key] = node
        return node

    def add_representer(cls, data_type, representer):
        if not 'yaml_representers' in cls.__dict__:
            cls.yaml_representers = cls.yaml_representers.copy()
        cls.yaml_representers[data_type] = representer
    add_representer = classmethod(add_representer)

    def represent_scalar(self, tag, value, style=None):
        return ScalarNode(tag, value, style=style)

    def represent_sequence(self, tag, sequence, flow_style=None):
        value = []
        for item in sequence:
            value.append(self.represent_object(item))
        return SequenceNode(tag, value, flow_style=flow_style)

    def represent_mapping(self, tag, mapping, flow_style=None):
        if hasattr(mapping, 'keys'):
            value = {}
            for item_key in mapping.keys():
                item_value = mapping[item_key]
                value[self.represent_object(item_key)] =    \
                        self.represent_object(item_value)
        else:
            value = []
            for item_key, item_value in mapping:
                value.append((self.represent_object(item_key),
                        self.represent_object(item_value)))
        return MappingNode(tag, value, flow_style=flow_style)

    def ignore_aliases(self, data):
        return False

class SafeRepresenter(BaseRepresenter):

    def ignore_aliases(self, data):
        if data in [None, ()]:
            return True
        if isinstance(data, (str, unicode, bool, int, float)):
            return True

    def represent_none(self, data):
        return self.represent_scalar(u'tag:yaml.org,2002:null',
                u'null')

    def represent_str(self, data):
        tag = None
        style = None
        try:
            data = unicode(data, 'ascii')
            tag = u'tag:yaml.org,2002:str'
        except UnicodeDecodeError:
            try:
                data = unicode(data, 'utf-8')
                tag = u'tag:yaml.org,2002:str'
            except UnicodeDecodeError:
                data = data.encode('base64')
                tag = u'tag:yaml.org,2002:binary'
                style = '|'
        return self.represent_scalar(tag, data, style=style)

    def represent_unicode(self, data):
        return self.represent_scalar(u'tag:yaml.org,2002:str', data)

    def represent_bool(self, data):
        if data:
            value = u'true'
        else:
            value = u'false'
        return self.represent_scalar(u'tag:yaml.org,2002:bool', value)

    def represent_int(self, data):
        return self.represent_scalar(u'tag:yaml.org,2002:int', unicode(data))

    def represent_long(self, data):
        return self.represent_scalar(u'tag:yaml.org,2002:int', unicode(data))

    inf_value = 1e300000
    nan_value = inf_value/inf_value

    def represent_float(self, data):
        if data == self.inf_value:
            value = u'.inf'
        elif data == -self.inf_value:
            value = u'-.inf'
        elif data == self.nan_value or data != data:
            value = u'.nan'
        else:
            value = unicode(repr(data))
        return self.represent_scalar(u'tag:yaml.org,2002:float', value)

    def represent_list(self, data):
        pairs = (len(data) > 0 and isinstance(data, list))
        if pairs:
            for item in data:
                if not isinstance(item, tuple) or len(item) != 2:
                    pairs = False
                    break
        if not pairs:
            return self.represent_sequence(u'tag:yaml.org,2002:seq', data)
        value = []
        for item_key, item_value in data:
            value.append(self.represent_mapping(u'tag:yaml.org,2002:map',
                [(item_key, item_value)]))
        return SequenceNode(u'tag:yaml.org,2002:pairs', value)

    def represent_dict(self, data):
        return self.represent_mapping(u'tag:yaml.org,2002:map', data)

    def represent_set(self, data):
        value = {}
        for key in data:
            value[key] = None
        return self.represent_mapping(u'tag:yaml.org,2002:set', value)

    def represent_date(self, data):
        value = u'%04d-%02d-%02d' % (data.year, data.month, data.day)
        return self.represent_scalar(u'tag:yaml.org,2002:timestamp', value)

    def represent_datetime(self, data):
        value = u'%04d-%02d-%02d %02d:%02d:%02d' \
                % (data.year, data.month, data.day,
                    data.hour, data.minute, data.second)
        if data.microsecond:
            value += u'.' + unicode(data.microsecond/1000000.0).split(u'.')[1]
        if data.utcoffset():
            value += unicode(data.utcoffset())
        return self.represent_scalar(u'tag:yaml.org,2002:timestamp', value)

    def represent_yaml_object(self, tag, data, cls, flow_style=None):
        if hasattr(data, '__getstate__'):
            state = data.__getstate__()
        else:
            state = data.__dict__.copy()
        return self.represent_mapping(tag, state, flow_style=flow_style)

    def represent_undefined(self, data):
        raise RepresenterError("cannot represent an object: %s" % data)

SafeRepresenter.add_representer(type(None),
        SafeRepresenter.represent_none)

SafeRepresenter.add_representer(str,
        SafeRepresenter.represent_str)

SafeRepresenter.add_representer(unicode,
        SafeRepresenter.represent_unicode)

SafeRepresenter.add_representer(bool,
        SafeRepresenter.represent_bool)

SafeRepresenter.add_representer(int,
        SafeRepresenter.represent_int)

SafeRepresenter.add_representer(long,
        SafeRepresenter.represent_long)

SafeRepresenter.add_representer(float,
        SafeRepresenter.represent_float)

SafeRepresenter.add_representer(list,
        SafeRepresenter.represent_list)

SafeRepresenter.add_representer(tuple,
        SafeRepresenter.represent_list)

SafeRepresenter.add_representer(dict,
        SafeRepresenter.represent_dict)

SafeRepresenter.add_representer(set,
        SafeRepresenter.represent_set)

if datetime_available:
    SafeRepresenter.add_representer(datetime.date,
            SafeRepresenter.represent_date)
    SafeRepresenter.add_representer(datetime.datetime,
            SafeRepresenter.represent_datetime)

SafeRepresenter.add_representer(None,
        SafeRepresenter.represent_undefined)

class Representer(SafeRepresenter):
    
    def represent_str(self, data):
        tag = None
        style = None
        try:
            data = unicode(data, 'ascii')
            tag = u'tag:yaml.org,2002:str'
        except UnicodeDecodeError:
            try:
                data = unicode(data, 'utf-8')
                tag = u'tag:yaml.org,2002:python/str'
            except UnicodeDecodeError:
                data = data.encode('base64')
                tag = u'tag:yaml.org,2002:binary'
                style = '|'
        return self.represent_scalar(tag, data, style=style)

    def represent_unicode(self, data):
        tag = None
        try:
            data.encode('ascii')
            tag = u'tag:yaml.org,2002:python/unicode'
        except UnicodeEncodeError:
            tag = u'tag:yaml.org,2002:str'
        return self.represent_scalar(tag, data)

    def represent_long(self, data):
        tag = u'tag:yaml.org,2002:int'
        if int(data) is not data:
            tag = u'tag:yaml.org,2002:python/long'
        return self.represent_scalar(tag, unicode(data))

    def represent_complex(self, data):
        if data.real != 0.0:
            data = u'%r+%rj' % (data.real, data.imag)
        else:
            data = u'%rj' % data.imag
        return self.represent_scalar(u'tag:yaml.org,2002:python/complex', data)

    def represent_tuple(self, data):
        return self.represent_sequence(u'tag:yaml.org,2002:python/tuple', data)

    def represent_name(self, data):
        name = u'%s.%s' % (data.__module__, data.__name__)
        return self.represent_scalar(u'tag:yaml.org,2002:python/name:'+name, u'')

    def represent_module(self, data):
        return self.represent_scalar(
                u'tag:yaml.org,2002:python/module:'+data.__name__, u'')

Representer.add_representer(str,
        Representer.represent_str)

Representer.add_representer(unicode,
        Representer.represent_unicode)

Representer.add_representer(long,
        Representer.represent_long)

Representer.add_representer(complex,
        Representer.represent_complex)

Representer.add_representer(tuple,
        Representer.represent_tuple)

Representer.add_representer(type,
        Representer.represent_name)

Representer.add_representer(Representer.classobj_type,
        Representer.represent_name)

Representer.add_representer(Representer.function_type,
        Representer.represent_name)

Representer.add_representer(Representer.builtin_function_type,
        Representer.represent_name)

Representer.add_representer(Representer.module_type,
        Representer.represent_module)

