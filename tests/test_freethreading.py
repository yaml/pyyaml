"""Thread-safety of the class-level registries.

Under the free-threaded build (PEP 703) the copy-on-write in
``add_constructor`` / ``add_representer`` / ``add_implicit_resolver`` is a
check-then-act: the copy of the inherited registry and the assignment that
publishes it are separate operations.  Two threads registering at the same
time can each copy the parent registry, and the second assignment discards the
first thread's copy, losing that registration with no error.

These tests register from many threads at once and assert that every
registration survives.
"""

import re
import threading

import yaml

THREADS = 16
TRIALS = 50


def _run_concurrently(fn, threads=THREADS):
    """Call fn(i) on `threads` threads released from a common barrier."""
    barrier = threading.Barrier(threads)
    errors = []

    def worker(i):
        barrier.wait()
        try:
            fn(i)
        except BaseException as exc:  # pragma: no cover - surfaced via assert
            errors.append(exc)

    ts = [threading.Thread(target=worker, args=(i,)) for i in range(threads)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    assert not errors, f"worker raised: {errors[0]!r}"


def test_concurrent_add_constructor_keeps_every_registration():
    for _ in range(TRIALS):
        loader = type("TrialLoader", (yaml.SafeLoader,), {})
        _run_concurrently(lambda i: loader.add_constructor(f"!tag{i}", lambda l, n: i))
        missing = [f"!tag{i}" for i in range(THREADS) if f"!tag{i}" not in loader.yaml_constructors]
        assert not missing, f"lost {len(missing)} of {THREADS} constructors: {missing[:5]}"


def test_concurrent_add_multi_constructor_keeps_every_registration():
    for _ in range(TRIALS):
        loader = type("TrialLoader", (yaml.SafeLoader,), {})
        _run_concurrently(lambda i: loader.add_multi_constructor(f"!p{i}/", lambda l, s, n: i))
        missing = [f"!p{i}/" for i in range(THREADS) if f"!p{i}/" not in loader.yaml_multi_constructors]
        assert not missing, f"lost {len(missing)} of {THREADS} multi-constructors: {missing[:5]}"


def test_concurrent_add_representer_keeps_every_registration():
    types = [type(f"T{i}", (), {}) for i in range(THREADS)]
    for _ in range(TRIALS):
        dumper = type("TrialDumper", (yaml.SafeDumper,), {})
        _run_concurrently(lambda i: dumper.add_representer(types[i], lambda d, o: d.represent_str("x")))
        missing = [i for i in range(THREADS) if types[i] not in dumper.yaml_representers]
        assert not missing, f"lost {len(missing)} of {THREADS} representers: {missing[:5]}"


def test_concurrent_add_implicit_resolver_keeps_every_registration():
    for _ in range(TRIALS):
        resolver = type("TrialResolver", (yaml.resolver.Resolver,), {})
        _run_concurrently(
            lambda i: resolver.add_implicit_resolver(f"!t{i}", re.compile(rf"^{i}$"), [str(i % 10)])
        )
        registered = {tag for entries in resolver.yaml_implicit_resolvers.values() for tag, _ in entries}
        missing = [f"!t{i}" for i in range(THREADS) if f"!t{i}" not in registered]
        assert not missing, f"lost {len(missing)} of {THREADS} implicit resolvers: {missing[:5]}"


def test_concurrent_add_path_resolver_keeps_every_registration():
    for _ in range(TRIALS):
        resolver = type("TrialResolver", (yaml.resolver.Resolver,), {})
        _run_concurrently(lambda i: resolver.add_path_resolver(f"!p{i}", [str(i)], dict))
        registered = set(resolver.yaml_path_resolvers.values())
        missing = [f"!p{i}" for i in range(THREADS) if f"!p{i}" not in registered]
        assert not missing, f"lost {len(missing)} of {THREADS} path resolvers: {missing[:5]}"
