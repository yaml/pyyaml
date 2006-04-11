
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

class MyConstructor(Constructor):
    pass
class MyRepresenter(Representer):
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

    yaml_constructor = MyConstructor
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

MyConstructor.add_constructor("!tag1", construct1)
MyRepresenter.add_representer(MyTestClass1, represent1)

class TestTypeRepresenter(test_appliance.TestAppliance):

    def _testTypes(self, test_name, data_filename, code_filename):
        natives1 = eval(file(code_filename, 'rb').read())
        natives2 = None
        output = None
        try:
            output = dump(natives1, Representer=MyRepresenter)
            natives2 = load(output, Constructor=MyConstructor)
            try:
                self.failUnlessEqual(natives1, natives2)
            except AssertionError:
                if isinstance(natives1, dict):
                    natives1 = natives1.items()
                    natives1.sort()
                    natives1 = repr(natives1)
                    natives2 = natives2.items()
                    natives2.sort()
                    natives2 = repr(natives2)
                if natives1 != natives2:
                    raise
        except:
            print
            print "OUTPUT:"
            print output
            print "NATIVES1:", natives1
            print "NATIVES2:", natives2
            raise

TestTypeRepresenter.add_tests('testTypes', '.data', '.code')

