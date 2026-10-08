import pytest
import yaml


def test_dump():
    assert yaml.dump(['foo'])


def test_load_no_loader():
    with pytest.raises(TypeError):
        yaml.load("- foo\n")


def test_load_safeloader():
    assert yaml.load("- foo\n", Loader=yaml.SafeLoader)

@pytest.mark.parametrize("yaml_input", [
    '!!bool "maybe"',
    '!!bool ""',
    '!!bool "on"',
    '!!int "astring"',
    '!!int "0x"',
    '!!int "0b"',
    '!!int "1.5"',
    '!!int "inf"',
    '!!int ""',
    '!!float "not-a-number"',
    '!!float ""',
    '!!float "0x10"',
    '!!float "true"',
    '!!binary "not-base64!!!"',
    '!!binary "ñoño"',
    '!!timestamp "not-a-date"',
    '!!timestamp "2024-13-01"',
    '!!timestamp "yesterday"',
    '!!python/object:os.system {}',
    '!!python/name:os.system',
    '!!python/module:os',
])
def test_safeloader_explicit_tag_errors(yaml_input):
    with pytest.raises(yaml.constructor.ConstructorError):
        yaml.safe_load(yaml_input)
