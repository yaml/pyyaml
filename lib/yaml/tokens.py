
class Token:
    def __init__(self, start_marker, end_marker):
        self.start_marker = start_marker
        self.end_marker = end_marker

class DirectiveToken(Token):
    pass

class YAMLDirectiveToken(DirectiveToken):
    def __init__(self, major_version, minor_version, start_marker, end_marker):
        self.major_version = major_version
        self.minor_version = minor_version
        self.start_marker = start_marker
        self.end_marker = end_marker

class TagDirectiveToken(DirectiveToken):
    pass

class ReservedDirectiveToken(DirectiveToken):
    def __init__(self, name, start_marker, end_marker):
        self.name = name
        self.start_marker = start_marker
        self.end_marker = end_marker

class DocumentStartToken(Token):
    pass

class DocumentEndToken(Token):
    pass

class EndToken(Token):
    pass

class BlockSequenceStartToken(Token):
    pass

class BlockMappingStartToken(Token):
    pass

class BlockEndToken(Token):
    pass

class FlowSequenceStartToken(Token):
    pass

class FlowMappingStartToken(Token):
    pass

class FlowSequenceEndToken(Token):
    pass

class FlowMappingEndToken(Token):
    pass

class KeyToken(Token):
    pass

class ValueToken(Token):
    pass

class EntryToken(Token):
    pass

class AliasToken(Token):
    def __init__(self, value, start_marker, end_marker):
        self.value = value
        self.start_marker = start_marker
        self.end_marker = end_marker

class AnchorToken(Token):
    def __init__(self, value, start_marker, end_marker):
        self.value = value
        self.start_marker = start_marker
        self.end_marker = end_marker

class TagToken(Token):
    def __init__(self, value, start_marker, end_marker):
        self.value = value
        self.start_marker = start_marker
        self.end_marker = end_marker

class ScalarToken(Token):
    def __init__(self, value, plain, start_marker, end_marker):
        self.value = value
        self.plain = plain
        self.start_marker = start_marker
        self.end_marker = end_marker

