import pytest
import yaml


@pytest.mark.parametrize("source", [
    "0x_",
    "0b_",
    "!!int 1::3",
])
def test_malformed_int_scalar_raises_yaml_error(source):
    with pytest.raises(yaml.YAMLError):
        yaml.safe_load(source)


@pytest.mark.parametrize("source", [
    "!!float +_",
    "!!float 1::3",
])
def test_malformed_float_scalar_raises_yaml_error(source):
    with pytest.raises(yaml.YAMLError):
        yaml.safe_load(source)


@pytest.mark.parametrize("source,expected", [
    ("0x1A", 26),
    ("0b101", 5),
    ("017", 15),
    ("1_000", 1000),
    ("0_", 0),
    ("!!int 1:30", 90),
])
def test_valid_int_scalar_still_parses(source, expected):
    assert yaml.safe_load(source) == expected


@pytest.mark.parametrize("source,expected", [
    ("!!float 1.5", 1.5),
    ("!!float 1:30:00", 5400.0),
])
def test_valid_float_scalar_still_parses(source, expected):
    assert yaml.safe_load(source) == expected
