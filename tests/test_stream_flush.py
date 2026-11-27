import io

import pytest
import yaml


def dumper_classes(include_base=False):
    classes = [yaml.SafeDumper, yaml.Dumper]
    if include_base:
        classes.append(yaml.BaseDumper)
    if yaml.__with_libyaml__:
        classes.extend([yaml.CSafeDumper, yaml.CDumper])
        if include_base:
            classes.append(yaml.CBaseDumper)
    return classes


@pytest.mark.parametrize('Dumper', dumper_classes())
@pytest.mark.parametrize('encoding', [None, 'utf-8', 'utf-16-le', 'utf-16-be'])
def test_dump_flushes_buffered_file(tmp_path, Dumper, encoding):
    path = tmp_path / 'output.yaml'
    mode = 'w' if encoding is None else 'wb'
    options = {'encoding': 'utf-8', 'newline': ''} if encoding is None else {}
    with path.open(mode, **options) as stream:
        yaml.dump_all([{'message': 'hello'}, {'message': 'world'}], stream,
                      Dumper=Dumper, encoding=encoding)
        actual = path.read_bytes()
        expected = yaml.dump_all([{'message': 'hello'}, {'message': 'world'}],
                                 Dumper=Dumper, encoding=encoding)
        if encoding is None:
            expected = expected.encode('utf-8')
        assert actual == expected
        assert not stream.closed


@pytest.mark.parametrize('Dumper', dumper_classes(include_base=True))
def test_emit_flushes_buffered_file(tmp_path, Dumper):
    path = tmp_path / 'events.yaml'
    source = 'message: hello\n'
    with path.open('w') as stream:
        yaml.emit(yaml.parse(source), stream, Dumper=Dumper)
        assert path.read_text() == source
        assert not stream.closed


class WriteOnlyStream:
    def __init__(self):
        self.parts = []

    def write(self, data):
        self.parts.append(data)


@pytest.mark.parametrize('Dumper', dumper_classes())
def test_dump_supports_stream_without_flush(Dumper):
    stream = WriteOnlyStream()
    yaml.dump({'message': 'hello'}, stream, Dumper=Dumper)
    assert ''.join(stream.parts) == 'message: hello\n'


class FlushErrorStream(io.StringIO):
    def flush(self):
        raise OSError('flush failed')


@pytest.mark.parametrize('Dumper', dumper_classes())
@pytest.mark.parametrize('use_events', [False, True])
def test_stream_flush_error_is_propagated(Dumper, use_events):
    stream = FlushErrorStream()
    with pytest.raises(OSError, match='flush failed'):
        if use_events:
            yaml.emit(yaml.parse('message: hello\n'), stream, Dumper=Dumper)
        else:
            yaml.dump({'message': 'hello'}, stream, Dumper=Dumper)


@pytest.mark.parametrize('Dumper', dumper_classes(include_base=True))
def test_closing_empty_stream_flushes_once(Dumper):
    class CountingStream(io.StringIO):
        flush_count = 0

        def flush(self):
            self.flush_count += 1

    stream = CountingStream()
    dumper = Dumper(stream)
    try:
        dumper.open()
        dumper.close()
        dumper.close()
        assert stream.flush_count == 1
    finally:
        dumper.dispose()
