import yaml
import sys
import functools

_vowels = set(('a','e','i','o','u'))

def sort_keys_vowels_first(a, b):
    # params are (key,value) pairs
    a=a[0]
    b=b[0]
    if (a in _vowels) == (b in _vowels):
        return (a>b)-(a<b) # cmp(a,b)
    else:
        return (b in _vowels)*2-1

def test_sort_keys_function(input_filename, sorted_filename, verbose=False):
    with open(input_filename, 'rb') as file:
        input = file.read().decode('utf-8')
    with open(sorted_filename, 'rb') as file:
        sorted = file.read().decode('utf-8')
    data = yaml.load(input, Loader=yaml.FullLoader)
    dump_sorted = yaml.dump(data, default_flow_style=False, sort_keys=functools.cmp_to_key(sort_keys_vowels_first))
    dump_unsorted = yaml.dump(data, default_flow_style=False, sort_keys=False)
    dump_unsorted_safe = yaml.dump(data, default_flow_style=False, sort_keys=False, Dumper=yaml.SafeDumper)
    if verbose:
        print("INPUT:")
        print(input)
        print("DATA:")
        print(data)

    assert dump_sorted == sorted

    if sys.version_info>=(3,7):
        assert dump_unsorted == input
        assert dump_unsorted_safe == input

test_sort_keys_function.unittest = ['.sort_vowels_first', '.sorted_vowels_first']

if __name__ == '__main__':
    import test_appliance
    test_appliance.run(globals())
