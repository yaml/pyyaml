"""The ``yaml.add_*`` helpers must also register on ``SafeLoader``.

``yaml.safe_load()`` is the loader PyYAML tells users to reach for when the
input is not trusted, so a tag registered through the module level helpers has
to be honoured by it.  These helpers used to update ``Loader``, ``FullLoader``
and ``UnsafeLoader`` only, which left the safe path silently ignoring the
registration: an implicitly resolved tag fell back to a plain string and an
explicit tag raised ``ConstructorError``.
"""

import re

import pytest
import yaml

WORKING_TAG = "!test/working"
MULTI_PREFIX = "!test/multi/"

PLAIN_SCALAR_DOCUMENT = "registry_probe_scalar"
MULTI_DOCUMENT = MULTI_PREFIX + "suffix_value payload"

ALL_LOADERS = [yaml.Loader, yaml.FullLoader, yaml.UnsafeLoader, yaml.SafeLoader]


def working_constructor(loader, node):
    return ("scalar", loader.construct_scalar(node))


def multi_constructor(loader, tag_suffix, node):
    return ("multi", tag_suffix, loader.construct_scalar(node))


yaml.add_implicit_resolver(WORKING_TAG, re.compile(r"^registry_probe_scalar$"))
yaml.add_constructor(WORKING_TAG, working_constructor)
yaml.add_multi_constructor(MULTI_PREFIX, multi_constructor)


@pytest.mark.parametrize("loader", ALL_LOADERS)
def test_registrations_reach_every_loader_registry(loader):
    assert WORKING_TAG in loader.yaml_constructors
    assert MULTI_PREFIX in loader.yaml_multi_constructors
    registered = loader.yaml_implicit_resolvers.get(
        PLAIN_SCALAR_DOCUMENT[0], []
    ) + loader.yaml_implicit_resolvers.get(None, [])
    assert any(resolved == WORKING_TAG for resolved, _regexp in registered)


@pytest.mark.parametrize("loader", ALL_LOADERS)
def test_add_implicit_resolver_and_constructor_reach_every_loader(loader):
    assert yaml.load(PLAIN_SCALAR_DOCUMENT, Loader=loader) == (
        "scalar",
        PLAIN_SCALAR_DOCUMENT,
    )


def test_add_implicit_resolver_and_constructor_reach_safe_load():
    # Before the fix yaml.safe_load() returned the bare string here, because the
    # resolver had been registered on the non-safe loaders only.
    assert yaml.safe_load(PLAIN_SCALAR_DOCUMENT) == (
        "scalar",
        PLAIN_SCALAR_DOCUMENT,
    )


@pytest.mark.parametrize(
    "safe_load",
    [yaml.safe_load, lambda doc: list(yaml.safe_load_all(doc))[0]],
    ids=["safe_load", "safe_load_all"],
)
def test_safe_entry_points_honour_the_registrations(safe_load):
    assert safe_load(PLAIN_SCALAR_DOCUMENT) == ("scalar", PLAIN_SCALAR_DOCUMENT)


@pytest.mark.parametrize("loader", ALL_LOADERS)
def test_add_multi_constructor_reaches_every_loader(loader):
    assert yaml.load(MULTI_DOCUMENT, Loader=loader) == (
        "multi",
        "suffix_value",
        "payload",
    )


def test_add_multi_constructor_reaches_safe_load():
    # Before the fix this raised
    # "ConstructorError: could not determine a constructor for the tag '!test/multi/...'"
    assert yaml.safe_load(MULTI_DOCUMENT) == ("multi", "suffix_value", "payload")


def test_add_constructor_reaches_safe_load_without_implicit_resolver():
    tag = "!test/explicit-only"
    yaml.add_constructor(tag, working_constructor)
    assert yaml.safe_load(tag + " payload") == ("scalar", "payload")


def test_explicit_loader_argument_still_works():
    # The explicit Loader= form must keep behaving exactly as before.
    tag = "!test/explicit-loader-arg"
    yaml.add_constructor(tag, working_constructor, Loader=yaml.SafeLoader)
    assert yaml.load(tag + " payload", Loader=yaml.SafeLoader) == (
        "scalar",
        "payload",
    )


def test_base_loader_is_not_touched_by_default():
    # BaseLoader resolves nothing and has no yaml_constructors registry, so the
    # module level helpers must not reach for it.
    assert yaml.BaseLoader.yaml_constructors == {}
    assert yaml.load(PLAIN_SCALAR_DOCUMENT, Loader=yaml.BaseLoader) == (
        PLAIN_SCALAR_DOCUMENT
    )
