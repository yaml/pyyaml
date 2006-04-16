
__all__ = ['Composer', 'ComposerError']

from error import MarkedYAMLError
from events import *
from nodes import *

class ComposerError(MarkedYAMLError):
    pass

class Composer:

    def __init__(self):
        self.all_anchors = {}
        self.complete_anchors = {}

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
        node = self.compose_node(None, None)

        # Drop the DOCUMENT-END event.
        self.get_event()

        self.all_anchors = {}
        self.complete_anchors = {}
        return node

    def compose_node(self, parent, index):
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
        event = self.peek_event()
        anchor = event.anchor
        if anchor is not None:
            if anchor in self.all_anchors:
                raise ComposerError("found duplicate anchor %r; first occurence"
                        % anchor.encode('utf-8'), self.all_anchors[anchor].start_mark,
                        "second occurence", event.start_mark)
            self.all_anchors[anchor] = event
        self.descend_resolver(parent, index)
        if self.check_event(ScalarEvent):
            node = self.compose_scalar_node()
        elif self.check_event(SequenceStartEvent):
            node = self.compose_sequence_node()
        elif self.check_event(MappingStartEvent):
            node = self.compose_mapping_node()
        if anchor is not None:
            self.complete_anchors[anchor] = node
        self.ascend_resolver()
        return node

    def compose_scalar_node(self):
        event = self.get_event()
        tag = event.tag
        if tag is None or tag == u'!':
            tag = self.resolve(ScalarNode, event.value, event.implicit)
        return ScalarNode(tag, event.value,
                event.start_mark, event.end_mark, style=event.style)

    def compose_sequence_node(self):
        start_event = self.get_event()
        tag = start_event.tag
        if tag is None or tag == u'!':
            tag = self.resolve(SequenceNode, None, start_event.implicit)
        node = SequenceNode(tag, [],
                start_event.start_mark, None,
                flow_style=start_event.flow_style)
        index = 0
        while not self.check_event(SequenceEndEvent):
            node.value.append(self.compose_node(node, index))
            index += 1
        end_event = self.get_event()
        node.end_mark = end_event.end_mark
        return node

    def compose_mapping_node(self):
        start_event = self.get_event()
        tag = start_event.tag
        if tag is None or tag == u'!':
            tag = self.resolve(MappingNode, None, start_event.implicit)
        node = MappingNode(tag, {},
                start_event.start_mark, None,
                flow_style=start_event.flow_style)
        while not self.check_event(MappingEndEvent):
            key_event = self.peek_event()
            item_key = self.compose_node(node, None)
            if item_key in node.value:
                raise ComposerError("while composing a mapping", start_event.start_mark,
                        "found duplicate key", key_event.start_mark)
            item_value = self.compose_node(node, item_key)
            node.value[item_key] = item_value
        end_event = self.get_event()
        node.end_mark = end_event.end_mark
        return node

