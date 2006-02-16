
import test_appliance

from yaml.reader import Reader
from yaml.scanner import Scanner
from yaml.parser import *

class TestStructure(test_appliance.TestAppliance):

    def _testStructure(self, test_name, data_filename, structure_filename):
        node1 = None
        node2 = eval(file(structure_filename, 'rb').read())
        try:
            parser = Parser(Scanner(Reader(file(data_filename, 'rb'))))
            node1 = parser.parse()
            node1 = [self._convert(n) for n in node1]
            if len(node1) == 1:
                node1 = node1[0]
            self.failUnlessEqual(node1, node2)
        except:
            print
            print "DATA:"
            print file(data_filename, 'rb').read()
            print "NODE1:", node1
            print "NODE2:", node2
            raise

    def _convert(self, node):
        if isinstance(node, ScalarNode):
            return True
        elif isinstance(node, SequenceNode):
            sequence = []
            for item in node.value:
                sequence.append(self._convert(item))
            return sequence
        elif isinstance(node, MappingNode):
            mapping = []
            for key, value in node.value:
                mapping.append((self._convert(key), self._convert(value)))
            return mapping
        elif isinstance(node, AliasNode):
            return '*'
        else:
            return node

TestStructure.add_tests('testStructure', '.data', '.structure')

class TestParser(test_appliance.TestAppliance):

    def _testParser(self, test_name, data_filename, canonical_filename):
        documents1 = None
        documents2 = None
        try:
            parser = Parser(Scanner(Reader(file(data_filename, 'rb'))))
            documents1 = parser.parse()
            canonical = test_appliance.CanonicalParser(canonical_filename, file(canonical_filename, 'rb').read())
            documents2 = canonical.parse()
            self._compare(documents1, documents2)
        except:
            print
            print "DATA1:"
            print file(data_filename, 'rb').read()
            print "DATA2:"
            print file(canonical_filename, 'rb').read()
            print "DOCUMENTS1:", documents1
            print "DOCUMENTS2:", documents2
            raise

    def _compare(self, value1, value2):
        if value1 is None and hasattr(value2, 'tag') and value2.tag == 'tag:yaml.org,2002:null':
            return
        self.failUnlessEqual(type(value1), type(value2))
        if isinstance(value1, list) or isinstance(value1, tuple):
            self.failUnlessEqual(len(value1), len(value2))
            for item1, item2 in zip(value1, value2):
                self._compare(item1, item2)
        else:
            self.failUnlessEqual(value1.__class__.__name__, value2.__class__.__name__)
            if isinstance(value1, SequenceNode) or isinstance(value1, MappingNode):
                self._compare(value1.value, value2.value)

TestParser.add_tests('testParser', '.data', '.canonical')

