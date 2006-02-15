
import test_appliance
from yaml.stream import Stream, StreamError

class TestStreamErrors(test_appliance.TestAppliance):

    def _testStreamUnicodeErrors(self, test_name, stream_filename):
        try:
            data = unicode(file(stream_filename, 'rb').read(), 'utf-8')
        except:
            return
        self.failUnlessRaises(StreamError, lambda: self._load(stream_filename, data))

    def _testStreamStringErrors(self, test_name, stream_filename):
        data = file(stream_filename, 'rb').read()
        self.failUnlessRaises(StreamError, lambda: self._load(stream_filename, data))

    def _testStreamFileErrors(self, test_name, stream_filename):
        data = file(stream_filename, 'rb')
        self.failUnlessRaises(StreamError, lambda: self._load(stream_filename, data))

    def _load(self, stream_filename, data):
        stream = Stream(stream_filename, data)
        while stream.peek() != u'\0':
            stream.forward()

TestStreamErrors.add_tests('testStreamUnicodeErrors', '.stream-error')
TestStreamErrors.add_tests('testStreamStringErrors', '.stream-error')
TestStreamErrors.add_tests('testStreamFileErrors', '.stream-error')


