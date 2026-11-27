import datetime

import pytest
import yaml


def test_dump():
    assert yaml.dump(['foo'])


def test_load_no_loader():
    with pytest.raises(TypeError):
        yaml.load("- foo\n")


def test_load_safeloader():
    assert yaml.load("- foo\n", Loader=yaml.SafeLoader)


def safe_implementations():
    implementations = [(yaml.SafeDumper, yaml.SafeLoader)]
    if hasattr(yaml, 'CSafeDumper'):
        implementations.append((yaml.CSafeDumper, yaml.CSafeLoader))
    return implementations


@pytest.mark.parametrize('Dumper,Loader', safe_implementations())
@pytest.mark.parametrize('offset', [
    datetime.timedelta(seconds=30),
    datetime.timedelta(seconds=-30),
    datetime.timedelta(minutes=19, seconds=32),
    datetime.timedelta(microseconds=1),
    datetime.timedelta(microseconds=-1),
])
def test_datetime_subminute_offset_roundtrip(offset, Dumper, Loader):
    value = datetime.datetime(2024, 1, 1,
                              tzinfo=datetime.timezone(offset))
    dumped = yaml.dump(value, Dumper=Dumper)
    loaded = yaml.load(dumped, Loader=Loader)
    assert loaded == value
    assert loaded.utcoffset() == datetime.timedelta(0)


@pytest.mark.parametrize('Dumper,Loader', safe_implementations())
@pytest.mark.parametrize('offset', [None, datetime.timedelta(0),
                                  datetime.timedelta(hours=5, minutes=30),
                                  datetime.timedelta(hours=-3, minutes=-30)])
def test_datetime_whole_minute_offset_unchanged(offset, Dumper, Loader):
    tzinfo = datetime.timezone(offset) if offset is not None else None
    value = datetime.datetime(2024, 1, 1, tzinfo=tzinfo)
    dumped = yaml.dump(value, Dumper=Dumper)
    assert dumped.splitlines()[0] == value.isoformat(' ')
    loaded = yaml.load(dumped, Loader=Loader)
    assert loaded == value
    assert loaded.utcoffset() == offset


@pytest.mark.parametrize('Dumper,Loader', safe_implementations())
@pytest.mark.parametrize('value', [
    datetime.datetime.min.replace(
        tzinfo=datetime.timezone(datetime.timedelta(seconds=30))),
    datetime.datetime.max.replace(
        tzinfo=datetime.timezone(datetime.timedelta(seconds=-30))),
])
def test_datetime_subminute_offset_outside_utc_range(value, Dumper, Loader):
    with pytest.raises(yaml.representer.RepresenterError,
                       match='outside UTC range'):
        yaml.dump(value, Dumper=Dumper)
