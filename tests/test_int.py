import sys

import pytest

import yaml


def loader_classes():
    classes = [yaml.SafeLoader]
    if hasattr(yaml, "CSafeLoader"):
        classes.append(yaml.CSafeLoader)
    return classes


@pytest.mark.parametrize("Loader", loader_classes())
def test_sexagesimal_int(Loader):
    assert yaml.load("190:20:30", Loader=Loader) == 685230
    assert yaml.load("-1:0", Loader=Loader) == -60


@pytest.mark.skipif(not hasattr(sys, "get_int_max_str_digits"),
        reason="int() has no string conversion limit")
@pytest.mark.parametrize("Loader", loader_classes())
def test_sexagesimal_int_respects_int_max_str_digits(Loader):
    limit = sys.get_int_max_str_digits()
    if not limit:
        pytest.skip("int() string conversion limit is disabled")
    # The decimal form of this value is rejected by int(), the sexagesimal
    # form must not be a way around that limit.
    with pytest.raises(yaml.constructor.ConstructorError):
        yaml.load("1" + ":1" * limit, Loader=Loader)
    parts = limit // 2
    value = yaml.load("1" + ":0" * (parts - 1), Loader=Loader)
    assert value == 60 ** (parts - 1)
