import yaml
import os
import sys
import pprint

def check_bool(value, expected):
    if expected == 'false()' and value is False:
        return 1
    if expected == 'true()' and value is True:
        return 1
    print(value)
    print(expected)
    return 0

def check_int(value, expected):
    if (int(expected) == value):
        return 1
    print(value)
    print(expected)
    return 0

def check_float(value, expected):
    if expected == 'inf()':
        if value == float("inf"):
          return 1
    elif expected == 'inf-neg()':
        if value == float("-inf"):
          return 1
    elif expected == 'nan()':
        if value != value or (value == 0.0 and value == 1.0):
          return 1
    elif (float(expected) == value):
        return 1
    else:
        print(value)
        print(expected)
        return 0

def check_str(value, expected):
    if value == expected:
        return 1
    print(value)
    print(expected)
    return 0


def _fail(input, test):
    print("Input: >>" + input + "<<");
    print(test);

# The tests/data/yaml11.schema file is copied from
# https://github.com/perlpunk/yaml-test-schema/blob/dev/data/schema-yaml11.yaml
def test_implicit_resolver(data_filename, skip_filename, verbose=False):
    types = {
        'str':   [str,   check_str],
        'int':   [int,   check_int],
        'float': [float, check_float],
        'inf':   [float, check_float],
        'nan':   [float, check_float],
        'bool':  [bool,  check_bool],
    }
    loaders = {
        'yaml11': yaml.SafeLoader,
        'core': yaml.CoreLoader,
        'json': yaml.JSONLoader,
    }
    dumpers = {
        'yaml11': yaml.SafeDumper,
        'core': yaml.CoreDumper,
        'json': yaml.JSONDumper,
    }
    loadername = os.path.splitext(os.path.basename(data_filename))[0]
    print('==================')
    print(loadername)
#    loadername = 'yaml11'
    skipdata = yaml.load(open(skip_filename, 'rb'), Loader=yaml.SafeLoader)
    skip_load = skipdata['load'];
    skip_dump = skipdata['dump'];
    if verbose:
        print(skip_load)
    tests = yaml.load(open(data_filename, 'rb'), Loader=yaml.SafeLoader)

    i = 0;
    fail = 0;
    for input, test in sorted(tests.items()):
        if verbose:
            print('-------------------- ' + str(i))
        test = tests[input]
        i += 1

        # Skip known loader bugs
        if input in skip_load:
            continue

        exp_type = test[0];
        data     = test[1];
        exp_dump = test[2];

        # Test loading
        try:
            doc_input = """---\n""" + input
            loaded = yaml.load(doc_input, Loader=loaders[loadername])
        except:
            print("Error:", sys.exc_info()[0], '(', sys.exc_info()[1], ')')
            fail+=1
            _fail(input, test)
            continue

        if verbose:
            print(input)
            print(test)
            print(loaded)
            print(type(loaded))

        if exp_type == 'null':
            if loaded is None:
                pass
            else:
                fail+=1
                _fail(input, test)
        else:
            t = types[exp_type][0]
            code = types[exp_type][1]

            if isinstance(loaded, t):
                if code(loaded, data):
                    pass
                else:
                    fail+=1
                    print("Expected data: >>" + str(data) + "<< Got: >>" + str(loaded) + "<<");
                    _fail(input, test)
            else:
                fail+=1
                print("Expected type: >>" + exp_type + "<< Got: >>" + str(loaded) + "<<");
                _fail(input, test)

        # Skip known dumper bugs
        if input in skip_dump:
            continue

        dump = yaml.dump(loaded, explicit_end=False, Dumper=dumpers[loadername])
        # strip trailing newlines and footers
        if (dump == '...\n'):
            dump = ''
        if dump.endswith('\n...\n'):
            dump = dump[:-5]
        if dump.endswith('\n'):
            dump = dump[:-1]
        if dump == exp_dump:
            pass
        else:
            print("Compare: >>" + dump + "<< >>" + exp_dump + "<<");
            print(skip_dump)
            print(input)
            print(test)
            print(loaded)
            print(type(loaded))
            fail+=1
            _fail(input, test)

#        if i >= 80:
#            break

    if fail > 0:
        print("Failed " + str(fail) + " / " + str(i) + " tests");
        assert(False)
    else:
        print("Passed " + str(i) + " tests");
    print("Skipped " + str(len(skip_load)) + " load tests");
    print("Skipped " + str(len(skip_dump)) + " dump tests");

test_implicit_resolver.unittest = ['.schema', '.schema-skip']

if __name__ == '__main__':
    import test_appliance
    test_appliance.run(globals())

