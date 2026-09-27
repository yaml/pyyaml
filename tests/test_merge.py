import pytest

import yaml


def loader_classes():
    classes = [yaml.SafeLoader]
    if hasattr(yaml, "CSafeLoader"):
        classes.append(yaml.CSafeLoader)
    return classes


def flatten_mapping_keys(source, name, Loader):
    loader = Loader(source)
    try:
        root = loader.get_single_node()
        for key_node, value_node in root.value:
            if key_node.value == name:
                loader.flatten_mapping(value_node)
                return [key_node.value for key_node, value_node in value_node.value]
        raise AssertionError("mapping %r was not found" % name)
    finally:
        loader.dispose()


def merge_fanout_source(levels, width):
    lines = [
        "n0: &n0 {%s}" % ", ".join(
            "k%s: %s" % (index, index) for index in range(width)
        )
    ]
    previous = "n0"
    for level in range(1, levels+1):
        prefix = chr(ord("a") + level - 1)
        aliases = []
        for index in range(width):
            name = "%s%s" % (prefix, index)
            lines.append("%s: &%s {<<: *%s}" % (name, name, previous))
            aliases.append("*%s" % name)
        current = "n%s" % level
        lines.append("%s: &%s {<<: [%s]}" % (current, current, ",".join(aliases)))
        previous = current
    lines.append("root: {<<: *%s}" % previous)
    return "\n".join(lines)


@pytest.mark.parametrize("Loader", loader_classes())
def test_flatten_mapping_skips_duplicate_sequence_merge_nodes(Loader):
    keys = flatten_mapping_keys(
        """
base: &base {x: 1, y: 2}
target:
  <<: [*base, *base]
  z: 3
""",
        "target",
        Loader,
    )

    assert keys == ["x", "y", "z"]


@pytest.mark.parametrize("Loader", loader_classes())
def test_flatten_mapping_skips_duplicate_direct_merge_nodes(Loader):
    keys = flatten_mapping_keys(
        """
base: &base {x: 1, y: 2}
target:
  <<: *base
  <<: *base
  z: 3
""",
        "target",
        Loader,
    )

    assert keys == ["x", "y", "z"]


@pytest.mark.parametrize("Loader", loader_classes())
def test_flatten_mapping_skips_nested_duplicate_merge_nodes(Loader):
    keys = flatten_mapping_keys(
        """
a0: &a0 {k0: 0}
a1: &a1
  <<: [*a0, *a0]
  k1: 1
a2: &a2
  <<: [*a1, *a1]
  k2: 2
target:
  <<: [*a2, *a2]
  k3: 3
""",
        "target",
        Loader,
    )

    assert keys == ["k0", "k1", "k2", "k3"]


@pytest.mark.parametrize("Loader", loader_classes())
def test_flatten_mapping_deduplicates_fanout_merge_keys(Loader):
    keys = flatten_mapping_keys(
        merge_fanout_source(levels=4, width=4),
        "root",
        Loader,
    )

    assert keys == ["k0", "k1", "k2", "k3"]


@pytest.mark.parametrize("Loader", loader_classes())
@pytest.mark.parametrize("key", ["x", "kk", "long_merge_key"])
@pytest.mark.parametrize("aliases", ["*a, *b, *c", "*a, *b, *a"])
def test_sequence_merge_uses_first_mapping_value(Loader, key, aliases):
    source = """
a: &a {%s: 1}
b: &b {%s: 2}
c: &c {%s: 3}
target:
  <<: [%s]
""" % (key, key, key, aliases)

    assert yaml.load(source, Loader=Loader)["target"] == {key: 1}


@pytest.mark.parametrize("Loader", loader_classes())
@pytest.mark.parametrize("explicit_first", [False, True])
def test_explicit_key_overrides_sequence_merge(Loader, explicit_first):
    fields = ["  <<: [*a, *b]", "  kk: 3"]
    if explicit_first:
        fields.reverse()
    source = "a: &a {kk: 1}\nb: &b {kk: 2}\ntarget:\n" + "\n".join(fields)

    assert yaml.load(source, Loader=Loader)["target"] == {"kk": 3}


@pytest.mark.parametrize("Loader", loader_classes())
def test_nested_merge_preserves_earlier_source_override(Loader):
    source = """
base: &base {kk: 1, base_only: 4}
override: &override {kk: 2}
combined: &combined
  <<: [*override, *base]
target:
  <<: [*base, *combined]
"""

    result = yaml.load(source, Loader=Loader)
    assert result["combined"] == {"kk": 2, "base_only": 4}
    assert result["target"] == {"kk": 1, "base_only": 4}
    assert flatten_mapping_keys(source, "target", Loader).count("base_only") == 1


@pytest.mark.parametrize("Loader", loader_classes())
def test_merge_preserves_values_with_shared_scalar_key_node(Loader):
    source = """
a: &a {&key kk: 1}
b: &b {*key: 2}
target:
  <<: [*a, *b]
"""

    assert yaml.load(source, Loader=Loader)["target"] == {"kk": 1}
