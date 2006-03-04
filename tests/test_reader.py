
import test_appliance
from yaml.reader import Reader, ReaderError

import codecs

class TestReaderErrors(test_appliance.TestAppliance):

    def _testReaderUnicodeErrors(self, test_name, stream_filename):
        for encoding in ['utf-8', 'utf-16-le', 'utf-16-be']:
            try:
                data = unicode(file(stream_filename, 'rb').read(), encoding)
                break
            except:
                pass
        else:
            return
        #self._load(data)
        self.failUnlessRaises(ReaderError,
                lambda: self._load(data))
        #self._load(codecs.open(stream_filename, encoding=encoding))
        self.failUnlessRaises(ReaderError,
                lambda: self._load(codecs.open(stream_filename, encoding=encoding)))

    def _testReaderStringErrors(self, test_name, stream_filename):
        data = file(stream_filename, 'rb').read()
        #self._load(data)
        self.failUnlessRaises(ReaderError, lambda: self._load(data))

    def _testReaderFileErrors(self, test_name, stream_filename):
        data = file(stream_filename, 'rb')
        #self._load(data)
        self.failUnlessRaises(ReaderError, lambda: self._load(data))

    def _load(self, data):
        stream = Reader(data)
        while stream.peek() != u'\0':
            stream.forward()

TestReaderErrors.add_tests('testReaderUnicodeErrors', '.stream-error')
TestReaderErrors.add_tests('testReaderStringErrors', '.stream-error')
TestReaderErrors.add_tests('testReaderFileErrors', '.stream-error')


