
class Token:
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

#class BOMToken(Token):
#    id = '<byte order mark>'

class DirectiveToken(Token):
    id = '<directive>'
    def __init__(self, name, value, start_marker, end_marker):
        self.name = name
        self.value = value
        self.start_marker = start_marker
        self.end_marker = end_marker

class DocumentStartToken(Token):
    id = '<document start>'

class DocumentEndToken(Token):
    id = '<document end>'

class StreamEndToken(Token):
    id = '<stream end>'

class BlockSequenceStartToken(Token):
    id = '<block sequence start>'

class BlockMappingStartToken(Token):
    id = '<block mapping end>'

class BlockEndToken(Token):
    id = '<block end>'

class FlowSequenceStartToken(Token):
    id = '['

class FlowMappingStartToken(Token):
    id = '{'

class FlowSequenceEndToken(Token):
    id = ']'

class FlowMappingEndToken(Token):
    id = '}'

class KeyToken(Token):
    id = '?'

class ValueToken(Token):
    id = ':'

class BlockEntryToken(Token):
    id = '-'

class FlowEntryToken(Token):
    id = ','

class AliasToken(Token):
    id = '<alias>'
    def __init__(self, value, start_marker, end_marker):
        self.value = value
        self.start_marker = start_marker
        self.end_marker = end_marker

class AnchorToken(Token):
    id = '<anchor>'
    def __init__(self, value, start_marker, end_marker):
        self.value = value
        self.start_marker = start_marker
        self.end_marker = end_marker

class TagToken(Token):
    id = '<tag>'
    def __init__(self, value, start_marker, end_marker):
        self.value = value
        self.start_marker = start_marker
        self.end_marker = end_marker

class ScalarToken(Token):
    id = '<scalar>'
    def __init__(self, value, plain, start_marker, end_marker):
        self.value = value
        self.plain = plain
        self.start_marker = start_marker
        self.end_marker = end_marker

