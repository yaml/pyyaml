import pytest

import yaml


def dumper_loader_pairs():
    pairs = [
        (yaml.Dumper, yaml.SafeLoader),
        (yaml.SafeDumper, yaml.SafeLoader),
    ]
    if hasattr(yaml, "CDumper") and hasattr(yaml, "CSafeLoader"):
        pairs.extend([
            (yaml.CDumper, yaml.CSafeLoader),
            (yaml.CSafeDumper, yaml.CSafeLoader),
        ])
    return pairs


@pytest.mark.parametrize("Dumper,Loader", dumper_loader_pairs())
def test_yaml_object_without_attributes(Dumper, Loader):
    class EmptyObj(yaml.YAMLObject):
        yaml_tag = "!EmptyObj"
        yaml_loader = Loader
        yaml_dumper = Dumper

        def __eq__(self, other):
            return isinstance(other, EmptyObj)

    dumped = yaml.dump({"obj": EmptyObj()}, Dumper=Dumper)
    assert dumped == "obj: !EmptyObj {}\n"

    loaded = yaml.load(dumped, Loader=Loader)
    assert loaded == {"obj": EmptyObj()}


@pytest.mark.parametrize("Dumper,Loader", dumper_loader_pairs())
def test_yaml_object_with_attributes(Dumper, Loader):
    class SimpleObj(yaml.YAMLObject):
        yaml_tag = "!SimpleObj"
        yaml_loader = Loader
        yaml_dumper = Dumper

        def __init__(self, name="X"):
            self.name = name

        def __eq__(self, other):
            return isinstance(other, SimpleObj) and self.name == other.name

    dumped = yaml.dump({"obj": SimpleObj("abc")}, Dumper=Dumper)
    loaded = yaml.load(dumped, Loader=Loader)
    assert loaded == {"obj": SimpleObj("abc")}


def test_yaml_object_getstate_returns_none():
    class NoneStateObj(yaml.YAMLObject):
        yaml_tag = "!NoneStateObj"
        yaml_loader = yaml.SafeLoader

        def __getstate__(self):
            return None

    dumped = yaml.dump(NoneStateObj())
    assert dumped == "!NoneStateObj {}\n"
    loaded = yaml.safe_load(dumped)
    assert isinstance(loaded, NoneStateObj)


def test_yaml_object_custom_getstate_pairs():
    class PairStateObj(yaml.YAMLObject):
        yaml_tag = "!PairStateObj"
        yaml_loader = yaml.SafeLoader

        def __getstate__(self):
            return (("a", 1), ("b", 2))

    dumped = yaml.dump(PairStateObj())
    loaded = yaml.safe_load(dumped)
    assert isinstance(loaded, PairStateObj)
    assert loaded.a == 1
    assert loaded.b == 2


def test_yaml_object_with_slots():
    class SlottedEmptyObj(yaml.YAMLObject):
        yaml_tag = "!SlottedEmptyObj"
        yaml_loader = yaml.SafeLoader
        __slots__ = ("value",)

        def __setstate__(self, state):
            if "value" in state:
                self.value = state["value"]

    empty = SlottedEmptyObj()
    dumped_empty = yaml.dump(empty)
    assert dumped_empty == "!SlottedEmptyObj {}\n"
    loaded_empty = yaml.safe_load(dumped_empty)
    assert isinstance(loaded_empty, SlottedEmptyObj)
    assert not hasattr(loaded_empty, "value")

    class SlottedValueObj(yaml.YAMLObject):
        yaml_tag = "!SlottedValueObj"
        yaml_loader = yaml.SafeLoader
        __slots__ = ("value",)

        def __init__(self, value=None):
            self.value = value

        def __setstate__(self, state):
            self.value = state["value"]

    populated = SlottedValueObj(42)
    dumped_populated = yaml.dump(populated)
    assert dumped_populated == "!SlottedValueObj\nvalue: 42\n"
    loaded_populated = yaml.safe_load(dumped_populated)
    assert isinstance(loaded_populated, SlottedValueObj)
    assert loaded_populated.value == 42
