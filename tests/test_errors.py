
import test_appliance

from yaml import *

class TestErrors(test_appliance.TestAppliance):

    def _testErrors(self, test_name, invalid_filename):
        #self._load(invalid_filename)
        self.failUnlessRaises(YAMLError, lambda: self._load(invalid_filename))

    def _testStringErrors(self, test_name, invalid_filename):
        #self._load_string(invalid_filename)
        self.failUnlessRaises(YAMLError, lambda: self._load_string(invalid_filename))

    def _load(self, filename):
        try:
            return list(load_all(file(filename, 'rb')))
        except YAMLError, exc:
        #except ScannerError, exc:
        #except ParserError, exc:
        #except ComposerError, exc:
        #except ConstructorError, exc:
            #print '.'*70
            #print "%s:" % exc.__class__.__name__, exc
            raise

    def _load_string(self, filename):
        try:
            return list(load_all(file(filename, 'rb').read()))
        except YAMLError, exc:
        #except ScannerError, exc:
        #except ParserError, exc:
        #except ComposerError, exc:
        #except ConstructorError, exc:
            #print '.'*70
            #print "%s:" % filename
            #print "%s:" % exc.__class__.__name__, exc
            raise

TestErrors.add_tests('testErrors', '.error-message')
TestErrors.add_tests('testStringErrors', '.error-message')

