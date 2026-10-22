import pytest
import yaml


LOADERS = [yaml.SafeLoader]
if yaml.__with_libyaml__:
    LOADERS.append(yaml.CSafeLoader)


@pytest.fixture(params=LOADERS, ids=lambda loader: loader.__name__)
def loader(request):
    return request.param


@pytest.mark.parametrize(
    "document, expected",
    [
        ("! 12", "12"),
        ('! "12"', "12"),
        ("!", ""),
        ("! true", "true"),
        ("! null", "null"),
        ("! ~", "~"),
        ("! 1.5", "1.5"),
        ("! yes", "yes"),
        ("! 2020-01-01", "2020-01-01"),
        ("! |\n  text\n", "text\n"),
        ("key: ! 12", {"key": "12"}),
        ("- ! 12", ["12"]),
    ],
)
def test_non_specific_tag_resolves_to_str(loader, document, expected):
    assert yaml.load(document, Loader=loader) == expected


@pytest.mark.parametrize(
    "document, expected, tag",
    [
        ("! [1, 2]", [1, 2], "tag:yaml.org,2002:seq"),
        ("! {a: 1}", {"a": 1}, "tag:yaml.org,2002:map"),
    ],
)
def test_non_specific_tag_on_collections(loader, document, expected, tag):
    assert yaml.load(document, Loader=loader) == expected
    assert yaml.compose(document, Loader=loader).tag == tag


def test_non_specific_tag_scalar_node_tag(loader):
    assert yaml.compose("! 12", Loader=loader).tag == "tag:yaml.org,2002:str"


@pytest.mark.parametrize("document, expected", [("!!int 12", 12), ("!!str 12", "12")])
def test_explicit_tags_are_unchanged(loader, document, expected):
    assert yaml.load(document, Loader=loader) == expected


DUMPERS = [yaml.Dumper]
if yaml.__with_libyaml__:
    DUMPERS.append(yaml.CDumper)


@pytest.mark.parametrize("dumper", DUMPERS, ids=lambda dumper: dumper.__name__)
def test_empty_null_is_not_emitted_as_non_specific_tag(dumper):
    node = yaml.compose("key:")
    output = yaml.serialize(node, Dumper=dumper)
    assert "!!null" in output
    assert yaml.safe_load(output) == {"key": None}


@pytest.mark.parametrize(
    "document, expected",
    [
        ("{key: }", {"key": None}),
        ("[key:]", [{"key": None}]),
        ('key: !!null ""', {"key": None}),
        ('!!null ""', None),
    ],
)
@pytest.mark.parametrize("dumper", DUMPERS, ids=lambda dumper: dumper.__name__)
def test_empty_null_round_trips(dumper, document, expected):
    node = yaml.compose(document)
    output = yaml.serialize(node, Dumper=dumper)
    assert yaml.safe_load(output) == expected
