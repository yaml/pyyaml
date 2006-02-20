
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
        node = self.compose_node()
        self.all_anchors = {}
        self.complete_anchors = {}
        return node

    def compose_node(self):
        if self.parser.check(AliasEvent):
            event = self.parser.get()
            anchor = event.anchor
            if anchor not in self.all_anchors:
                raise ComposerError(None, None, "found undefined alias %r"
                        % anchor.encode('utf-8'), event.start_marker)
            if anchor not in self.complete_anchors:
                collection_event = self.all_anchors[anchor]
                raise ComposerError("while composing a collection",
                        collection_event.start_marker,
                        "found recursive anchor %r" % anchor.encode('utf-8'),
                        event.start_marker)
            return self.complete_anchors[anchor]
        event = self.parser.peek()
        anchor = event.anchor
        if anchor is not None:
            if anchor in self.all_anchors:
                raise ComposerError("found duplicate anchor %r; first occurence"
                        % anchor.encode('utf-8'), self.all_anchors[anchor].start_marker,
                        "second occurence", event.start_marker)
            self.all_anchors[anchor] = event
        if self.parser.check(ScalarEvent):
            node = self.compose_scalar_node()
        elif self.parser.check(SequenceEvent):
            node = self.compose_sequence_node()
        elif self.parser.check(MappingEvent):
            node = self.compose_mapping_node()
        if anchor is not None:
            self.complete_anchors[anchor] = node
        return node

    def compose_scalar_node(self):
        event = self.parser.get()
        return ScalarNode(event.tag, event.value,
                event.start_marker, event.end_marker)

    def compose_sequence_node(self):
        start_event = self.parser.get()
        value = []
        while not self.parser.check(CollectionEndEvent):
            value.append(self.compose_node())
        end_event = self.parser.get()
        return SequenceNode(start_event.tag, value,
                start_event.start_marker, end_event.end_marker)

    def compose_mapping_node(self):
        start_event = self.parser.get()
        value = []
        while not self.parser.check(CollectionEndEvent):
            item_key = self.compose_node()
            item_value = self.compose_node()
            value.append((item_key, item_value))
        end_event = self.parser.get()
        return MappingNode(start_event.tag, value,
                start_event.start_marker, end_event.end_marker)

