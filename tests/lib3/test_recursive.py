
import yaml

# We could use something like @loaderdumper.register_class
# instead of the unsafe loader.
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

def test_recursive(recursive_filename, verbose=False):
    context = globals().copy()
    exec(open(recursive_filename, 'rb').read(), context)
    value1 = context['value']
    output1 = None
    value2 = None
    output2 = None
    try:
        output1 = yaml.dump(value1)
        value2 = yaml.unsafe_load(output1)
        output2 = yaml.dump(value2)
        assert output1 == output2, (output1, output2)
    finally:
        if verbose:
            print("VALUE1:", value1)
            print("VALUE2:", value2)
            print("OUTPUT1:")
            print(output1)
            print("OUTPUT2:")
            print(output2)

test_recursive.unittest = ['.recursive']

def test_recursive_12(recursive_filename, verbose=False):
    context = globals().copy()
    exec(open(recursive_filename, 'rb').read(), context)
    value1 = context['value']
    output1 = None
    value2 = None
    output2 = None
    # ruyaml.register_class(AnInstanceWithState)
    try:
        output1 = yaml.dump(value1, Dumper=yaml.YAML12Dumper, sort_keys=False)
        value2 = yaml.load(output1, Loader=yaml.YAML12UnsafeLoader)
        output2 = yaml.dump(value2, Dumper=yaml.YAML12Dumper, sort_keys=False)
        # raise Exception(value1, output1, value2, output2)
        assert output1 == output2, (output1, output2)
    finally:
        if verbose:
            print("VALUE1:", value1)
            print("VALUE2:", value2)
            print("OUTPUT1:")
            print(output1)
            print("OUTPUT2:")
            print(output2)

test_recursive_12.unittest = ['.recursive']

if __name__ == '__main__':
    import test_appliance
    test_appliance.run(globals())

