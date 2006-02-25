
import test_appliance
try:
    import datetime
except ImportError:
    pass

from yaml import *

class MyConstructor(Constructor):
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

MyConstructor.add_constructor("!tag1", construct1)

class MyTestClass2(MyTestClass1, YAMLObject):

    yaml_constructor = MyConstructor
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

class TestTypes(test_appliance.TestAppliance):

    def _testTypes(self, test_name, data_filename, code_filename):
        natives1 = None
        natives2 = None
        try:
            constructor1 = MyConstructor(Resolver(Composer(Parser(Scanner(Reader(file(data_filename, 'rb')))))))
            natives1 = list(iter(constructor1))
            if len(natives1) == 1:
                natives1 = natives1[0]
            natives2 = eval(file(code_filename, 'rb').read())
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
            print "DATA:"
            print file(data_filename, 'rb').read()
            print "CODE:"
            print file(code_filename, 'rb').read()
            print "NATIVES1:", natives1
            print "NATIVES2:", natives2
            raise

TestTypes.add_tests('testTypes', '.data', '.code')

