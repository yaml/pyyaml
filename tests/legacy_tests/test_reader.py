
import yaml.reader

def _run_reader(data, verbose):
    try:
        stream = yaml.reader.Reader(data)
        while stream.peek() != '\0':
            stream.forward()
    except yaml.reader.ReaderError as exc:
        if verbose:
            print(exc)
    else:
        raise AssertionError("expected an exception")

def test_stream_error(error_filename, verbose=False):
    with open(error_filename, 'rb') as file:
        _run_reader(file, verbose)
    with open(error_filename, 'rb') as file:
        _run_reader(file.read(), verbose)
    for encoding in ['utf-8', 'utf-16-le', 'utf-16-be']:
        try:
            with open(error_filename, 'rb') as file:
                data = file.read().decode(encoding)
            break
        except UnicodeDecodeError:
            pass
    else:
        return
    _run_reader(data, verbose)
    with open(error_filename, encoding=encoding) as file:
        _run_reader(file, verbose)

test_stream_error.unittest = ['.stream-error']

if __name__ == '__main__':
    import test_appliance
    test_appliance.run(globals())

