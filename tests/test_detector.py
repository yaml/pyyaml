
import test_appliance

from yaml import *

class TestDetector(test_appliance.TestAppliance):

    def _testDetector(self, test_name, data_filename, detect_filename):
        node = None
        correct_tag = None
        try:
            correct_tag = file(detect_filename, 'rb').read().strip()
            node = compose(file(data_filename, 'rb'))
            self.failUnless(isinstance(node, SequenceNode))
            for scalar in node.value:
                self.failUnless(isinstance(scalar, ScalarNode))
                self.failUnlessEqual(scalar.tag, correct_tag)
        except:
            print
            print "DATA:"
            print file(data_filename, 'rb').read()
            print "CORRECT_TAG:"
            print file(detect_filename, 'rb').read()
            print "ROOT NODE:", node
            print "SCALAR NODES:", node.value
            raise

TestDetector.add_tests('testDetector', '.data', '.detect')

