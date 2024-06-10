import yaml

def test_dump(verbose=False):
    assert yaml.dump(['foo'])
test_dump.unittest = True

def test_load_no_loader(verbose=False):
    try:
        yaml.load("- foo\n")
    except TypeError:
        return True
    assert(False, "load() require Loader=...")
test_load_no_loader.unittest = True

def test_load_safeloader(verbose=False):
    assert yaml.load("- foo\n", Loader=yaml.SafeLoader)
test_load_safeloader.unittest = True

if __name__ == '__main__':
    import sys, test_load
    sys.modules['test_load'] = sys.modules['__main__']
    import test_appliance
    test_appliance.run(globals())
