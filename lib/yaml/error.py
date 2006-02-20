
__all__ = ['Marker', 'YAMLError', 'MarkedYAMLError']

class Marker:

    def __init__(self, name, line, column, buffer, pointer):
        self.name = name
        self.line = line
        self.column = column
        self.buffer = buffer
        self.pointer = pointer

    def get_snippet(self, indent=4, max_length=75):
        if self.buffer is None:
            return None
        head = ''
        start = self.pointer
        while start > 0 and self.buffer[start-1] not in u'\0\r\n\x85\u2028\u2029':
            start -= 1
            if self.pointer-start > max_length/2-1:
                head = ' ... '
                start += 5
                break
        tail = ''
        end = self.pointer
        while end < len(self.buffer) and self.buffer[end] not in u'\0\r\n\x85\u2028\u2029':
            end += 1
            if end-self.pointer > max_length/2-1:
                tail = ' ... '
                end -= 5
                break
        snippet = self.buffer[start:end].encode('utf-8')
        return ' '*indent + head + snippet + tail + '\n'  \
                + ' '*(indent+self.pointer-start+len(head)) + '^'

    def __str__(self):
        snippet = self.get_snippet()
        where = "  in \"%s\", line %d, column %d"   \
                % (self.name, self.line+1, self.column+1)
        if snippet is not None:
            where += ":\n"+snippet
        return where

class YAMLError(Exception):
    pass

class MarkedYAMLError(YAMLError):

    def __init__(self, context=None, context_marker=None,
            problem=None, problem_marker=None):
        self.context = context
        self.context_marker = context_marker
        self.problem = problem
        self.problem_marker = problem_marker

    def __str__(self):
        lines = []
        #for (place, marker) in [(self.context, self.context_marker),
        #                        (self.problem, self.problem_marker)]:
        #    if place is not None:
        #        lines.append(place)
        #        if marker is not None:
        #            lines.append(str(marker))
        if self.context is not None:
            lines.append(self.context)
            if self.context_marker is not None  \
                and (self.problem is None or self.problem_marker is None
                        or self.context_marker.name != self.problem_marker.name
                        or self.context_marker.line != self.problem_marker.line
                        or self.context_marker.column != self.problem_marker.column):
                lines.append(str(self.context_marker))
        if self.problem is not None:
            lines.append(self.problem)
            if self.problem_marker is not None:
                lines.append(str(self.problem_marker))
        return '\n'.join(lines)



