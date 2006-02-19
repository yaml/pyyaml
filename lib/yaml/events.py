
class Event:
    def __init__(self, start_marker, end_marker):
        self.start_marker = start_marker
        self.end_marker = end_marker
    def __repr__(self):
        attributes = [key for key in self.__dict__
                if not key.endswith('_marker')]
        attributes.sort()
        arguments = ', '.join(['%s=%r' % (key, getattr(self, key))
                for key in attributes])
        return '%s(%s)' % (self.__class__.__name__, arguments)

class NodeEvent(Event):
    def __init__(self, anchor, tag, start_marker, end_marker):
        self.anchor = anchor
        self.tag = tag
        self.start_marker = start_marker
        self.end_marker = end_marker

class AliasEvent(NodeEvent):
    def __init__(self, name, start_marker, end_marker):
        self.name = name
        self.start_marker = start_marker
        self.end_marker = end_marker

class ScalarEvent(NodeEvent):
    def __init__(self, anchor, tag, value, start_marker, end_marker):
        self.anchor = anchor
        self.tag = tag
        self.value = value
        self.start_marker = start_marker
        self.end_marker = end_marker

class CollectionEvent(NodeEvent):
    pass

class SequenceEvent(CollectionEvent):
    pass

class MappingEvent(CollectionEvent):
    pass

class CollectionEndEvent(Event):
    pass

class StreamEndEvent(Event):
    pass

