from dataclasses import dataclass
from datetime import date
import yaml

def _simple_roundtrip(orig):
    loaded = yaml.load(yaml.dump(orig, Dumper=yaml.CDumper, sort_keys=False), Loader=yaml.CLoader)
    assert loaded == orig

def test_scalar_types(verbose=False):
    _simple_roundtrip({i for i in range(10)})
    _simple_roundtrip({str(i) for i in range(10)})
    _simple_roundtrip({str(i): i for i in range(10)})

test_scalar_types.unittest = None

@dataclass(frozen=True)
class ModelFitkey:
    broker: str
    currency: str

@dataclass(frozen=True)
class SingleDayOutput:
    day: date
    path: str

def test_complex_types(verbose=False):
    _simple_roundtrip({ModelFitkey('ib', 'euro'), ModelFitkey('ib', 'usd'), ModelFitkey('cme', 'cad')})
    d = {
        ModelFitkey('ib', 'euro'): [SingleDayOutput(date(2022, 1, 2), '/a/b/c/20220102/euro.bin'),
                                    SingleDayOutput(date(2022, 1, 3), '/a/b/c/20220103/euro.bin')],
        ModelFitkey('ib', 'usd'): [SingleDayOutput(date(2022, 1, 2), '/z/b/20220101/usd.bin'),
                                   SingleDayOutput(date(2022, 1, 3), '/z/b/20220102/usd.bin'),
                                   SingleDayOutput(date(2022, 2, 3), '/z/b/20220202/usd.bin')],
        ModelFitkey('cme', 'cad'): []}
    _simple_roundtrip(d)

test_complex_types.unittest = None


if __name__ == '__main__':
    import test_appliance
    test_appliance.run(globals())