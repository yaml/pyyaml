
import test_appliance

from yaml import *

class TestStructure(test_appliance.TestAppliance):

    def _testStructure(self, test_name, data_filename, structure_filename):
        node1 = None
        node2 = eval(file(structure_filename, 'rb').read())
        try:
            loader = Loader(file(data_filename, 'rb'))
            node1 = []
            while not loader.check_event(StreamEndEvent):
                if not loader.check_event(StreamStartEvent, DocumentStartEvent, DocumentEndEvent):
                    node1.append(self._convert(loader))
                else:
                    loader.get_event()
            loader.get_event()
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

    def _convert(self, loader):
        if loader.check_event(ScalarEvent):
            event = loader.get_event()
            if event.tag or event.anchor or event.value:
                return True
            else:
                return None
        elif loader.check_event(SequenceStartEvent):
            loader.get_event()
            sequence = []
            while not loader.check_event(SequenceEndEvent):
                sequence.append(self._convert(loader))
            loader.get_event()
            return sequence
        elif loader.check_event(MappingStartEvent):
            loader.get_event()
            mapping = []
            while not loader.check_event(MappingEndEvent):
                key = self._convert(loader)
                value = self._convert(loader)
                mapping.append((key, value))
            loader.get_event()
            return mapping
        elif loader.check_event(AliasEvent):
            loader.get_event()
            return '*'
        else:
            loader.get_event()
            return '?'

TestStructure.add_tests('testStructure', '.data', '.structure')

class TestParser(test_appliance.TestAppliance):

    def _testParser(self, test_name, data_filename, canonical_filename):
        events1 = None
        events2 = None
        try:
            events1 = list(parse(file(data_filename, 'rb')))
            events2 = list(test_appliance.canonical_parse(file(canonical_filename, 'rb')))
            self._compare(events1, events2)
        except:
            print
            print "DATA1:"
            print file(data_filename, 'rb').read()
            print "DATA2:"
            print file(canonical_filename, 'rb').read()
            print "EVENTS1:", events1
            print "EVENTS2:", events2
            raise

    def _compare(self, events1, events2):
        self.failUnlessEqual(len(events1), len(events2))
        for event1, event2 in zip(events1, events2):
            self.failUnlessEqual(event1.__class__, event2.__class__)
            if isinstance(event1, AliasEvent):
                #self.failUnlessEqual(event1.name, event2.name)
                pass
            elif isinstance(event1, ScalarEvent):
                #self.failUnlessEqual(event1.anchor, event2.anchor)
                #self.failUnlessEqual(event1.tag, event2.tag)
                self.failUnlessEqual(event1.value, event2.value)
            if isinstance(event1, CollectionStartEvent):
                #self.failUnlessEqual(event1.anchor, event2.anchor)
                #self.failUnlessEqual(event1.tag, event2.tag)
                pass

TestParser.add_tests('testParser', '.data', '.canonical')

class TestResolver(test_appliance.TestAppliance):

    def _testResolver(self, test_name, data_filename, canonical_filename):
        nodes1 = None
        nodes2 = None
        try:
            nodes1 = list(compose_all(file(data_filename, 'rb')))
            nodes2 = list(test_appliance.canonical_compose_all(file(canonical_filename, 'rb')))
            self.failUnlessEqual(len(nodes1), len(nodes2))
            for node1, node2 in zip(nodes1, nodes2):
                self._compare(node1, node2)
        except:
            print
            print "DATA1:"
            print file(data_filename, 'rb').read()
            print "DATA2:"
            print file(canonical_filename, 'rb').read()
            print "NODES1:", nodes1
            print "NODES2:", nodes2
            raise

    def _compare(self, node1, node2):
        self.failUnlessEqual(node1.__class__, node2.__class__)
        if isinstance(node1, ScalarNode):
            #self.failUnlessEqual(node1.tag, node2.tag)
            self.failUnlessEqual(node1.value, node2.value)
        elif isinstance(node1, SequenceNode):
            self.failUnlessEqual(len(node1.value), len(node2.value))
            for item1, item2 in zip(node1.value, node2.value):
                self._compare(item1, item2)
        elif isinstance(node1, MappingNode):
            self.failUnlessEqual(len(node1.value), len(node2.value))
            items1 = node1.value.items()
            items1.sort(lambda (k1,v1), (k2,v2): cmp((k1.tag,k1.value,v1.tag,v1.value),
                                                    (k2.tag,k2.value,v2.tag,v2.value)))
            items2 = node2.value.items()
            items2.sort(lambda (k1,v1), (k2,v2): cmp((k1.tag,k1.value,v1.tag,v1.value),
                                                    (k2.tag,k2.value,v2.tag,v2.value)))
            for (key1, value1), (key2, value2) in zip(items1, items2):
                self._compare(key1, key2)
                self._compare(value1, value2)

TestResolver.add_tests('testResolver', '.data', '.canonical')

class MyLoader(Loader):
    def construct_sequence(self, node):
        return tuple(Loader.construct_sequence(self, node))

    def construct_mapping(self, node):
        pairs = self.construct_pairs(node)
        pairs.sort()
        return pairs

    def construct_undefined(self, node):
        return self.construct_scalar(node)

MyLoader.add_constructor(u'tag:yaml.org,2002:map', MyLoader.construct_mapping)
MyLoader.add_constructor(None, MyLoader.construct_undefined)

class MyCanonicalLoader(test_appliance.CanonicalLoader):

    def construct_sequence(self, node):
        return tuple(test_appliance.CanonicalLoader.construct_sequence(self, node))

    def construct_mapping(self, node):
        pairs = self.construct_pairs(node)
        pairs.sort()
        return pairs

    def construct_undefined(self, node):
        return self.construct_scalar(node)

MyCanonicalLoader.add_constructor(u'tag:yaml.org,2002:map', MyCanonicalLoader.construct_mapping)
MyCanonicalLoader.add_constructor(None, MyCanonicalLoader.construct_undefined)

class TestConstructor(test_appliance.TestAppliance):

    def _testConstructor(self, test_name, data_filename, canonical_filename):
        data1 = None
        data2 = None
        try:
            data1 = list(load_all(file(data_filename, 'rb'), Loader=MyLoader))
            data2 = list(load_all(file(canonical_filename, 'rb'), Loader=MyCanonicalLoader))
            self.failUnlessEqual(data1, data2)
        except:
            print
            print "DATA1:"
            print file(data_filename, 'rb').read()
            print "DATA2:"
            print file(canonical_filename, 'rb').read()
            print "NATIVES1:", data1
            print "NATIVES2:", data2
            raise

TestConstructor.add_tests('testConstructor', '.data', '.canonical')

class TestParserOnCanonical(test_appliance.TestAppliance):

    def _testParserOnCanonical(self, test_name, canonical_filename):
        events1 = None
        events2 = None
        try:
            events1 = list(parse(file(canonical_filename, 'rb')))
            events2 = list(test_appliance.canonical_parse(file(canonical_filename, 'rb')))
            self._compare(events1, events2)
        except:
            print
            print "DATA:"
            print file(canonical_filename, 'rb').read()
            print "EVENTS1:", events1
            print "EVENTS2:", events2
            raise

    def _compare(self, events1, events2):
        self.failUnlessEqual(len(events1), len(events2))
        for event1, event2 in zip(events1, events2):
            self.failUnlessEqual(event1.__class__, event2.__class__)
            if isinstance(event1, AliasEvent):
                self.failUnlessEqual(event1.anchor, event2.anchor)
            elif isinstance(event1, ScalarEvent):
                self.failUnlessEqual(event1.anchor, event2.anchor)
                self.failUnlessEqual(event1.tag, event2.tag)
                self.failUnlessEqual(event1.value, event2.value)
            if isinstance(event1, CollectionStartEvent):
                self.failUnlessEqual(event1.anchor, event2.anchor)
                self.failUnlessEqual(event1.tag, event2.tag)

TestParserOnCanonical.add_tests('testParserOnCanonical', '.canonical')

