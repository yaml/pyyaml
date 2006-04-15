
import test_appliance

class TestCanonicalAppliance(test_appliance.TestAppliance):

    def _testCanonicalScanner(self, test_name, canonical_filename):
        data = file(canonical_filename, 'rb').read()
        tokens = list(test_appliance.canonical_scan(data))
        #for token in tokens:
        #    print token

    def _testCanonicalParser(self, test_name, canonical_filename):
        data = file(canonical_filename, 'rb').read()
        event = list(test_appliance.canonical_parse(data))
        #for event in events:
        #    print event

TestCanonicalAppliance.add_tests('testCanonicalScanner', '.canonical')
TestCanonicalAppliance.add_tests('testCanonicalParser', '.canonical')

