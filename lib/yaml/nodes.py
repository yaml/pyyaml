
class Node:
    def __init__(self, tag, value, start_mark, end_mark):
        self.tag = tag
        self.value = value
        self.start_mark = start_mark
        self.end_mark = end_mark
    def __repr__(self):
        value = self.value
        if isinstance(value, list):
            if len(value) == 0:
                value = '<empty>'
            elif len(value) == 1:
                value = '<1 item>'
            else:
                value = '<%d items>' % len(value)
        else:
            if len(value) > 75:
                value = repr(value[:70]+u' ... ')
            else:
                value = repr(value)
        return '%s(tag=%r, value=%s)' % (self.__class__.__name__, self.tag, value)

class ScalarNode(Node):
    id = 'scalar'
    def __init__(self, tag, value, implicit, start_mark, end_mark):
        self.tag = tag
        self.value = value
        self.implicit = implicit
        self.start_mark = start_mark
        self.end_mark = end_mark

class CollectionNode(Node):
    pass

class SequenceNode(CollectionNode):
    id = 'sequence'

class MappingNode(CollectionNode):
    id = 'mapping'

