
__all__ = ['BaseRepresenter', 'SafeRepresenter', 'Representer',
    'RepresenterError']

from error import *
from nodes import *
from detector import *

try:
    import datetime
    datetime_available = True
except ImportError:
    datetime_available = False

try:
    set
except NameError:
    from sets import Set as set

class RepresenterError(YAMLError):
    pass

class BaseRepresenter(BaseDetector):

    DEFAULT_SCALAR_TAG = u'tag:yaml.org,2002:str'
    DEFAULT_SEQUENCE_TAG = u'tag:yaml.org,2002:seq'
    DEFAULT_MAPPING_TAG = u'tag:yaml.org,2002:map'

    def __init__(self, serializer):
        self.serializer = serializer
        self.represented_objects = {}

    def close(self):
        self.serializer.close()

    def represent(self, native):
        node = self.represent_object(native)
        self.serializer.serialize(node)
        self.represented_objects = {}

    def represent_object(self, native):
        if self.ignore_aliases(native):
            alias_key = None
        else:
            alias_key = id(native)
        if alias_key is not None:
            if alias_key in self.represented_objects:
                node = self.represented_objects[alias_key]
                if node is None:
                    raise RepresenterError("recursive objects are not allowed: %r" % native)
                return node
            self.represented_objects[alias_key] = None
        for native_type in type(native).__mro__:
            if native_type in self.yaml_representers:
                node = self.yaml_representers[native_type](self, native)
                break
        else:
            if None in self.yaml_representers:
                node = self.yaml_representers[None](self, native)
            else:
                node = ScalarNode(None, unicode(native))
        if alias_key is not None:
            self.represented_objects[alias_key] = node
        return node

    def add_representer(cls, native_type, representer):
        if not 'yaml_representers' in cls.__dict__:
            cls.yaml_representers = cls.yaml_representers.copy()
        cls.yaml_representers[native_type] = representer
    add_representer = classmethod(add_representer)

    yaml_representers = {}

    def represent_scalar(self, tag, value, style=None):
        detected_tag = self.detect(value)
        if detected_tag is None:
            detected_tag = self.DEFAULT_SCALAR_TAG
        implicit = (tag == detected_tag)
        if tag == self.DEFAULT_SCALAR_TAG:
            tag = None
        return ScalarNode(tag, value, implicit=implicit, style=style)

    def represent_sequence(self, tag, sequence, flow_style=None):
        if tag == self.DEFAULT_SEQUENCE_TAG:
            tag = None
        value = []
        for item in sequence:
            value.append(self.represent_object(item))
        return SequenceNode(tag, value, flow_style=flow_style)

    def represent_mapping(self, tag, mapping, flow_style=None):
        if tag == self.DEFAULT_MAPPING_TAG:
            tag = None
        value = {}
        if hasattr(mapping, 'keys'):
            for item_key in mapping.keys():
                item_value = mapping[item_key]
                value[self.represent_object(item_key)] =    \
                        self.represent_object(item_value)
        else:
            for item_key, item_value in mapping:
                value[self.represent_object(item_key)] =    \
                        self.represent_object(item_value)
        return MappingNode(tag, value, flow_style=flow_style)

    def ignore_aliases(self, native):
        return False

class SafeRepresenter(Detector, BaseRepresenter):

    def ignore_aliases(self, native):
        if native in [None, ()]:
            return True
        if isinstance(native, (str, unicode, bool, int, float)):
            return True

    def represent_none(self, native):
        return self.represent_scalar(u'tag:yaml.org,2002:null',
                u'null')

    def represent_str(self, native):
        encoding = None
        try:
            unicode(native, 'ascii')
            encoding = 'ascii'
        except UnicodeDecodeError:
            try:
                unicode(native, 'utf-8')
                encoding = 'utf-8'
            except UnicodeDecodeError:
                pass
        if encoding:
            return self.represent_scalar(u'tag:yaml.org,2002:str',
                    unicode(native, encoding))
        else:
            return self.represent_scalar(u'tag:yaml.org,2002:binary',
                    unicode(native.encode('base64')), style='|')

    def represent_unicode(self, native):
        return self.represent_scalar(u'tag:yaml.org,2002:str', native)

    def represent_bool(self, native):
        if native:
            value = u'true'
        else:
            value = u'false'
        return self.represent_scalar(u'tag:yaml.org,2002:bool', value)

    def represent_int(self, native):
        return self.represent_scalar(u'tag:yaml.org,2002:int', unicode(native))

    def represent_long(self, native):
        return self.represent_scalar(u'tag:yaml.org,2002:int', unicode(native))

    inf_value = 1e300000
    nan_value = inf_value/inf_value

    def represent_float(self, native):
        if native == self.inf_value:
            value = u'.inf'
        elif native == -self.inf_value:
            value = u'-.inf'
        elif native == self.nan_value or native != native:
            value = u'.nan'
        else:
            value = unicode(native)
        return self.represent_scalar(u'tag:yaml.org,2002:float', value)

    def represent_list(self, native):
        pairs = (len(native) > 0)
        for item in native:
            if not isinstance(item, tuple) or len(item) != 2:
                pairs = False
                break
        if not pairs:
            return self.represent_sequence(u'tag:yaml.org,2002:seq', native)
        value = []
        for item_key, item_value in native:
            value.append(self.represent_mapping(u'tag:yaml.org,2002:map',
                [(item_key, item_value)]))
        return SequenceNode(u'tag:yaml.org,2002:pairs', value)

    def represent_dict(self, native):
        return self.represent_mapping(u'tag:yaml.org,2002:map', native)

    def represent_set(self, native):
        value = {}
        for key in native:
            value[key] = None
        return self.represent_mapping(u'tag:yaml.org,2002:set', value)

    def represent_date(self, native):
        value = u'%04d-%02d-%02d' % (native.year, native.month, native.day)
        return self.represent_scalar(u'tag:yaml.org,2002:timestamp', value)

    def represent_datetime(self, native):
        value = u'%04d-%02d-%02d %02d:%02d:%02d' \
                % (native.year, native.month, native.day,
                    native.hour, native.minute, native.second)
        if native.microsecond:
            value += u'.' + unicode(native.microsecond/1000000.0).split(u'.')[1]
        if native.utcoffset():
            value += unicode(native.utcoffset())
        return self.represent_scalar(u'tag:yaml.org,2002:timestamp', value)

    def represent_undefined(self, native):
        raise RepresenterError("cannot represent an object: %s" % native)

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
    pass

