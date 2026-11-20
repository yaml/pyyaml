from __future__ import annotations

import pytest
import yaml

try:
    HAS_LIBYAML = yaml._yaml and yaml.cyaml
    HAS_LIBYAML_RECURSION_CONTROL = yaml._yaml._get_max_nest_level() != -1
except AttributeError:
    HAS_LIBYAML = False
    HAS_LIBYAML_RECURSION_CONTROL = False


pytestmark = pytest.mark.skipif(not HAS_LIBYAML, reason="libyaml extension unavailable")

def test_recursion_controls() -> None:
    """Validate libyaml recursion control behavior."""
    default_max = yaml._yaml._get_max_nest_level()
    try:
        yaml._yaml._set_max_nest_level(42)

        if HAS_LIBYAML_RECURSION_CONTROL:
            assert default_max > 100
            assert yaml._yaml._get_max_nest_level() == 42
        else:
            # libyaml is missing the recursion control feature; setter should no-op, getter always returns -1
            assert default_max == -1
            assert yaml._yaml._get_max_nest_level() == default_max
    finally:
        # always restore the default since it's global
        yaml._yaml._set_max_nest_level(default_max)


@pytest.mark.parametrize("loader", [yaml.CLoader, yaml.CBaseLoader, yaml.CSafeLoader, yaml.CFullLoader, yaml.CUnsafeLoader])
@pytest.mark.parametrize("ch", [('[', ']'), ('{', '}')])
@pytest.mark.skipif(not HAS_LIBYAML_RECURSION_CONTROL, reason="libyaml recursion control feature unavailable")
def test_recursion_depth_exceeded(loader: yaml.cyaml.CParser, ch: tuple[str, str]) -> None:
    default_max = yaml._yaml._get_max_nest_level()

    try:
        maxdepth = 5
        yaml._yaml._set_max_nest_level(maxdepth)
        assert yaml._yaml._get_max_nest_level() == maxdepth

        data = (ch[0] * (maxdepth + 2)) + "blah" + (ch[1] * (maxdepth + 2))

        with pytest.raises(yaml.scanner.ScannerError, match="exceeded maximum nesting depth"):
            yaml.load(data, Loader=loader)

    finally:
        # always restore the default since it's global
        yaml._yaml._set_max_nest_level(default_max)
