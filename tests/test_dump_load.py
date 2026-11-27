import pytest
import yaml


def test_dump():
    assert yaml.dump(['foo'])


def test_load_no_loader():
    with pytest.raises(TypeError):
        yaml.load("- foo\n")


def test_load_safeloader():
    assert yaml.load("- foo\n", Loader=yaml.SafeLoader)


def test_dump_yaml_object_without_members():
    # https://github.com/yaml/pyyaml/issues/1020
    class Without(yaml.YAMLObject):
        yaml_tag = '!Without'
        yaml_loader = yaml.SafeLoader

        def __init__(self):
            pass

    assert yaml.dump({"obj": Without()}) == "obj: !Without {}\n"
    loaded = yaml.safe_load("obj: !Without {}\n")
    assert isinstance(loaded["obj"], Without)
