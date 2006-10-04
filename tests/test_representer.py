
import test_appliance
from test_constructor import *

from yaml import *

class TestRepresenterTypes(test_appliance.TestAppliance):

    def _testTypesUnicode(self, test_name, data_filename, code_filename):
        return self._testTypes(test_name, data_filename, code_filename, allow_unicode=True)

    def _testTypes(self, test_name, data_filename, code_filename, allow_unicode=False):
        data1 = eval(file(code_filename, 'rb').read())
        data2 = None
        output = None
        try:
            output = dump(data1, Dumper=MyDumper, allow_unicode=allow_unicode)
            data2 = load(output, Loader=MyLoader)
            self.failUnlessEqual(type(data1), type(data2))
            try:
                self.failUnlessEqual(data1, data2)
            except (AssertionError, TypeError):
                if isinstance(data1, dict):
                    data1 = [(repr(key), value) for key, value in data1.items()]
                    data1.sort()
                    data1 = repr(data1)
                    data2 = [(repr(key), value) for key, value in data2.items()]
                    data2.sort()
                    data2 = repr(data2)
                    if data1 != data2:
                        raise
                elif isinstance(data1, list):
                    self.failUnlessEqual(type(data1), type(data2))
                    self.failUnlessEqual(len(data1), len(data2))
                    for item1, item2 in zip(data1, data2):
                        if (item1 != item1 or (item1 == 0.0 and item1 == 1.0)) and  \
                                (item2 != item2 or (item2 == 0.0 and item2 == 1.0)):
                            continue
                        if isinstance(item1, datetime.datetime) \
                                and isinstance(item2, datetime.datetime):
                            self.failUnlessEqual(item1.microsecond,
                                    item2.microsecond)
                        if isinstance(item1, datetime.datetime):
                            item1 = item1.utctimetuple()
                        if isinstance(item2, datetime.datetime):
                            item2 = item2.utctimetuple()
                        self.failUnlessEqual(item1, item2)
                else:
                    raise
        except:
            print
            print "OUTPUT:"
            print output
            print "NATIVES1:", data1
            print "NATIVES2:", data2
            raise

TestRepresenterTypes.add_tests('testTypes', '.data', '.code')
TestRepresenterTypes.add_tests('testTypesUnicode', '.data', '.code')

