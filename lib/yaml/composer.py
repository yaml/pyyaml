
__all__ = ['Composer', 'ComposerError']

from error import MarkedYAMLError
from events import *
from nodes import *

class ComposerError(MarkedYAMLError):
    pass

class Composer:

    def __init__(self, parser):
        self.parser = parser
        self.all_anchors = {}
        self.complete_anchors = {}

        # Drop the STREAM-START event.
        self.parser.get()

    def check(self):
        # If there are more documents available?
        return not self.parser.check(StreamEndEvent)

    def get(self):
        # Get the root node of the next document.
        if not self.parser.check(StreamEndEvent):
            return self.compose_document()

    def __iter__(self):
        # Iterator protocol.
        while not self.parser.check(StreamEndEvent):
            yield self.compose_document()

    def compose_document(self):

        # Drop the DOCUMENT-START event.
        self.parser.get()

        # Compose the root node.
        node = self.compose_node()

        # Drop the DOCUMENT-END event.
        self.parser.get()

        self.all_anchors = {}
        self.complete_anchors = {}
        return node

    def compose_node(self):
        if self.parser.check(AliasEvent):
            event = self.parser.get()
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
        event = self.parser.peek()
        anchor = event.anchor
        if anchor is not None:
            if anchor in self.all_anchors:
                raise ComposerError("found duplicate anchor %r; first occurence"
                        % anchor.encode('utf-8'), self.all_anchors[anchor].start_mark,
                        "second occurence", event.start_mark)
            self.all_anchors[anchor] = event
        if self.parser.check(ScalarEvent):
            node = self.compose_scalar_node()
        elif self.parser.check(SequenceStartEvent):
            node = self.compose_sequence_node()
        elif self.parser.check(MappingStartEvent):
            node = self.compose_mapping_node()
        if anchor is not None:
            self.complete_anchors[anchor] = node
        return node

    def compose_scalar_node(self):
        event = self.parser.get()
        return ScalarNode(event.tag, event.value, event.implicit,
                event.start_mark, event.end_mark)

    def compose_sequence_node(self):
        start_event = self.parser.get()
        value = []
        while not self.parser.check(SequenceEndEvent):
            value.append(self.compose_node())
        end_event = self.parser.get()
        return SequenceNode(start_event.tag, value,
                start_event.start_mark, end_event.end_mark)

    def compose_mapping_node(self):
        start_event = self.parser.get()
        value = {}
        while not self.parser.check(MappingEndEvent):
            key_event = self.parser.peek()
            item_key = self.compose_node()
            item_value = self.compose_node()
            if item_key in value:
                raise ComposerError("while composing a mapping", start_event.start_mark,
                        "found duplicate key", key_event.start_mark)
            value[item_key] = item_value
        end_event = self.parser.get()
        return MappingNode(start_event.tag, value,
                start_event.start_mark, end_event.end_mark)

