
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
class MyDumper(Dumper):
    pass

class MyTestClass1(object):

    def __init__(self, x, y=0, z=0):
        self.x = x
        self.y = y
        self.z = z

    def __eq__(self, other):
        if isinstance(other, MyTestClass1):
            return self.__class__, self.__dict__ == other.__class__, other.__dict__
        else:
            return False

def construct1(constructor, node):
    mapping = constructor.construct_mapping(node)
    return MyTestClass1(**mapping)
def represent1(representer, native):
    return representer.represent_mapping("!tag1", native.__dict__)

class MyTestClass2(MyTestClass1, YAMLObject):

    yaml_loader = MyLoader
    yaml_dumper = MyDumper
    yaml_tag = "!tag2"

    def from_yaml(cls, constructor, node):
        x = constructor.construct_yaml_int(node)
        return cls(x=x)
    from_yaml = classmethod(from_yaml)

    def to_yaml(cls, representer, native):
        return representer.represent_scalar(cls.yaml_tag, str(native.x))
    to_yaml = classmethod(to_yaml)

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

    def to_yaml(cls, representer, native):
        return representer.represent_mapping(cls.yaml_tag, native.__dict__)
    to_yaml = classmethod(to_yaml)

MyLoader.add_constructor("!tag1", construct1)
MyDumper.add_representer(MyTestClass1, represent1)

class YAMLObject1(YAMLObject):
    yaml_loader = MyLoader
    yaml_dumper = MyDumper
    yaml_tag = '!foo'
    yaml_flow_style = True

    def __init__(self, my_parameter=None, my_another_parameter=None):
        self.my_parameter = my_parameter
        self.my_another_parameter = my_another_parameter

    def __eq__(self, other):
        if isinstance(other, YAMLObject1):
            return self.__class__, self.__dict__ == other.__class__, other.__dict__
        else:
            return False

class TestTypeRepresenter(test_appliance.TestAppliance):

    def _testTypes(self, test_name, data_filename, code_filename):
        data1 = eval(file(code_filename, 'rb').read())
        data2 = None
        output = None
        try:
            output = dump(data1, Dumper=MyDumper)
            data2 = load(output, Loader=MyLoader)
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
            print "OUTPUT:"
            print output
            print "NATIVES1:", data1
            print "NATIVES2:", data2
            raise

TestTypeRepresenter.add_tests('testTypes', '.data', '.code')

