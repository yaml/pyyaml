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


def test_safe_load_invalid_binary_integer_raises_constructor_error():
    with pytest.raises(ConstructorError):
        yaml.safe_load("0b_:")
