
__all__ = ['BaseResolver', 'Resolver', 'ResolverError']

from error import MarkedYAMLError
from nodes import *

import re

# Not really used.
class ResolverError(MarkedYAMLError):
    pass

class BaseResolver:

    DEFAULT_SCALAR_TAG = u'tag:yaml.org,2002:str'
    DEFAULT_SEQUENCE_TAG = u'tag:yaml.org,2002:seq'
    DEFAULT_MAPPING_TAG = u'tag:yaml.org,2002:map'

    def __init__(self, composer):
        self.composer = composer
        self.resolved_nodes = {}

    def check(self):
        # If there are more documents available?
        return self.composer.check()

    def get(self):
        # Resolve and return the root node of the next document.
        if self.composer.check():
            return self.resolve_document(self.composer.get())

    def __iter__(self):
        # Iterator protocol.
        while self.composer.check():
            yield self.resolve_document(self.composer.get())

    def resolve_document(self, node):
        self.resolve_node([], node)
        return node
        self.resolved_nodes = {}

    def resolve_node(self, path, node):
        if node in self.resolved_nodes:
            return
        self.resolved_nodes[node] = None
        if isinstance(node, ScalarNode):
            self.resolve_scalar(path, node)
        elif isinstance(node, SequenceNode):
            self.resolve_sequence(path, node)
            for index in range(len(node.value)):
                self.resolve_node(path+[(node, index)], node.value[index])
        elif isinstance(node, MappingNode):
            self.resolve_mapping(path, node)
            for key in node.value:
                self.resolve_node(path+[node, None], key)
                self.resolve_node(path+[node, key], node.value[key])

    def resolve_scalar(self, path, node):
        if node.tag is None and node.implicit:
            node.tag = self.detect_scalar(node.value)
        if node.tag is None or node.tag == u'!':
            node.tag = self.DEFAULT_SCALAR_TAG

    def resolve_sequence(self, path, node):
        if node.tag is None or node.tag == u'!':
            node.tag = self.DEFAULT_SEQUENCE_TAG

    def resolve_mapping(self, path, node):
        if node.tag is None or node.tag == u'!':
            node.tag = self.DEFAULT_MAPPING_TAG

    def detect_scalar(self, value):
        if value == u'':
            detectors = self.yaml_detectors.get(u'', [])
        else:
            detectors = self.yaml_detectors.get(value[0], [])
        detectors += self.yaml_detectors.get(None, [])
        for tag, regexp in detectors:
            if regexp.match(value):
                return tag

    def add_detector(cls, tag, regexp, first):
        if not 'yaml_detectors' in cls.__dict__:
            cls.yaml_detectors = cls.yaml_detectors.copy()
        for ch in first:
            cls.yaml_detectors.setdefault(ch, []).append((tag, regexp))
    add_detector = classmethod(add_detector)

    yaml_detectors = {}

class Resolver(BaseResolver):
    pass

Resolver.add_detector(
        u'tag:yaml.org,2002:bool',
        re.compile(ur'''^(?:yes|Yes|YES|n|N|no|No|NO
                    |true|True|TRUE|false|False|FALSE
                    |on|On|ON|off|Off|OFF)$''', re.X),
        list(u'yYnNtTfFoO'))

Resolver.add_detector(
        u'tag:yaml.org,2002:float',
        re.compile(ur'''^(?:[-+]?(?:[0-9][0-9_]*)?\.[0-9_]*(?:[eE][-+][0-9]+)?
                    |[-+]?[0-9][0-9_]*(?::[0-5]?[0-9])+\.[0-9_]*
                    |[-+]?\.(?:inf|Inf|INF)
                    |\.(?:nan|NaN|NAN))$''', re.X),
        list(u'-+0123456789.'))

Resolver.add_detector(
        u'tag:yaml.org,2002:int',
        re.compile(ur'''^(?:[-+]?0b[0-1_]+
                    |[-+]?0[0-7_]+
                    |[-+]?(?:0|[1-9][0-9_]*)
                    |[-+]?0x[0-9a-fA-F_]+
                    |[-+]?[1-9][0-9_]*(?::[0-5]?[0-9])+)$''', re.X),
        list(u'-+0123456789'))

Resolver.add_detector(
        u'tag:yaml.org,2002:merge',
        re.compile(ur'^(?:<<)$'),
        ['<'])

Resolver.add_detector(
        u'tag:yaml.org,2002:null',
        re.compile(ur'''^(?: ~
                    |null|Null|NULL
                    | )$''', re.X),
        [u'~', u'n', u'N', u''])

Resolver.add_detector(
        u'tag:yaml.org,2002:timestamp',
        re.compile(ur'''^(?:[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]
                    |[0-9][0-9][0-9][0-9] -[0-9][0-9]? -[0-9][0-9]?
                     (?:[Tt]|[ \t]+)[0-9][0-9]?
                     :[0-9][0-9] :[0-9][0-9] (?:\.[0-9]*)?
                     (?:[ \t]*(?:Z|[-+][0-9][0-9]?(?::[0-9][0-9])?))?)$''', re.X),
        list(u'0123456789'))

Resolver.add_detector(
        u'tag:yaml.org,2002:value',
        re.compile(ur'^(?:=)$'),
        ['='])

# The following detector is only for documentation purposes. It cannot work
# because plain scalars cannot start with '!', '&', or '*'.
Resolver.add_detector(
        u'tag:yaml.org,2002:yaml',
        re.compile(ur'^(?:!|&|\*)$'),
        list(u'!&*'))

