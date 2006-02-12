
import test_appliance

from yaml.marker import Marker

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
            for str_type in [str, unicode]:
                marker = Marker(test_name, str_type(input), index, line, column)
                snippet = marker.get_snippet()
                #print "INPUT:"
                #print input
                #print "SNIPPET:"
                #print snippet
                self.failUnless(isinstance(snippet, str))
                self.failUnlessEqual(snippet.count('\n'), 2)
                data, pointer, dummy = snippet.split('\n')
                self.failUnless(len(data) < 80)
                self.failUnlessEqual(data[len(pointer)-1], '*')

TestMarker.add_tests('testMarkers', '.markers')

