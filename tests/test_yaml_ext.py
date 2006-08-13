
import unittest, test_appliance

import _yaml, yaml

class TestCVersion(unittest.TestCase):

    def testCVersion(self):
        self.failUnlessEqual("%s.%s.%s" % _yaml.get_version(), _yaml.get_version_string())

class TestCLoader(test_appliance.TestAppliance):

    def _testCScannerFileInput(self, test_name, data_filename, canonical_filename):
        self._testCScanner(test_name, data_filename, canonical_filename, True)

    def _testCScanner(self, test_name, data_filename, canonical_filename, file_input=False, Loader=yaml.Loader):
        if file_input:
            data = file(data_filename, 'r')
        else:
            data = file(data_filename, 'r').read()
        tokens = list(yaml.scan(data, Loader=Loader))
        ext_tokens = []
        try:
            if file_input:
                data = file(data_filename, 'r')
            for token in yaml.scan(data, Loader=yaml.CLoader):
                ext_tokens.append(token)
            self.failUnlessEqual(len(tokens), len(ext_tokens))
            for token, ext_token in zip(tokens, ext_tokens):
                self.failUnlessEqual(token.__class__, ext_token.__class__)
                self.failUnlessEqual((token.start_mark.index, token.start_mark.line, token.start_mark.column),
                        (ext_token.start_mark.index, ext_token.start_mark.line, ext_token.start_mark.column))
                self.failUnlessEqual((token.end_mark.index, token.end_mark.line, token.end_mark.column),
                        (ext_token.end_mark.index, ext_token.end_mark.line, ext_token.end_mark.column))
                if hasattr(token, 'value'):
                    self.failUnlessEqual(token.value, ext_token.value)
        except:
            print
            print "DATA:"
            print file(data_filename, 'rb').read()
            print "TOKENS:", tokens
            print "EXT_TOKENS:", ext_tokens
            raise

    def _testCParser(self, test_name, data_filename, canonical_filename, Loader=yaml.Loader):
        data = file(data_filename, 'r').read()
        events = list(yaml.parse(data, Loader=Loader))
        ext_events = []
        try:
            for event in yaml.parse(data, Loader=yaml.CLoader):
                ext_events.append(event)
                #print "EVENT:", event
            self.failUnlessEqual(len(events), len(ext_events))
            for event, ext_event in zip(events, ext_events):
                self.failUnlessEqual(event.__class__, ext_event.__class__)
                if hasattr(event, 'anchor'):
                    self.failUnlessEqual(event.anchor, ext_event.anchor)
                if hasattr(event, 'tag'):
                    self.failUnlessEqual(event.tag, ext_event.tag)
                if hasattr(event, 'implicit'):
                    self.failUnlessEqual(event.implicit, ext_event.implicit)
                if hasattr(event, 'value'):
                    self.failUnlessEqual(event.value, ext_event.value)
                if hasattr(event, 'explicit'):
                    self.failUnlessEqual(event.explicit, ext_event.explicit)
                if hasattr(event, 'version'):
                    self.failUnlessEqual(event.version, ext_event.version)
                if hasattr(event, 'tags'):
                    self.failUnlessEqual(event.tags, ext_event.tags)
        except:
            print
            print "DATA:"
            print file(data_filename, 'rb').read()
            print "EVENTS:", events
            print "EXT_EVENTS:", ext_events
            raise

TestCLoader.add_tests('testCScanner', '.data', '.canonical')
TestCLoader.add_tests('testCScannerFileInput', '.data', '.canonical')
TestCLoader.add_tests('testCParser', '.data', '.canonical')

class TestCEmitter(test_appliance.TestAppliance):

    def _testCEmitter(self, test_name, data_filename, canonical_filename, Loader=yaml.Loader):
        data1 = file(data_filename, 'r').read()
        events = list(yaml.parse(data1, Loader=Loader))
        data2 = yaml.emit(events, Dumper=yaml.CDumper)
        ext_events = []
        try:
            for event in yaml.parse(data2):
                ext_events.append(event)
            self.failUnlessEqual(len(events), len(ext_events))
            for event, ext_event in zip(events, ext_events):
                self.failUnlessEqual(event.__class__, ext_event.__class__)
                if hasattr(event, 'anchor'):
                    self.failUnlessEqual(event.anchor, ext_event.anchor)
                if hasattr(event, 'tag'):
                    if not (event.tag in ['!', None] and ext_event.tag in ['!', None]):
                        self.failUnlessEqual(event.tag, ext_event.tag)
                if hasattr(event, 'implicit'):
                    self.failUnlessEqual(event.implicit, ext_event.implicit)
                if hasattr(event, 'value'):
                    self.failUnlessEqual(event.value, ext_event.value)
                if hasattr(event, 'explicit'):
                    self.failUnlessEqual(event.explicit, ext_event.explicit)
                if hasattr(event, 'version'):
                    self.failUnlessEqual(event.version, ext_event.version)
                if hasattr(event, 'tags'):
                    self.failUnlessEqual(event.tags, ext_event.tags)
        except:
            print
            print "DATA1:"
            print data1
            print "DATA2:"
            print data2
            print "EVENTS:", events
            print "EXT_EVENTS:", ext_events
            raise

TestCEmitter.add_tests('testCEmitter', '.data', '.canonical')

yaml.BaseLoader = yaml.CBaseLoader
yaml.SafeLoader = yaml.CSafeLoader
yaml.Loader = yaml.CLoader
yaml.BaseDumper = yaml.CBaseDumper
yaml.SafeDumper = yaml.CSafeDumper
yaml.Dumper = yaml.CDumper
old_scan = yaml.scan
def scan(stream, Loader=yaml.CLoader):
    return old_scan(stream, Loader)
yaml.scan = scan
old_parse = yaml.parse
def parse(stream, Loader=yaml.CLoader):
    return old_parse(stream, Loader)
yaml.parse = parse
old_compose = yaml.compose
def compose(stream, Loader=yaml.CLoader):
    return old_compose(stream, Loader)
yaml.compose = compose
old_compose_all = yaml.compose_all
def compose_all(stream, Loader=yaml.CLoader):
    return old_compose_all(stream, Loader)
yaml.compose_all = compose_all
old_load_all = yaml.load_all
def load_all(stream, Loader=yaml.CLoader):
    return old_load_all(stream, Loader)
yaml.load_all = load_all
old_load = yaml.load
def load(stream, Loader=yaml.CLoader):
    return old_load(stream, Loader)
yaml.load = load
def safe_load_all(stream):
    return yaml.load_all(stream, yaml.CSafeLoader)
yaml.safe_load_all = safe_load_all
def safe_load(stream):
    return yaml.load(stream, yaml.CSafeLoader)
yaml.safe_load = safe_load
old_emit = yaml.emit
def emit(events, stream=None, Dumper=yaml.CDumper, **kwds):
    return old_emit(events, stream, Dumper, **kwds)
yaml.emit = emit
old_serialize_all = yaml.serialize_all
def serialize_all(nodes, stream=None, Dumper=yaml.CDumper, **kwds):
    return old_serialize_all(nodes, stream, Dumper, **kwds)
yaml.serialize_all = serialize_all
old_serialize = yaml.serialize
def serialize(node, stream, Dumper=yaml.CDumper, **kwds):
    return old_serialize(node, stream, Dumper, **kwds)
yaml.serialize = serialize
old_dump_all = yaml.dump_all
def dump_all(documents, stream=None, Dumper=yaml.CDumper, **kwds):
    return old_dump_all(documents, stream, Dumper, **kwds)
yaml.dump_all = dump_all
old_dump = yaml.dump
def dump(data, stream=None, Dumper=yaml.CDumper, **kwds):
    return old_dump(data, stream, Dumper, **kwds)
yaml.dump = dump
def safe_dump_all(documents, stream=None, **kwds):
    return yaml.dump_all(documents, stream, yaml.CSafeDumper, **kwds)
yaml.safe_dump_all = safe_dump_all
def safe_dump(data, stream=None, **kwds):
    return yaml.dump(data, stream, yaml.CSafeDumper, **kwds)
yaml.safe_dump = safe_dump

from test_yaml import *

def main(module='__main__'):
    unittest.main(module)

if __name__ == '__main__':
    main()

