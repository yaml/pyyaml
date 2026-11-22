import pytest

import yaml


# A shorthand tag at the end of a flow collection entry has no node
# following it; the closing flow indicator must terminate the tag
# suffix instead of being consumed as part of it. These tests use the
# pure-Python loaders: the C loaders are provided by libyaml, which
# is maintained separately.


@pytest.mark.parametrize("source,expected", [
    ("!!seq [!!bool true, !!str]", [True, ""]),
    ("!!seq [!!bool true, !!str ]", [True, ""]),
    ("!!seq [!!str, !!str b]", ["", "b"]),
    ("[!!str a, !!str b]", ["a", "b"]),
    ("{a: !!str, b: 2}", {"a": "", "b": 2}),
    ("{a: !!str}", {"a": ""}),
])
def test_tag_suffix_stops_at_flow_indicators(source, expected):
    assert yaml.load(source, Loader=yaml.SafeLoader) == expected


def test_tag_token_in_flow_sequence():
    tokens = list(yaml.scan("[!!str a]", Loader=yaml.SafeLoader))
    tag_tokens = [token for token in tokens
            if isinstance(token, yaml.TagToken)]
    assert len(tag_tokens) == 1
    assert tag_tokens[0].value == ("!!", "str")
    assert isinstance(tokens[-2], yaml.FlowSequenceEndToken)


def test_verbatim_tag_keeps_flow_indicator_characters():
    tokens = list(yaml.scan(
        "!<tag:example.com,2024:foo[bar]> value", Loader=yaml.SafeLoader))
    tag_tokens = [token for token in tokens
            if isinstance(token, yaml.TagToken)]
    assert len(tag_tokens) == 1
    assert tag_tokens[0].value == (None, "tag:example.com,2024:foo[bar]")
