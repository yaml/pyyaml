
import test_appliance

import datetime
try:
    set
except NameError:
    from sets import Set as set

from yaml import *

import yaml.tokens

class MyLoader(Loader):
    pass
class MyDumper(Dumper):
    pass

class MyTestClass1:

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

add_constructor("!tag1", construct1, Loader=MyLoader)
add_representer(MyTestClass1, represent1, Dumper=MyDumper)

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

class YAMLObject1(YAMLObject):

    yaml_loader = MyLoader
    yaml_dumper = MyDumper
    yaml_tag = '!foo'

    def __init__(self, my_parameter=None, my_another_parameter=None):
        self.my_parameter = my_parameter
        self.my_another_parameter = my_another_parameter

    def __eq__(self, other):
        if isinstance(other, YAMLObject1):
            return self.__class__, self.__dict__ == other.__class__, other.__dict__
        else:
            return False

class YAMLObject2(YAMLObject):

    yaml_loader = MyLoader
    yaml_dumper = MyDumper
    yaml_tag = '!bar'

    def __init__(self, foo=1, bar=2, baz=3):
        self.foo = foo
        self.bar = bar
        self.baz = baz

    def __getstate__(self):
        return {1: self.foo, 2: self.bar, 3: self.baz}

    def __setstate__(self, state):
        self.foo = state[1]
        self.bar = state[2]
        self.baz = state[3]

    def __eq__(self, other):
        if isinstance(other, YAMLObject2):
            return self.__class__, self.__dict__ == other.__class__, other.__dict__
        else:
            return False

class AnObject(object):

    def __new__(cls, foo=None, bar=None, baz=None):
        self = object.__new__(cls)
        self.foo = foo
        self.bar = bar
        self.baz = baz
        return self

    def __cmp__(self, other):
        return cmp((type(self), self.foo, self.bar, self.baz),
                (type(other), other.foo, other.bar, other.baz))

    def __eq__(self, other):
        return type(self) is type(other) and    \
                (self.foo, self.bar, self.baz) == (other.foo, other.bar, other.baz)

class AnInstance:

    def __init__(self, foo=None, bar=None, baz=None):
        self.foo = foo
        self.bar = bar
        self.baz = baz

    def __cmp__(self, other):
        return cmp((type(self), self.foo, self.bar, self.baz),
                (type(other), other.foo, other.bar, other.baz))

    def __eq__(self, other):
        return type(self) is type(other) and    \
                (self.foo, self.bar, self.baz) == (other.foo, other.bar, other.baz)

class AState(AnInstance):

    def __getstate__(self):
        return {
            '_foo': self.foo,
            '_bar': self.bar,
            '_baz': self.baz,
        }

    def __setstate__(self, state):
        self.foo = state['_foo']
        self.bar = state['_bar']
        self.baz = state['_baz']

class ACustomState(AnInstance):

    def __getstate__(self):
        return (self.foo, self.bar, self.baz)

    def __setstate__(self, state):
        self.foo, self.bar, self.baz = state

class InitArgs(AnInstance):

    def __getinitargs__(self):
        return (self.foo, self.bar, self.baz)

    def __getstate__(self):
        return {}

class InitArgsWithState(AnInstance):

    def __getinitargs__(self):
        return (self.foo, self.bar)

    def __getstate__(self):
        return self.baz

    def __setstate__(self, state):
        self.baz = state

class NewArgs(AnObject):

    def __getnewargs__(self):
        return (self.foo, self.bar, self.baz)

    def __getstate__(self):
        return {}

class NewArgsWithState(AnObject):

    def __getnewargs__(self):
        return (self.foo, self.bar)

    def __getstate__(self):
        return self.baz

    def __setstate__(self, state):
        self.baz = state

class Reduce(AnObject):

    def __reduce__(self):
        return self.__class__, (self.foo, self.bar, self.baz)

class ReduceWithState(AnObject):

    def __reduce__(self):
        return self.__class__, (self.foo, self.bar), self.baz

    def __setstate__(self, state):
        self.baz = state

class MyInt(int):

    def __eq__(self, other):
        return type(self) is type(other) and int(self) == int(other)

class MyList(list):

    def __init__(self, n=1):
        self.extend([None]*n)

    def __eq__(self, other):
        return type(self) is type(other) and list(self) == list(other)

class MyDict(dict):

    def __init__(self, n=1):
        for k in range(n):
            self[k] = None

    def __eq__(self, other):
        return type(self) is type(other) and dict(self) == dict(other)

class FixedOffset(datetime.tzinfo):

    def __init__(self, offset, name):
        self.__offset = datetime.timedelta(minutes=offset)
        self.__name = name

    def utcoffset(self, dt):
        return self.__offset

    def tzname(self, dt):
        return self.__name

    def dst(self, dt):
        return datetime.timedelta(0)


def execute(code):
    exec code
    return value

class TestConstructorTypes(test_appliance.TestAppliance):

    def _testTypes(self, test_name, data_filename, code_filename):
        data1 = None
        data2 = None
        try:
            data1 = list(load_all(file(data_filename, 'rb'), Loader=MyLoader))
            if len(data1) == 1:
                data1 = data1[0]
            data2 = eval(file(code_filename, 'rb').read())
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
            print "DATA:"
            print file(data_filename, 'rb').read()
            print "CODE:"
            print file(code_filename, 'rb').read()
            print "NATIVES1:", data1
            print "NATIVES2:", data2
            raise

TestConstructorTypes.add_tests('testTypes', '.data', '.code')

