
import test_appliance

from yaml import *

class AnInstance:

    def __init__(self, foo, bar):
        self.foo = foo
        self.bar = bar

    def __repr__(self):
        try:
            return "%s(foo=%r, bar=%r)" % (self.__class__.__name__,
                    self.foo, self.bar)
        except RuntimeError:
            return "%s(foo=..., bar=...)" % self.__class__.__name__

class AnInstanceWithState(AnInstance):

    def __getstate__(self):
        return {'attributes': [self.foo, self.bar]}

    def __setstate__(self, state):
        self.foo, self.bar = state['attributes']

class TestRecursive(test_appliance.TestAppliance):

    def _testRecursive(self, test_name, recursive_filename):
        exec file(recursive_filename, 'r').read()
        value1 = value
        output1 = None
        value2 = None
        output2 = None
        try:
            output1 = dump(value1)
            #print "OUTPUT %s:" % test_name
            #print output1
            value2 = load(output1)
            output2 = dump(value2)
            self.failUnlessEqual(output1, output2)
        except:
            print "VALUE1:", value1
            print "VALUE2:", value2
            print "OUTPUT1:"
            print output1
            print "OUTPUT2:"
            print output2
            raise

TestRecursive.add_tests('testRecursive', '.recursive')

