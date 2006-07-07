
import unittest, test_appliance

import _yaml, yaml

class TestExtVersion(unittest.TestCase):

    def testExtVersion(self):
        self.failUnlessEqual("%s.%s.%s" % _yaml.get_version(), _yaml.get_version_string())

class TestExtLoader(test_appliance.TestAppliance):

    def _testExtScanner(self, test_name, data_filename, canonical_filename):
        data = file(data_filename, 'r').read()
        tokens = list(yaml.scan(data))
        ext_tokens = []
        try:
            for token in yaml.scan(data, Loader=yaml.ExtLoader):
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

    def _testExtParser(self, test_name, data_filename, canonical_filename):
        data = file(data_filename, 'r').read()
        events = list(yaml.parse(data))
        ext_events = []
        try:
            for event in yaml.parse(data, Loader=yaml.ExtLoader):
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
        except:
            print
            print "DATA:"
            print file(data_filename, 'rb').read()
            print "EVENTS:", events
            print "EXT_EVENTS:", ext_events
            raise

TestExtLoader.add_tests('testExtScanner', '.data', '.canonical')
TestExtLoader.add_tests('testExtParser', '.data', '.canonical')

def main(module='__main__'):
    unittest.main(module)

if __name__ == '__main__':
    main()

