
import test_appliance

from yaml.reader import Reader
from yaml.scanner import Scanner
from yaml.parser import *
from yaml.composer import *
from yaml.resolver import *
from yaml.nodes import *

class TestDetector(test_appliance.TestAppliance):

    def _testDetector(self, test_name, data_filename, detect_filename):
        node = None
        correct_tag = None
        try:
            correct_tag = file(detect_filename, 'rb').read().strip()
            resolver = Resolver(Composer(Parser(Scanner(Reader(file(data_filename, 'rb'))))))
            node = list(iter(resolver))[0]
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


