"""Token-mark parity for directives.

The token-class suites (`test_tokens`, `test_scanner`) do not compare marks,
so an engine that emits the right token kinds with wrong spans passes them.
These tests pin the exact spans the pure-Python scanner produces, and run
against whichever scanner is active (pure or the optional `yaml._rust`
accelerator).
"""

import yaml


def _directive_marks(doc):
    return [
        (t.name, t.value, t.start_mark.index, t.end_mark.index)
        for t in yaml.scan(doc)
        if isinstance(t, yaml.DirectiveToken)
    ]


def test_unknown_directive_end_mark():
    # End mark sits right after the directive name, before the scanner
    # skips the ignored rest of the line.
    assert _directive_marks("%FOO  bar baz # ignored\n--- foo\n") == [
        ("FOO", None, 0, 4)
    ]


def test_yaml_directive_end_mark():
    assert _directive_marks("%YAML 1.2\n--- foo\n") == [
        ("YAML", (1, 2), 0, 9)
    ]


def test_tag_directive_end_mark():
    assert _directive_marks("%TAG ! tag:example.com,2000:app/\n--- foo\n") == [
        ("TAG", ("!", "tag:example.com,2000:app/"), 0, 32)
    ]
