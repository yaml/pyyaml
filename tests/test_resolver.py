
import test_appliance

from yaml import *

class MyLoader(Loader):
    pass

class MyDumper(Dumper):
    pass

add_path_resolver(u'!root', [],
        Loader=MyLoader, Dumper=MyDumper)

add_path_resolver(u'!root/scalar', [], str,
        Loader=MyLoader, Dumper=MyDumper)

add_path_resolver(u'!root/key11/key12/*', ['key11', 'key12'],
        Loader=MyLoader, Dumper=MyDumper)

add_path_resolver(u'!root/key21/1/*', ['key21', 1],
        Loader=MyLoader, Dumper=MyDumper)

add_path_resolver(u'!root/key31/*/*/key14/map', ['key31', None, None, 'key14'], dict,
        Loader=MyLoader, Dumper=MyDumper)

class TestResolver(test_appliance.TestAppliance):

    def _testImplicitResolver(self, test_name, data_filename, detect_filename):
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

    def _testPathResolverLoader(self, test_name, data_filename, path_filename):
        #print serialize_all(compose_all(file(data_filename, 'rb').read(), Loader=MyLoader))
        nodes1 = compose_all(file(data_filename, 'rb').read(), Loader=MyLoader)
        nodes2 = compose_all(file(path_filename, 'rb').read())
        for node1, node2 in zip(nodes1, nodes2):
            self.failUnlessEqual(self._convert(node1), self._convert(node2))

    def _testPathResolverDumper(self, test_name, data_filename, path_filename):
        for filename in [data_filename, path_filename]:
            output = serialize_all(compose_all(file(filename, 'rb').read()), Dumper=MyDumper)
            #print output
            nodes1 = compose_all(output)
            nodes2 = compose_all(file(data_filename, 'rb').read())
            for node1, node2 in zip(nodes1, nodes2):
                self.failUnlessEqual(self._convert(node1), self._convert(node2))

    def _convert(self, node):
        if isinstance(node, ScalarNode):
            return node.tag, node.value
        elif isinstance(node, SequenceNode):
            value = []
            for item in node.value:
                value.append(self._convert(item))
            return node.tag, value
        elif isinstance(node, MappingNode):
            value = []
            for key, item in node.value:
                value.append((self._convert(key), self._convert(item)))
            value.sort()
            return node.tag, value

TestResolver.add_tests('testImplicitResolver', '.data', '.detect')
TestResolver.add_tests('testPathResolverLoader', '.data', '.path')
TestResolver.add_tests('testPathResolverDumper', '.data', '.path')

