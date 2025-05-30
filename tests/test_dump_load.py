import sys

import pytest
import yaml


def test_dump():
    assert yaml.dump(['foo'])


def test_load_no_loader():
    with pytest.raises(TypeError):
        yaml.load("- foo\n")


def test_load_safeloader():
    assert yaml.load("- foo\n", Loader=yaml.SafeLoader)


@pytest.mark.skipif(sys.version_info < (3, 11), reason="Requires Python 3.11 or higher")
def test_dump_str_enum():
    from enum import StrEnum

    class ContentType(StrEnum):
        YAML = "YAML"

    assert yaml.safe_load(yaml.safe_dump(ContentType.YAML)) == ContentType.YAML
