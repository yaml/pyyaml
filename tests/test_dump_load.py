import pytest
import yaml


def test_dump():
    assert yaml.dump(['foo'])


def test_load_no_loader():
    with pytest.raises(TypeError):
        yaml.load("- foo\n")


def test_load_safeloader():
    assert yaml.load("- foo\n", Loader=yaml.SafeLoader)


@pytest.mark.parametrize('allow_unicode', [False, True])
@pytest.mark.parametrize('style', [None, "'", '|', '>'])
@pytest.mark.parametrize('value', ['\x85', 'a\x85b', '\x85a', 'a\x85'])
def test_dump_load_nel(value, style, allow_unicode):
    # The reader turns NEL (U+0085) into a line feed, so the emitter
    # must escape it in a double-quoted scalar to keep it.
    data = {'key': value, value: 'value'}
    dumped = yaml.dump(data, default_style=style, allow_unicode=allow_unicode)
    assert yaml.load(dumped, Loader=yaml.SafeLoader) == data
