
class Token:
    def __init__(self, start_marker, end_marker):
        self.start_marker = start_marker
        self.end_marker = end_marker

class DirectiveToken(Token):
    code = '<directive>'
    def __init__(self, name, value, start_marker, end_marker):
        self.name = name
        self.value = value
        self.start_marker = start_marker
        self.end_marker = end_marker

class DocumentStartToken(Token):
    code = '<document start>'

class DocumentEndToken(Token):
    code = '<document end>'

class StreamEndToken(Token):
    code = '<stream end>'

class BlockSequenceStartToken(Token):
    code = '<block sequence start>'

class BlockMappingStartToken(Token):
    code = '<block mapping end>'

class BlockEndToken(Token):
    code = '<block end>'

class FlowSequenceStartToken(Token):
    code = '['

class FlowMappingStartToken(Token):
    code = '{'

class FlowSequenceEndToken(Token):
    code = ']'

class FlowMappingEndToken(Token):
    code = '}'

class KeyToken(Token):
    code = '?'

class ValueToken(Token):
    code = ':'

class EntryToken(Token):
    code = '- or ,'

class AliasToken(Token):
    code = '<alias>'
    def __init__(self, value, start_marker, end_marker):
        self.value = value
        self.start_marker = start_marker
        self.end_marker = end_marker

class AnchorToken(Token):
    code = '<anchor>'
    def __init__(self, value, start_marker, end_marker):
        self.value = value
        self.start_marker = start_marker
        self.end_marker = end_marker

class TagToken(Token):
    code = '<tag>'
    def __init__(self, value, start_marker, end_marker):
        self.value = value
        self.start_marker = start_marker
        self.end_marker = end_marker

class ScalarToken(Token):
    code = '<scalar>'
    def __init__(self, value, plain, start_marker, end_marker):
        self.value = value
        self.plain = plain
        self.start_marker = start_marker
        self.end_marker = end_marker

