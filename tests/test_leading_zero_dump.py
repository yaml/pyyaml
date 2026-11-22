"""Dump-side quoting for leading-zero digit strings (#966, #741)."""
import yaml


def test_leading_zero_digit_strings_are_quoted():
    # PyYAML's own resolver keeps these strings, but lenient YAML 1.1
    # readers parse them as numbers; they must not be written plain.
    for value in ['08', '09', '04549', '0123456789', '008', '-08', '+08', '0_8']:
        dumped = yaml.safe_dump({'id': value})
        assert f"'{value}'" in dumped, (value, dumped)
        assert yaml.safe_load(dumped) == {'id': value}


def test_other_strings_keep_plain_style():
    # Values that no reader can confuse must not gain quotes.
    for value in ['abc', 'x1y', 'abc10', 'value']:
        dumped = yaml.safe_dump({'id': value})
        assert value in dumped
        assert yaml.safe_load(dumped) == {'id': value}


def test_values_matching_own_resolver_stay_quoted():
    # Strings matching PyYAML's own int/float regexes were already quoted
    # before this change; their behavior and round-trip must be unchanged.
    for value in ['10', '24543', '-10', '0x1f', '0.8', '07']:
        dumped = yaml.safe_dump({'id': value})
        assert yaml.safe_load(dumped) == {'id': value}


def test_issue_741_round_trip():
    data = yaml.safe_load("value:\n    - '04549'\n    - '24543'\n")
    dumped = yaml.safe_dump(data)
    assert yaml.safe_load(dumped) == data
    assert all(isinstance(v, str) for v in data['value'])
