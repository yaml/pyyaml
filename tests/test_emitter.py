
import test_appliance, sys, StringIO

from yaml import *
import yaml

class TestEmitterOnCanonical(test_appliance.TestAppliance):

    def _testEmitterOnCanonical(self, test_name, canonical_filename):
        events = list(iter(Parser(Scanner(Reader(file(canonical_filename, 'rb'))))))
        #writer = sys.stdout
        writer = StringIO.StringIO()
        emitter = Emitter(writer)
        #print "-"*30
        #print "ORIGINAL DATA:"
        #print file(canonical_filename, 'rb').read()
        for event in events:
            emitter.emit(event)
        data = writer.getvalue()
        new_events = list(parse(data))
        self.failUnlessEqual(len(events), len(new_events))
        for event, new_event in zip(events, new_events):
            self.failUnlessEqual(event.__class__, new_event.__class__)

TestEmitterOnCanonical.add_tests('testEmitterOnCanonical', '.canonical')

class EventsConstructor(Constructor):

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
        if class_name == 'ScalarEvent':
            mapping.setdefault('value', '')
        value = getattr(yaml, class_name)(**mapping)
        return value

EventsConstructor.add_constructor(None, EventsConstructor.construct_event)

class TestEmitter(test_appliance.TestAppliance):

    def _testEmitter(self, test_name, events_filename):
        events = load_document(file(events_filename, 'rb'), Constructor=EventsConstructor)
        self._dump(events_filename, events)
        writer = StringIO.StringIO()
        emitter = Emitter(writer)
        for event in events:
            emitter.emit(event)
        data = writer.getvalue()
        new_events = list(parse(data))
        self.failUnlessEqual(len(events), len(new_events))
        for event, new_event in zip(events, new_events):
            self.failUnlessEqual(event.__class__, new_event.__class__)

    def _dump(self, events_filename, events):
        writer = sys.stdout
        emitter = Emitter(writer)
        print "="*30
        print "EVENTS:"
        print file(events_filename, 'rb').read()
        print '-'*30
        print "OUTPUT:"
        for event in events:
            emitter.emit(event)
        
TestEmitter.add_tests('testEmitter', '.events')

