
__all__ = ['Resolver', 'ResolverError']

from error import MarkedYAMLError
from detector import Detector
from nodes import *

import re

# Not really used.
class ResolverError(MarkedYAMLError):
    pass

class Resolver(Detector):

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
            node.tag = self.detect(node.value)
        if node.tag is None or node.tag == u'!':
            node.tag = self.DEFAULT_SCALAR_TAG

    def resolve_sequence(self, path, node):
        if node.tag is None or node.tag == u'!':
            node.tag = self.DEFAULT_SEQUENCE_TAG

    def resolve_mapping(self, path, node):
        if node.tag is None or node.tag == u'!':
            node.tag = self.DEFAULT_MAPPING_TAG

