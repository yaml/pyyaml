"""Dump-side quoting for leading-zero digit strings (#966)."""
import yaml


def test_leading_zero_digit_strings_are_quoted():
    # PyYAML's own resolver keeps these strings, but lenient YAML 1.1
    # readers parse them as numbers; they must not be written plain.
    for value in ['08', '09', '0123456789', '008', '-08', '+0_8', '0_8']:
        dumped = yaml.safe_dump({'id': value})
        assert f"'{value}'" in dumped, (value, dumped)
        assert yaml.safe_load(dumped) == {'id': value}


def test_other_strings_keep_plain_style():
    # Values that no reader can confuse must not gain quotes.
    for value in ['10', 'abc', '0']:
        dumped = yaml.safe_dump({'id': value})
        assert value in dumped
        assert yaml.safe_load(dumped) == {'id': value}
