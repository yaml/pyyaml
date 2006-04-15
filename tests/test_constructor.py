
import test_appliance
try:
    import datetime
except ImportError:
    pass
try:
    set
except NameError:
    from sets import Set as set

from yaml import *

class MyLoader(Loader):
    pass

class MyTestClass1:

    def __init__(self, x, y=0, z=0):
        self.x = x
        self.y = y
        self.z = z

    def __eq__(self, other):
        return self.__class__, self.__dict__ == other.__class__, other.__dict__

def construct1(constructor, node):
    mapping = constructor.construct_mapping(node)
    return MyTestClass1(**mapping)

MyLoader.add_constructor("!tag1", construct1)

class MyTestClass2(MyTestClass1, YAMLObject):

    yaml_loader = MyLoader
    yaml_tag = "!tag2"

    def from_yaml(cls, constructor, node):
        x = constructor.construct_yaml_int(node)
        return cls(x=x)
    from_yaml = classmethod(from_yaml)

class MyTestClass3(MyTestClass2):

    yaml_tag = "!tag3"

    def from_yaml(cls, constructor, node):
        mapping = constructor.construct_mapping(node)
        if '=' in mapping:
            x = mapping['=']
            del mapping['=']
            mapping['x'] = x
        return cls(**mapping)
    from_yaml = classmethod(from_yaml)

class YAMLObject1(YAMLObject):
    yaml_loader = MyLoader
    yaml_tag = '!foo'

    def __init__(self, my_parameter=None, my_another_parameter=None):
        self.my_parameter = my_parameter
        self.my_another_parameter = my_another_parameter

    def __eq__(self, other):
        if isinstance(other, YAMLObject1):
            return self.__class__, self.__dict__ == other.__class__, other.__dict__
        else:
            return False

class TestTypes(test_appliance.TestAppliance):

    def _testTypes(self, test_name, data_filename, code_filename):
        data1 = None
        data2 = None
        try:
            data1 = list(load_all(file(data_filename, 'rb'), Loader=MyLoader))
            if len(data1) == 1:
                data1 = data1[0]
            data2 = eval(file(code_filename, 'rb').read())
            try:
                self.failUnlessEqual(data1, data2)
            except AssertionError:
                if isinstance(data1, dict):
                    data1 = data1.items()
                    data1.sort()
                    data1 = repr(data1)
                    data2 = data2.items()
                    data2.sort()
                    data2 = repr(data2)
                if data1 != data2:
                    raise
        except:
            print
            print "DATA:"
            print file(data_filename, 'rb').read()
            print "CODE:"
            print file(code_filename, 'rb').read()
            print "NATIVES1:", data1
            print "NATIVES2:", data2
            raise

TestTypes.add_tests('testTypes', '.data', '.code')

