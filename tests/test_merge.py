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
@pytest.mark.parametrize("key", ["x", "a_longer_key_name"])
def test_merge_keeps_override_of_merged_source(Loader, key):
    # The explicit value in the merged mapping must win, whatever the key's
    # length (string interning used to change the result).
    source = "t: &t {x: 0}\na: {b: &s {<<: *t, x: 1}}\nc: {<<: *s}\n"
    data = yaml.load(source.replace("x", key), Loader=Loader)

    assert data["c"] == {key: 1}


@pytest.mark.parametrize("Loader", loader_classes())
@pytest.mark.parametrize("key", ["a", "a_longer_key_name"])
def test_merge_sequence_earlier_source_wins(Loader, key):
    source = "m: {<<: [{a: 1}, {a: 2}]}"
    data = yaml.load(source.replace("a", key), Loader=Loader)

    assert data["m"] == {key: 1}


@pytest.mark.parametrize("Loader", loader_classes())
def test_merge_repeated_source_keeps_value_and_key_order(Loader):
    # base is merged both directly and through derived; base comes first in
    # the list, so its x wins, and the keys keep their first position.
    data = yaml.load(
        """
base: &base {x: 0, z: 1}
derived: &derived {<<: *base, x: 1, y: 2}
target: {<<: [*base, *derived]}
""",
        Loader=Loader,
    )

    assert list(data["target"].items()) == [("x", 0), ("z", 1), ("y", 2)]


@pytest.mark.parametrize("Loader", loader_classes())
def test_merge_repeated_source_with_equal_non_string_keys(Loader):
    # 0x1, 01 and 1 are the same int key.
    data = yaml.load(
        """
a0: &a0 {0x1: 15}
a1: &a1 {01: 23, <<: [*a0, *a0]}
a2: &a2 {1: 93}
target: {<<: [*a0, *a2, *a2, *a1]}
""",
        Loader=Loader,
    )

    assert data["target"] == {1: 15}
