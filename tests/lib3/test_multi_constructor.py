import yaml
import pprint
import sys

def _load_code(expression):
    return eval(expression)

def myconstructor1(constructor, tag, node):
    seq = constructor.construct_sequence(node)
    return {tag: seq }

def myconstructor2(constructor, tag, node):
    seq = constructor.construct_sequence(node)
    string = ''
    try:
        i = tag.index('!') + 1
    except:
        try:
            i = tag.rindex(':') + 1
        except:
            pass
    if i >= 0:
        tag = tag[i:]
    return { tag: seq }

class Multi1(yaml.FullLoader):
    pass
class Multi2(yaml.FullLoader):
    pass

def test_multi_constructor(input_filename, code_filename, verbose=False):
    input = open(input_filename, 'rb').read().decode('utf-8')
    native = _load_code(open(code_filename, 'rb').read())

    # default multi constructor for ! and !! tags
    Multi1.add_multi_constructor('!', myconstructor1)
    Multi1.add_multi_constructor('tag:yaml.org,2002:', myconstructor1)

    data = yaml.load(input, Loader=Multi1)
    if verbose:
        print('Multi1:')
        print(data)
        print(native)
    assert(data == native)


    # default multi constructor for all tags
    Multi2.add_multi_constructor(None, myconstructor2)

    data = yaml.load(input, Loader=Multi2)
    if verbose:
        print('Multi2:')
        print(data)
        print(native)
    assert(data == native)


test_multi_constructor.unittest = ['.multi', '.code']

if __name__ == '__main__':
    import test_appliance
    test_appliance.run(globals())

