
class Event:
    def __init__(self, start_mark=None, end_mark=None):
        self.start_mark = start_mark
        self.end_mark = end_mark
    def __repr__(self):
        attributes = [key for key in ['anchor', 'tag', 'value']
                if hasattr(self, key)]
        arguments = ', '.join(['%s=%r' % (key, getattr(self, key))
                for key in attributes])
        return '%s(%s)' % (self.__class__.__name__, arguments)

class NodeEvent(Event):
    def __init__(self, anchor, start_mark=None, end_mark=None):
        self.anchor = anchor
        self.start_mark = start_mark
        self.end_mark = end_mark

class AliasEvent(NodeEvent):
    pass

class ScalarEvent(NodeEvent):
    def __init__(self, anchor, tag, value, start_mark=None, end_mark=None,
            implicit=None, style=None):
        self.anchor = anchor
        self.tag = tag
        self.value = value
        self.start_mark = start_mark
        self.end_mark = end_mark
        self.implicit = implicit
        self.style = style

class CollectionEvent(NodeEvent):
    def __init__(self, anchor, tag, start_mark=None, end_mark=None,
            flow=None, compact=None):
        self.anchor = anchor
        self.tag = tag
        self.start_mark = start_mark
        self.end_mark = end_mark
        self.flow = flow
        self.compact = compact

class SequenceEvent(CollectionEvent):
    pass

class MappingEvent(CollectionEvent):
    pass

class CollectionEndEvent(Event):
    pass

class DocumentStartEvent(Event):
    def __init__(self, start_mark=None, end_mark=None,
            indent=None, implicit=None, version=None, tags=None,
            canonical=None):
        self.start_mark = start_mark
        self.end_mark = end_mark
        self.indent = indent
        self.implicit = implicit
        self.version = version
        self.tags = tags
        self.canonical = canonical

class DocumentEndEvent(Event):
    pass

class StreamStartEvent(Event):
    def __init__(self, start_mark=None, end_mark=None,
            encoding=None):
        self.start_mark = start_mark
        self.end_mark = end_mark
        self.encoding = encoding

class StreamEndEvent(Event):
    pass

