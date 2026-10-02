import pytest
import yaml


def loader_classes():
    classes = [
        yaml.SafeLoader,
        yaml.FullLoader,
        yaml.Loader,
        yaml.UnsafeLoader,
        yaml.BaseLoader,
    ]
    if hasattr(yaml, "CSafeLoader"):
        classes.extend([
            yaml.CSafeLoader,
            yaml.CFullLoader,
            yaml.CLoader,
            yaml.CUnsafeLoader,
            yaml.CBaseLoader,
        ])
    return classes


@pytest.mark.parametrize("Loader", loader_classes())
def test_standalone_equals_scalar(Loader):
    assert yaml.load("=", Loader=Loader) == "="


@pytest.mark.parametrize("Loader", loader_classes())
def test_standalone_equals_in_sequence(Loader):
    assert yaml.load("- =", Loader=Loader) == ["="]


@pytest.mark.parametrize("Loader", loader_classes())
def test_standalone_equals_as_mapping_value(Loader):
    assert yaml.load("key: =", Loader=Loader) == {"key": "="}


@pytest.mark.parametrize("Loader", loader_classes())
def test_standalone_equals_in_flow_sequence(Loader):
    assert yaml.load("[=, '!=', ==]", Loader=Loader) == ["=", "!=", "=="]


@pytest.mark.parametrize("Loader", loader_classes())
def test_standalone_equals_in_flow_mapping(Loader):
    assert yaml.load("{key: =}", Loader=Loader) == {"key": "="}


@pytest.mark.parametrize("Loader", loader_classes())
def test_standalone_equals_prometheus_crd(Loader):
    crd_yaml = """
properties:
  matchType:
    enum:
    - '!='
    - =
    - =~
    - '!~'
    type: string
"""
    result = yaml.load(crd_yaml, Loader=Loader)
    assert result["properties"]["matchType"]["enum"] == ["!=", "=", "=~", "!~"]


@pytest.mark.parametrize("Loader", loader_classes())
def test_standalone_equals_multi_document(Loader):
    yaml_docs = """---
=
---
key: =
---
- =
"""
    result = list(yaml.load_all(yaml_docs, Loader=Loader))
    assert result == ["=", {"key": "="}, ["="]]


def test_scanner_and_parser_tokens_for_equals():
    tokens = list(yaml.scan("="))
    assert any(
        isinstance(tok, yaml.ScalarToken) and tok.value == "="
        for tok in tokens
    )

    events = list(yaml.parse("="))
    assert any(
        isinstance(ev, yaml.ScalarEvent) and ev.value == "="
        for ev in events
    )


def test_round_trip_dump_load():
    assert yaml.safe_load(yaml.dump("=")) == "="
    assert yaml.safe_load(yaml.dump(["="])) == ["="]
    assert yaml.safe_load(yaml.dump({"key": "="})) == {"key": "="}
