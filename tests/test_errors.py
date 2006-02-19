
import test_appliance

from yaml.error import YAMLError
from yaml.reader import Reader
from yaml.scanner import Scanner

class TestErrors(test_appliance.TestAppliance):

    def _testErrors(self, test_name, invalid_filename):
        #self._load(invalid_filename)
        self.failUnlessRaises(YAMLError, lambda: self._load(invalid_filename))

    def _testStringErrors(self, test_name, invalid_filename):
        #self._load_string(invalid_filename)
        self.failUnlessRaises(YAMLError, lambda: self._load_string(invalid_filename))

    def _load(self, filename):
        reader = Reader(file(filename, 'rb'))
        scanner = Scanner(reader)
        return list(scanner)

    def _load_string(self, filename):
        reader = Reader(file(filename, 'rb').read())
        scanner = Scanner(reader)
        return list(scanner)

TestErrors.add_tests('testErrors', '.error-message')
TestErrors.add_tests('testStringErrors', '.error-message')

