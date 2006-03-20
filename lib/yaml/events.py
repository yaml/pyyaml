
class Event:
    def __init__(self, start_mark, end_mark):
        self.start_mark = start_mark
        self.end_mark = end_mark
    def __repr__(self):
        attributes = [key for key in self.__dict__
                if not key.endswith('_mark')]
        attributes.sort()
        arguments = ', '.join(['%s=%r' % (key, getattr(self, key))
                for key in attributes])
        return '%s(%s)' % (self.__class__.__name__, arguments)

class NodeEvent(Event):
    def __init__(self, anchor, start_mark, end_mark):
        self.anchor = anchor
        self.start_mark = start_mark
        self.end_mark = end_mark

class AliasEvent(NodeEvent):
    pass

class ScalarEvent(NodeEvent):
    def __init__(self, anchor, tag, value, start_mark, end_mark):
        self.anchor = anchor
        self.tag = tag
        self.value = value
        self.start_mark = start_mark
        self.end_mark = end_mark

class CollectionEvent(NodeEvent):
    def __init__(self, anchor, tag, start_mark, end_mark):
        self.anchor = anchor
        self.tag = tag
        self.start_mark = start_mark
        self.end_mark = end_mark

class SequenceEvent(CollectionEvent):
    pass

class MappingEvent(CollectionEvent):
    pass

class CollectionEndEvent(Event):
    pass

class DocumentStartEvent(Event):
    pass

class DocumentEndEvent(Event):
    pass

class StreamStartEvent(Event):
    pass

class StreamEndEvent(Event):
    pass

