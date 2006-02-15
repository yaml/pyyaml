
class Marker:

    def __init__(self, source, data, index, line, column):
        self.source = source
        self.data = data
        self.index = index
        self.line = line
        self.column = column

    def get_snippet(self, max_length=79):
        if not isinstance(self.data, basestring):
            return None
        head = ''
        start = self.index
        while start > 0 and self.data[start-1] not in '\r\n':
            start -= 1
            if self.index-start > max_length/2-1:
                head = ' ... '
                start += 5
                break
        tail = ''
        end = self.index
        while end < len(self.data) and self.data[end] not in '\r\n':
            end += 1
            if end-self.index > max_length/2-1:
                tail = ' ... '
                end -= 5
                break
        snippet = self.data[start:end]
        if isinstance(snippet, unicode):
            snippet = snippet.encode('utf-8')
        return head + snippet + tail + '\n'  \
                + ' '*(self.index-start+len(head)) + '^' + '\n'

