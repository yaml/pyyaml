
import test_appliance

class TestCanonicalAppliance(test_appliance.TestAppliance):

    def _testCanonicalScanner(self, test_name, canonical_filename):
        data = file(canonical_filename, 'rb').read()
        scanner = test_appliance.CanonicalScanner(canonical_filename, data)
        tokens = scanner.scan()
        #print tokens

    def _testCanonicalParser(self, test_name, canonical_filename):
        data = file(canonical_filename, 'rb').read()
        parser = test_appliance.CanonicalParser(canonical_filename, data)
        documents = parser.parse()
        #for document in documents:
        #    print document

TestCanonicalAppliance.add_tests('testCanonicalScanner', '.canonical')
TestCanonicalAppliance.add_tests('testCanonicalParser', '.canonical')

