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


def test_dump_str_enum():
    if sys.version_info < (3, 11):
        return

    from enum import StrEnum

    class ContentType(StrEnum):
        YAML = "YAML"

    assert yaml.load(yaml.dump(ContentType.YAML, Dumper=yaml.SafeDumper), Loader=yaml.SafeLoader) == ContentType.YAML
