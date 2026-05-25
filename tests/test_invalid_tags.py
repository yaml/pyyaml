import pytest
import yaml


@pytest.mark.parametrize("document", [
    '!!bool "maybe"',
    '!!bool "yep"',
    '!!bool "nope"',
])
def test_invalid_bool_tag_raises_yaml_error(document):
    """!!bool with an unrecognised value must raise YAMLError, not raw KeyError."""
    with pytest.raises(yaml.YAMLError):
        yaml.safe_load(document)


@pytest.mark.parametrize("document", [
    '!!int "abc"',
    '!!int ""',
    '!!int "12abc"',
])
def test_invalid_int_tag_raises_yaml_error(document):
    """!!int with a non-integer string must raise YAMLError, not raw ValueError/IndexError."""
    with pytest.raises(yaml.YAMLError):
        yaml.safe_load(document)


@pytest.mark.parametrize("document", [
    '!!float "abc"',
    '!!float "not-a-float"',
])
def test_invalid_float_tag_raises_yaml_error(document):
    """!!float with a non-numeric string must raise YAMLError, not raw ValueError."""
    with pytest.raises(yaml.YAMLError):
        yaml.safe_load(document)


@pytest.mark.parametrize("document, expected", [
    ("!!bool 'true'", True),
    ("!!bool 'yes'", True),
    ("!!bool 'false'", False),
    ("!!bool 'no'", False),
    ("!!int '42'", 42),
    ("!!int '0xff'", 255),
    ("!!int '0b1010'", 10),
    ("!!float '3.14'", 3.14),
    ("!!float '.inf'", float('inf')),
])
def test_valid_tags_still_work(document, expected):
    """Valid scalar tags must still parse correctly after adding error handling."""
    result = yaml.safe_load(document)
    if expected == float('inf'):
        assert result == expected
    else:
        assert result == expected
