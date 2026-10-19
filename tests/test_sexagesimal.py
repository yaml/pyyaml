import pytest
import yaml


# Same magnitude as the decimal literal below, written as YAML 1.1 sexagesimal.
# https://github.com/yaml/pyyaml/issues/631
_DECIMAL = (
    "60.00000000000000355271367880050132378607394839652770586428264139311483660321755451150238513946533203125"
)
_SEXAGESIMAL = "1:0." + _DECIMAL.split(".", 1)[1]


def test_sexagesimal_float_matches_decimal_rounding():
    expected = float(_DECIMAL)
    assert yaml.safe_load(_DECIMAL) == expected
    assert yaml.load(_SEXAGESIMAL, Loader=yaml.Loader) == expected
    assert yaml.safe_load(_SEXAGESIMAL) == expected
    assert yaml.safe_load("-" + _SEXAGESIMAL) == -expected


def test_sexagesimal_float_keeps_canonical_value():
    assert yaml.safe_load("190:20:30.15") == 685230.15
    assert yaml.safe_load("190:20:30.1_5") == 685230.15
    assert yaml.safe_load("1:30.0") == 90.0
    assert yaml.safe_load("-1:2.5") == -62.5
    assert yaml.safe_load("+1:30:0.5") == 5400.5
    assert yaml.safe_load("1:2.") == 62.0
    assert yaml.safe_load("1:2:3.4") == 3723.4
    assert yaml.safe_load("!!float 1:2.5e1") == 85.0
    assert yaml.safe_load('!!float "1:+2.5"') == 62.5
    assert yaml.safe_load('!!float "1: 2.5"') == 62.5
    assert yaml.safe_load('!!float "1:.5"') == 60.5


def test_sexagesimal_float_invalid_component_raises_value_error():
    with pytest.raises(ValueError):
        yaml.safe_load('!!float "1:"')
    with pytest.raises(ValueError):
        yaml.safe_load('!!float "1::3"')
    with pytest.raises(ValueError):
        yaml.safe_load('!!float "1:abc"')


def test_sexagesimal_float_exponent_uses_float_rules():
    # An exponent is not plain sexagesimal, so each component still goes
    # through float(). Python turns an oversized exponent into infinity.
    assert yaml.safe_load('!!float "1:1e100000"') == float("inf")
    assert yaml.safe_load('!!float "1:1e-100000"') == 60.0


def test_sexagesimal_float_over_int_digit_limit_uses_float():
    # int() rejects a component longer than the interpreter digit limit.
    # The float() path still accepts these and returns 60.
    for digits in (4301, 5001):
        text = "1:0." + "0" * (digits - 1) + "1"
        assert yaml.safe_load(text) == 60.0
        assert yaml.safe_load("-" + text) == -60.0


def test_sexagesimal_float_huge_value_is_inf():
    text = ":".join(["59"] * 400) + ".0"
    assert yaml.safe_load(text) == float("inf")
    assert yaml.safe_load("-" + text) == float("-inf")
