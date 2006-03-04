
import test_appliance

from yaml.reader import Marker

class TestMarker(test_appliance.TestAppliance):

    def _testMarkers(self, test_name, markers_filename):
        inputs = file(markers_filename, 'rb').read().split('---\n')[1:]
        for input in inputs:
            index = 0
            line = 0
            column = 0
            while input[index] != '*':
                if input[index] == '\n':
                    line += 1
                    column = 0
                else:
                    column += 1
                index += 1
            marker = Marker(test_name, line, column, unicode(input), index)
            snippet = marker.get_snippet(indent=2, max_length=79)
            #print "INPUT:"
            #print input
            #print "SNIPPET:"
            #print snippet
            self.failUnless(isinstance(snippet, str))
            self.failUnlessEqual(snippet.count('\n'), 1)
            data, pointer = snippet.split('\n')
            self.failUnless(len(data) < 82)
            self.failUnlessEqual(data[len(pointer)-1], '*')

TestMarker.add_tests('testMarkers', '.markers')

