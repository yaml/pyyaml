
__all__ = ['BaseComposer', 'Composer', 'ComposerError']

from error import MarkedYAMLError
from events import *
from nodes import *

class ComposerError(MarkedYAMLError):
    pass

class BaseComposer:

    yaml_resolvers = {}

    def __init__(self):
        self.all_anchors = {}
        self.complete_anchors = {}
        self.resolver_tags = []
        self.resolver_paths = []

    def check_node(self):
        # If there are more documents available?
        return not self.check_event(StreamEndEvent)

    def get_node(self):
        # Get the root node of the next document.
        if not self.check_event(StreamEndEvent):
            return self.compose_document()

    def __iter__(self):
        # Iterator protocol.
        while not self.check_event(StreamEndEvent):
            yield self.compose_document()

    def compose_document(self):

        # Drop the STREAM-START event.
        if self.check_event(StreamStartEvent):
            self.get_event()

        # Drop the DOCUMENT-START event.
        self.get_event()

        # Compose the root node.
        node = self.compose_node([])

        # Drop the DOCUMENT-END event.
        self.get_event()

        self.all_anchors = {}
        self.complete_anchors = {}
        self.resolver_tags = []
        self.resolver_paths = []
        return node

    def increase_resolver_depth(self, path):
        depth = len(path)
        tag = None
        paths = []
        if not depth:
            for resolver_path in self.yaml_resolvers.keys():
                if resolver_path:
                    paths.append(resolver_path)
                else:
                    tag = self.yaml_resolvers[resolver_path]
        else:
            base, index = path[-1]
            if isinstance(index, ScalarNode)    \
                    and index.tag == self.DEFAULT_SCALAR_TAG:
                index = index.value
            elif isinstance(index, Node):
                index = None
            for resolver_path in self.resolver_paths[-1]:
                resolver_index = resolver_path[depth-1]
                if resolver_index is None or resolver_index == index:
                    if len(resolver_index) > depth:
                        paths.append(resolver_path)
                    else:
                        tag = self.yaml_resolvers[resolver_path]
        self.resolver_tags.append(tag)
        self.resolver_paths.append(paths)

    def decrease_resolver_depth(self):
        del self.resolver_tags[-1]
        del self.resolver_paths[-1]

    def compose_node(self, path):
        if self.check_event(AliasEvent):
            event = self.get_event()
            anchor = event.anchor
            if anchor not in self.all_anchors:
                raise ComposerError(None, None, "found undefined alias %r"
                        % anchor.encode('utf-8'), event.start_mark)
            if anchor not in self.complete_anchors:
                collection_event = self.all_anchors[anchor]
                raise ComposerError("while composing a collection",
                        collection_event.start_mark,
                        "found recursive anchor %r" % anchor.encode('utf-8'),
                        event.start_mark)
            return self.complete_anchors[anchor]
        self.increase_resolver_depth(path)
        event = self.peek_event()
        anchor = event.anchor
        if anchor is not None:
            if anchor in self.all_anchors:
                raise ComposerError("found duplicate anchor %r; first occurence"
                        % anchor.encode('utf-8'), self.all_anchors[anchor].start_mark,
                        "second occurence", event.start_mark)
            self.all_anchors[anchor] = event
        if self.check_event(ScalarEvent):
            node = self.compose_scalar_node(path)
        elif self.check_event(SequenceStartEvent):
            node = self.compose_sequence_node(path)
        elif self.check_event(MappingStartEvent):
            node = self.compose_mapping_node(path)
        if anchor is not None:
            self.complete_anchors[anchor] = node
        self.decrease_resolver_depth()
        return node

    def compose_scalar_node(self, path):
        event = self.get_event()
        tag = self.resolve_scalar(path, event.tag, event.implicit, event.value)
        return ScalarNode(tag, event.value,
                event.start_mark, event.end_mark, style=event.style)

    def compose_sequence_node(self, path):
        start_event = self.get_event()
        tag = self.resolve_sequence(path, start_event.tag)
        node = SequenceNode(tag, [],
                start_event.start_mark, None,
                flow_style=start_event.flow_style)
        index = 0
        while not self.check_event(SequenceEndEvent):
            node.value.append(self.compose_node(path+[(node, index)]))
            index += 1
        end_event = self.get_event()
        node.end_mark = end_event.end_mark
        return node

    def compose_mapping_node(self, path):
        start_event = self.get_event()
        tag = self.resolve_mapping(path, start_event.tag)
        node = MappingNode(tag, {},
                start_event.start_mark, None,
                flow_style=start_event.flow_style)
        while not self.check_event(MappingEndEvent):
            key_event = self.peek_event()
            item_key = self.compose_node(path+[(node, None)])
            item_value = self.compose_node(path+[(node, item_key)])
            if item_key in node.value:
                raise ComposerError("while composing a mapping", start_event.start_mark,
                        "found duplicate key", key_event.start_mark)
            node.value[item_key] = item_value
        end_event = self.get_event()
        node.end_mark = end_event.end_mark
        return node

    def resolve_scalar(self, path, tag, implicit, value):
        if implicit:
            tag = self.detect(value)
        if tag is None and self.resolver_tags[-1]:
            tag = self.resolver_tags[-1]
        if tag is None or tag == u'!':
            tag = self.DEFAULT_SCALAR_TAG
        return tag

    def resolve_sequence(self, path, tag):
        if tag is None and self.resolver_tags[-1]:
            tag = self.resolver_tags[-1]
        if tag is None or tag == u'!':
            tag = self.DEFAULT_SEQUENCE_TAG
        return tag

    def resolve_mapping(self, path, tag):
        if tag is None and self.resolver_tags[-1]:
            tag = self.resolver_tags[-1]
        if tag is None or tag == u'!':
            tag = self.DEFAULT_MAPPING_TAG
        return tag

    def add_resolver(self, tag, path):
        if not 'yaml_resolvers' in cls.__dict__:
            cls.yaml_resolvers = cls.yaml_resolvers.copy()
        cls.yaml_resolvers[tuple(path)] = tag
    add_resolver = classmethod(add_resolver)

class Composer(BaseComposer):
    pass

