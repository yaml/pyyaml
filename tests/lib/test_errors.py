
import yaml, test_emitter

def test_loader_error(error_filename, verbose=False):
    try:
        with open(error_filename, 'rb') as file:
            list(yaml.load_all(file, yaml.FullLoader))
    except yaml.YAMLError as exc:
        if verbose:
            print("%s:" % exc.__class__.__name__, exc)
    else:
        raise AssertionError("expected an exception")

test_loader_error.unittest = ['.loader-error']

def test_loader_error_string(error_filename, verbose=False):
    try:
        with open(error_filename, 'rb') as file:
            list(yaml.load_all(file.read(), yaml.FullLoader))
    except yaml.YAMLError as exc:
        if verbose:
            print("%s:" % exc.__class__.__name__, exc)
    else:
        raise AssertionError("expected an exception")

test_loader_error_string.unittest = ['.loader-error']

def test_loader_error_single(error_filename, verbose=False):
    try:
        with open(error_filename, 'rb') as file:
            yaml.load(file.read(), yaml.FullLoader)
    except yaml.YAMLError as exc:
        if verbose:
            print("%s:" % exc.__class__.__name__, exc)
    else:
        raise AssertionError("expected an exception")

test_loader_error_single.unittest = ['.single-loader-error']

def test_emitter_error(error_filename, verbose=False):
    with open(error_filename, 'rb') as file:
        events = list(yaml.load(file, Loader=test_emitter.EventsLoader))
    try:
        yaml.emit(events)
    except yaml.YAMLError as exc:
        if verbose:
            print("%s:" % exc.__class__.__name__, exc)
    else:
        raise AssertionError("expected an exception")

test_emitter_error.unittest = ['.emitter-error']

def test_dumper_error(error_filename, verbose=False):
    with open(error_filename, 'rb') as file:
        code = file.read()
    try:
        import yaml
        from io import StringIO
        exec(code)
    except yaml.YAMLError as exc:
        if verbose:
            print("%s:" % exc.__class__.__name__, exc)
    else:
        raise AssertionError("expected an exception")

test_dumper_error.unittest = ['.dumper-error']

if __name__ == '__main__':
    import test_appliance
    test_appliance.run(globals())

