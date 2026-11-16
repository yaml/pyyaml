import time

import pytest

import yaml
from yaml.composer import ComposerError


BILLION_LAUGHS = """
a: &a ["lol","lol","lol","lol","lol","lol","lol","lol","lol"]
b: &b [*a,*a,*a,*a,*a,*a,*a,*a,*a]
c: &c [*b,*b,*b,*b,*b,*b,*b,*b,*b]
d: &d [*c,*c,*c,*c,*c,*c,*c,*c,*c]
e: &e [*d,*d,*d,*d,*d,*d,*d,*d,*d]
f: &f [*e,*e,*e,*e,*e,*e,*e,*e,*e]
g: &g [*f,*f,*f,*f,*f,*f,*f,*f,*f]
h: &h [*g,*g,*g,*g,*g,*g,*g,*g,*g]
i: &i [*h,*h,*h,*h,*h,*h,*h,*h,*h]
"""


@pytest.mark.parametrize("source", [
    "- foo\n- 1\n- 2.5\n- true\n- null\n",
    "a: 1\nb: [x, y]\nc: {d: e}\nf: 2001-12-14\n",
    "plain scalar\n",
    "",
])
def test_plain_documents_load_like_safeloader(source):
    expected = yaml.load(source, Loader=yaml.SafeLoader)
    assert yaml.load(source, Loader=yaml.RestrictedSafeLoader) == expected


@pytest.mark.parametrize("source", [
    "a: &x 1\n",
    "a: &x [1, 2]\n",
    "a: &x {b: 1}\n",
    "&x a: 1\n",
])
def test_anchor_is_rejected(source):
    with pytest.raises(ComposerError, match="found anchor 'x'"):
        yaml.load(source, Loader=yaml.RestrictedSafeLoader)


def test_alias_is_rejected():
    with pytest.raises(ComposerError, match="found alias 'x'") as excinfo:
        yaml.load("a: *x\n", Loader=yaml.RestrictedSafeLoader)
    assert excinfo.value.problem_mark.line == 0
    assert excinfo.value.problem_mark.column == 3


def test_anchor_error_points_at_anchor():
    with pytest.raises(ComposerError) as excinfo:
        yaml.load("a: 1\nb: &x 2\n", Loader=yaml.RestrictedSafeLoader)
    assert excinfo.value.problem_mark.line == 1
    assert excinfo.value.problem_mark.column == 3


def test_billion_laughs_is_rejected_quickly():
    start = time.monotonic()
    with pytest.raises(ComposerError, match="found anchor 'a'"):
        yaml.load(BILLION_LAUGHS, Loader=yaml.RestrictedSafeLoader)
    assert time.monotonic() - start < 1.0


def test_merge_key_is_rejected():
    source = "base: {x: 1}\ntarget:\n  <<: *base\n  y: 2\n"
    with pytest.raises(ComposerError, match="found alias 'base'"):
        yaml.load(source, Loader=yaml.RestrictedSafeLoader)


def test_load_all_plain_documents():
    source = "--- 1\n--- [a, b]\n--- {c: d}\n"
    assert list(yaml.load_all(source, Loader=yaml.RestrictedSafeLoader)) == [
        1, ["a", "b"], {"c": "d"},
    ]


def test_load_all_rejects_anchor_in_later_document():
    source = "--- 1\n--- &x [a]\n"
    documents = yaml.load_all(source, Loader=yaml.RestrictedSafeLoader)
    assert next(documents) == 1
    with pytest.raises(ComposerError, match="found anchor 'x'"):
        next(documents)


def test_error_is_a_yaml_error():
    with pytest.raises(yaml.YAMLError) as excinfo:
        yaml.load("a: *x\n", Loader=yaml.RestrictedSafeLoader)
    assert isinstance(excinfo.value, yaml.composer.ComposerError)
    assert isinstance(excinfo.value, yaml.MarkedYAMLError)
