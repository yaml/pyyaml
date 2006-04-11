
__all__ = ['YAMLObject', 'YAMLObjectMetaclass']

from constructor import *
from representer import *

class YAMLObjectMetaclass(type):

    def __init__(cls, name, bases, kwds):
        super(YAMLObjectMetaclass, cls).__init__(name, bases, kwds)
        if 'yaml_tag' in kwds and kwds['yaml_tag'] is not None:
            cls.yaml_constructor.add_constructor(cls.yaml_tag, cls.from_yaml)
            cls.yaml_representer.add_representer(cls, cls.to_yaml)

class YAMLObject(object):

    __metaclass__ = YAMLObjectMetaclass

    yaml_constructor = Constructor
    yaml_representer = Representer

    yaml_tag = None

    def from_yaml(cls, constructor, node):
        raise ConstructorError(None, None,
                "found undefined constructor for the tag %r"
                % node.tag.encode('utf-8'), node.start_mark)
    from_yaml = classmethod(from_yaml)

    def to_yaml(cls, representer, native):
        raise RepresenterError(
                "found undefined representer for the object: %s" % native)
    to_yaml = classmethod(to_yaml)

