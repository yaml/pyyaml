
import test_appliance

class TestCanonicalAppliance(test_appliance.TestAppliance):

    def _testCanonicalScanner(self, test_name, canonical_filename):
        data = file(canonical_filename, 'rb').read()
        scanner = test_appliance.CanonicalScanner(data)
        tokens = scanner.scan()
        #for token in tokens:
        #    print token

    def _testCanonicalParser(self, test_name, canonical_filename):
        data = file(canonical_filename, 'rb').read()
        parser = test_appliance.CanonicalParser(data)
        events = parser.parse()
        #for event in events:
        #    print event

TestCanonicalAppliance.add_tests('testCanonicalScanner', '.canonical')
TestCanonicalAppliance.add_tests('testCanonicalParser', '.canonical')

