
import test_appliance
import test_emitter

import StringIO

from yaml import *

class TestErrors(test_appliance.TestAppliance):

    def _testLoaderErrors(self, test_name, invalid_filename):
        #self._load(invalid_filename)
        self.failUnlessRaises(YAMLError, lambda: self._load(invalid_filename))

    def _testLoaderStringErrors(self, test_name, invalid_filename):
        #self._load_string(invalid_filename)
        self.failUnlessRaises(YAMLError, lambda: self._load_string(invalid_filename))

    def _testLoaderSingleErrors(self, test_name, invalid_filename):
        #self._load_single(invalid_filename)
        self.failUnlessRaises(YAMLError, lambda: self._load_single(invalid_filename))

    def _testEmitterErrors(self, test_name, invalid_filename):
        events = list(load(file(invalid_filename, 'rb').read(),
            Loader=test_emitter.EventsLoader))
        self.failUnlessRaises(YAMLError, lambda: self._emit(events))

    def _testDumperErrors(self, test_name, invalid_filename):
        code = file(invalid_filename, 'rb').read()
        self.failUnlessRaises(YAMLError, lambda: self._dump(code))

    def _dump(self, code):
        try:
            exec code
        except YAMLError, exc:
            #print '.'*70
            #print "%s:" % exc.__class__.__name__, exc
            raise

    def _emit(self, events):
        try:
            emit(events)
        except YAMLError, exc:
            #print '.'*70
            #print "%s:" % exc.__class__.__name__, exc
            raise

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

    def _load_single(self, filename):
        try:
            return load(file(filename, 'rb').read())
        except YAMLError, exc:
        #except ScannerError, exc:
        #except ParserError, exc:
        #except ComposerError, exc:
        #except ConstructorError, exc:
            #print '.'*70
            #print "%s:" % filename
            #print "%s:" % exc.__class__.__name__, exc
            raise

TestErrors.add_tests('testLoaderErrors', '.loader-error')
TestErrors.add_tests('testLoaderStringErrors', '.loader-error')
TestErrors.add_tests('testLoaderSingleErrors', '.single-loader-error')
TestErrors.add_tests('testEmitterErrors', '.emitter-error')
TestErrors.add_tests('testDumperErrors', '.dumper-error')

