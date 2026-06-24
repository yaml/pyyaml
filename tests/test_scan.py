import pytest

import yaml
from yaml.tokens import StreamStartToken, ScalarToken, StreamEndToken


_loaders = (yaml.SafeLoader,)
if yaml.__with_libyaml__:
    _loaders += (yaml.CSafeLoader,)


@pytest.mark.parametrize('loader_cls', _loaders)
def test_scan_produces_empty_string_style_for_scalar_node(loader_cls):
    start, scalar, end = yaml.scan('example', Loader=loader_cls)
    assert isinstance(start, StreamStartToken)
    assert isinstance(scalar, ScalarToken)
    assert scalar.style == ''
    assert isinstance(end, StreamEndToken)
