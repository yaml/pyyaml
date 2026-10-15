import pytest
import yaml


pytestmark = pytest.mark.skipif(
    not yaml.__with_libyaml__, reason="requires the LibYAML extension"
)


@pytest.mark.parametrize("reader", [yaml.parse, yaml.scan])
@pytest.mark.parametrize("escaped", ["%c0%80", "%ed%a0%80", "%f4%90%80%80"])
@pytest.mark.parametrize("template", ["a: !<{}> 1\n", "%TAG !e! {}\n---\n!e!x value\n"])
def test_invalid_utf8_tag(reader, escaped, template):
    with pytest.raises(UnicodeDecodeError):
        list(reader(template.format(escaped), Loader=yaml.CSafeLoader))


@pytest.mark.parametrize("reader", [yaml.parse, yaml.scan])
def test_valid_escaped_tag(reader):
    items = list(reader("a: !<%41> 1\n", Loader=yaml.CSafeLoader))
    if reader is yaml.parse:
        assert any(getattr(item, "tag", None) == "A" for item in items)
    else:
        assert any(isinstance(item, yaml.tokens.TagToken)
                   and item.value == (None, "A") for item in items)
