import pytest
import yaml
from yaml.constructor import ConstructorError


def test_dump():
    assert yaml.dump(['foo'])


def test_load_no_loader():
    with pytest.raises(TypeError):
        yaml.load("- foo\n")


def test_load_safeloader():
    assert yaml.load("- foo\n", Loader=yaml.SafeLoader)


# Tests for safe_dump / safe_load round-trip with tuple keys (issue #938).
# safe_dump serialises tuple keys as YAML sequences; safe_load must convert
# them back to tuples so that the round-trip restores the original dict.

@pytest.mark.parametrize("original", [
    {(1, 2): 0},
    {(1,): "one-tuple"},
    {(): "empty-tuple"},
    {("a", "b"): "str-tuple"},
    {((1, 2), (3, 4)): "nested"},
    {"normal": 1, 42: True, (1, 2): "mixed"},
])
def test_safe_roundtrip_tuple_key(original):
    """safe_load(safe_dump(d)) == d when d has tuple keys (GH-938)."""
    assert yaml.safe_load(yaml.safe_dump(original)) == original


def test_safe_load_sequence_key_becomes_tuple():
    """A YAML sequence used as a mapping key is loaded as a tuple by SafeLoader."""
    result = yaml.safe_load("? - 1\n  - 2\n: value\n")
    assert result == {(1, 2): "value"}


def test_full_load_sequence_key_still_errors():
    """FullLoader must still reject unhashable (sequence) keys."""
    with pytest.raises(ConstructorError, match="found unhashable key"):
        yaml.full_load("? - foo\n  - bar\n: baz\n")
