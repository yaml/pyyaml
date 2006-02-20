
import test_appliance

class TestSyck(test_appliance.TestAppliance):

    def _testSyckOnTokenTests(self, test_name, data_filename, tokens_filename):
        try:
            syck.parse(file(data_filename, 'rb'))
        except:
            print
            print "DATA:"
            print file(data_filename, 'rb').read()
            raise

    def _testSyckOnCanonicalTests(self, test_name, data_filename, canonical_filename):
        try:
            syck.parse(file(data_filename, 'rb'))
        except:
            print
            print "DATA:"
            print file(data_filename, 'rb').read()
            raise

try:
    import syck
    #TestSyck.add_tests('testSyckOnTokenTests', '.data', '.tokens')
    #TestSyck.add_tests('testSyckOnCanonicalTests', '.data', '.canonical')
except ImportError:
    pass

