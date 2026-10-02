import pytest
import yaml
from yaml.constructor import ConstructorError


def loader_classes():
    classes = [yaml.SafeLoader, yaml.Loader, yaml.FullLoader, yaml.UnsafeLoader]
    if hasattr(yaml, "CSafeLoader"):
        classes.append(yaml.CSafeLoader)
    if hasattr(yaml, "CLoader"):
        classes.append(yaml.CLoader)
    if hasattr(yaml, "CFullLoader"):
        classes.append(yaml.CFullLoader)
    if hasattr(yaml, "CUnsafeLoader"):
        classes.append(yaml.CUnsafeLoader)
    return classes


def test_safe_load_regression_868():
    assert yaml.safe_load("0b") == "0b"
    with pytest.raises(ConstructorError):
        yaml.safe_load("0b_:")


@pytest.mark.parametrize("Loader", loader_classes())
def test_empty_int_base_literals(Loader):
    # Plain '0b', '0x', '0o' without explicit int tag resolve as strings
    assert yaml.load("0b", Loader=Loader) == "0b"
    assert yaml.load("0x", Loader=Loader) == "0x"
    assert yaml.load("0o", Loader=Loader) == "0o"

    # Malformed base literals with underscores that resolve to int tag
    for malformed in ["0b_", "0b_:", "0x_", "0x_:"]:
        with pytest.raises(ConstructorError):
            yaml.load(malformed, Loader=Loader)

    # Explicit int tags without digits
    for malformed in [
        "!!int 0b",
        "!!int 0x",
        "!!int 0o",
        "!!int +0b",
        "!!int -0b",
        "!!int +0x",
        "!!int -0x",
        "!!int +0o",
        "!!int -0o",
        "!!int 0b_",
        "!!int 0x_",
        "!!int 0o_",
        "!!int ''",
        "!!int '-'",
        "!!int '+'",
    ]:
        with pytest.raises(ConstructorError):
            yaml.load(malformed, Loader=Loader)

    # Valid base literals
    assert yaml.load("0b10", Loader=Loader) == 2
    assert yaml.load("0b_10", Loader=Loader) == 2
    assert yaml.load("+0b10", Loader=Loader) == 2
    assert yaml.load("-0b10", Loader=Loader) == -2
    assert yaml.load("0x10", Loader=Loader) == 16
    assert yaml.load("0x_10", Loader=Loader) == 16
    assert yaml.load("+0x10", Loader=Loader) == 16
    assert yaml.load("-0x10", Loader=Loader) == -16
    assert yaml.load("010", Loader=Loader) == 8
    assert yaml.load("0_10", Loader=Loader) == 8
    assert yaml.load("0o10", Loader=Loader) == "0o10"
    assert yaml.load("!!int 0o10", Loader=Loader) == 8
