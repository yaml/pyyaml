
import test_appliance, sys, StringIO

from yaml import *
import yaml

class TestEmitter(test_appliance.TestAppliance):

    def _testEmitterOnData(self, test_name, canonical_filename, data_filename):
        self._testEmitter(test_name, data_filename)

    def _testEmitterOnCanonicalNormally(self, test_name, canonical_filename):
        self._testEmitter(test_name, canonical_filename, False)

    def _testEmitterOnCanonicalCanonically(self, test_name, canonical_filename):
        self._testEmitter(test_name, canonical_filename, True)

    def _testEmitter(self, test_name, filename, canonical=None):
        events = list(parse(file(filename, 'rb')))
        #self._dump(filename, events, canonical)
        stream = StringIO.StringIO()
        emit(events, stream, canonical=canonical)
        data = stream.getvalue()
        new_events = list(parse(data))
        for event, new_event in zip(events, new_events):
            self.failUnlessEqual(event.__class__, new_event.__class__)
            if isinstance(event, NodeEvent):
                self.failUnlessEqual(event.anchor, new_event.anchor)
            if isinstance(event, CollectionStartEvent):
                self.failUnlessEqual(event.tag, new_event.tag)
            if isinstance(event, ScalarEvent):
                #self.failUnlessEqual(event.implicit, new_event.implicit)
                if True not in event.implicit+new_event.implicit:
                    self.failUnlessEqual(event.tag, new_event.tag)
                self.failUnlessEqual(event.value, new_event.value)

    def _dump(self, filename, events, canonical):
        print "="*30
        print "ORIGINAL DOCUMENT:"
        print file(filename, 'rb').read()
        print '-'*30
        print "EMITTED DOCUMENT:"
        emit(events, sys.stdout, canonical=canonical)
        
TestEmitter.add_tests('testEmitterOnData', '.canonical', '.data')
TestEmitter.add_tests('testEmitterOnCanonicalNormally', '.canonical')
TestEmitter.add_tests('testEmitterOnCanonicalCanonically', '.canonical')

class EventsLoader(Loader):

    def construct_event(self, node):
        if isinstance(node, ScalarNode):
            mapping = {}
        else:
            mapping = self.construct_mapping(node)
        class_name = str(node.tag[1:])+'Event'
        if class_name in ['AliasEvent', 'ScalarEvent', 'SequenceStartEvent', 'MappingStartEvent']:
            mapping.setdefault('anchor', None)
        if class_name in ['ScalarEvent', 'SequenceStartEvent', 'MappingStartEvent']:
            mapping.setdefault('tag', None)
        if class_name in ['SequenceStartEvent', 'MappingStartEvent']:
            mapping.setdefault('implicit', True)
        if class_name == 'ScalarEvent':
            mapping.setdefault('implicit', (False, True))
            mapping.setdefault('value', '')
        value = getattr(yaml, class_name)(**mapping)
        return value

EventsLoader.add_constructor(None, EventsLoader.construct_event)

class TestEmitterEvents(test_appliance.TestAppliance):

    def _testEmitterEvents(self, test_name, events_filename):
        events = list(load(file(events_filename, 'rb'), Loader=EventsLoader))
        #self._dump(events_filename, events)
        stream = StringIO.StringIO()
        emit(events, stream)
        data = stream.getvalue()
        new_events = list(parse(data))
        self.failUnlessEqual(len(events), len(new_events))
        for event, new_event in zip(events, new_events):
            self.failUnlessEqual(event.__class__, new_event.__class__)
            if isinstance(event, NodeEvent):
                self.failUnlessEqual(event.anchor, new_event.anchor)
            if isinstance(event, CollectionStartEvent):
                self.failUnlessEqual(event.tag, new_event.tag)
            if isinstance(event, ScalarEvent):
                self.failUnless(event.implicit == new_event.implicit
                        or event.tag == new_event.tag)
                self.failUnlessEqual(event.value, new_event.value)

    def _dump(self, events_filename, events):
        print "="*30
        print "EVENTS:"
        print file(events_filename, 'rb').read()
        print '-'*30
        print "OUTPUT:"
        emit(events, sys.stdout)
        
TestEmitterEvents.add_tests('testEmitterEvents', '.events')

