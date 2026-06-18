import enum
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


@pytest.mark.skipif(sys.version_info < (3, 11), reason="StrEnum was added in Python 3.11")
def test_StrEnum():
    class TestEnum(enum.StrEnum):
        TEST_VALUE = "test value"

    assert yaml.load(yaml.dump(TestEnum.TEST_VALUE), Loader=yaml.SafeLoader) == TestEnum.TEST_VALUE
