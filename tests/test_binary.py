import pytest
import yaml


@pytest.fixture(params=[
    'SafeLoader', 'FullLoader', 'Loader', 'CSafeLoader', 'CFullLoader', 'CLoader'
])
def loader(request):
    result = getattr(yaml, request.param, None)
    if result is None:
        pytest.skip('LibYAML extension is not available')
    return result


@pytest.mark.parametrize('value', ['!!!!', 'aGVs!bG8=', 'aGVsbG8=?', 'aGVsbG8=AAAA'])
def test_binary_rejects_invalid_base64(loader, value):
    with pytest.raises(yaml.constructor.ConstructorError, match='failed to decode base64 data'):
        yaml.load("!!binary '" + value + "'", Loader=loader)


@pytest.mark.parametrize('value', [
    "'aGVsbG8='", "'aG Vs bG8='", '|\n  aGVs\n  bG8=', '"aG\\tVs\\r\\nbG8="'
])
def test_binary_accepts_base64_whitespace(loader, value):
    assert yaml.load('!!binary ' + value, Loader=loader) == b'hello'


def test_binary_accepts_empty_data(loader):
    assert yaml.load("!!binary ''", Loader=loader) == b''
