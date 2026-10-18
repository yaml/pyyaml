import pytest
import yaml


def test_dump():
    assert yaml.dump(['foo'])


def test_load_no_loader():
    with pytest.raises(TypeError):
        yaml.load("- foo\n")


def test_load_safeloader():
    assert yaml.load("- foo\n", Loader=yaml.SafeLoader)


@pytest.mark.parametrize("source, prefix_directive", [
    ("%TAG ! tag:%002:\n---\n", "%TAG ! tag:%002:\n"),
    ("%TAG !e! tag:%C3%A9,2000:\n--- !e!x a\n", "%TAG !e! tag:%C3%A9,2000:\n"),
])
def test_emit_tag_prefix_percent_escapes(source, prefix_directive):
    output = yaml.emit(yaml.parse(source))
    assert output.startswith(prefix_directive)
