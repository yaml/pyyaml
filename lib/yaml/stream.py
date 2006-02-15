
from marker import Marker

class Stream:

    def __init__(self, source, data):
        self.source = source
        self.data = unicode(data, 'utf-8')+u'\0'
        self.index = 0
        self.line = 0
        self.column = 0

    def peek(self, k=1):
        return self.data[self.index:self.index+k]

    def read(self, k=1):
        value = self.data[self.index:self.index+k]
        for i in range(k):
            if self.index >= len(self.data):
                break
            if self.data[self.index] in u'\r\n\x85\u2028\u2029':
                self.line += 1
                self.column = 0
            else:
                self.column += 1
            self.index += 1
        return value

    def get_marker(self):
        return Marker(self.source, self.data, self.index, self.line, self.column)

