
import yaml.reader
import codecs

def _run_reader(data, verbose):
    try:
        stream = yaml.reader.Reader(data)
        while stream.peek() != u'\0':
            stream.forward()
    except yaml.reader.ReaderError, exc:
        if verbose:
            print exc
    else:
        raise AssertionError("expected an exception")

def test_stream_error(error_filename, verbose=False):
    with open(error_filename, 'rb') as fp:
        _run_reader(fp, verbose)
    with open(error_filename, 'rb') as fp:
        _run_reader(fp.read(), verbose)
    for encoding in ['utf-8', 'utf-16-le', 'utf-16-be']:
        try:
            with open(error_filename, 'rb') as fp:
                data = unicode(fp.read(), encoding)
            break
        except UnicodeDecodeError:
            pass
    else:
        return
    _run_reader(data, verbose)
    with codecs.open(error_filename, encoding=encoding) as fp:
        _run_reader(fp, verbose)

test_stream_error.unittest = ['.stream-error']

if __name__ == '__main__':
    import test_appliance
    test_appliance.run(globals())

