"""Benchmarks."""

import pathlib

from pytest_codspeed import BenchmarkFixture

from yaml import load
from yaml import CLoader

FIXTURE_PATH = pathlib.Path(__file__).parent.parent.joinpath("fixtures")



def test_large_parse_yaml(benchmark: BenchmarkFixture) -> None:
    """Test parsing a large YAML file."""
    yaml_str = FIXTURE_PATH.joinpath("large_automations.yaml").read_text()

    @benchmark
    def _parse_yaml() -> None:
        load(yaml_str, Loader=CLoader)
