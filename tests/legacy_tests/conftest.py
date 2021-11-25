# pytest custom collection adapter for legacy pyyaml unit tests/data files; surfaces each
# legacy test case as a pyyaml item

import os
import pytest
import warnings

from test_appliance import find_test_filenames, DATA

try:
    from yaml import _yaml
    HAS_LIBYAML_EXT = True
    del _yaml
except ImportError:
    HAS_LIBYAML_EXT = False


_test_filenames = find_test_filenames(DATA)

# ignore all datafiles
collect_ignore_glob = ['data/*']


class PyYAMLItem(pytest.Item):
    def __init__(self, parent=None, config=None, session=None, nodeid=None, function=None, filenames=None, **kwargs):
        self._function = function
        self._fargs = filenames or []

        super().__init__(os.path.basename(filenames[0]) if filenames else parent.name, parent, config, session, nodeid)
        # this is gnarly since the type of fspath is private; fixed in pytest 7 to use pathlib on the `path` attr
        if filenames:  # pass the data file location as the test path
            self.fspath = parent.fspath.__class__(filenames[0])
            self.lineno = 1
        else:  # pass the function location in the code
            self.fspath = parent.fspath.__class__(function.__code__.co_filename)
            self.lineno = function.__code__.co_firstlineno

    def runtest(self):
        self._function(verbose=True, *self._fargs)

    def reportinfo(self):
        return self.fspath, self.lineno, ''


class PyYAMLCollector(pytest.Collector):
    def __init__(self, name, parent=None, function=None, **kwargs):
        self._function = function
        self.fspath = parent.fspath.__class__(function.__code__.co_filename)
        self.lineno = function.__code__.co_firstlineno

        # avoid fspath deprecation warnings on pytest < 7
        if hasattr(self, 'path') and 'fspath' in kwargs:
            del kwargs['fspath']

        super().__init__(name=name, parent=parent, **kwargs)

    def collect(self):
        items = []

        unittest = getattr(self._function, 'unittest', None)

        if unittest is True:  # no filenames
            items.append(PyYAMLItem.from_parent(parent=self, function=self._function, filenames=None))
        else:
            for base, exts in _test_filenames:
                filenames = []
                for ext in unittest:
                    if ext not in exts:
                        break
                    filenames.append(os.path.join(DATA, base + ext))
                else:
                    skip_exts = getattr(self._function, 'skip', [])
                    for skip_ext in skip_exts:
                        if skip_ext in exts:
                            break
                    else:
                        items.append(PyYAMLItem.from_parent(parent=self, function=self._function, filenames=filenames))

        return items or None

    def reportinfo(self):
        return self.fspath, self.lineno, ''

    @classmethod
    def from_parent(cls, parent, fspath, **kwargs):
        return super().from_parent(parent=parent, fspath=fspath, **kwargs)


@pytest.hookimpl(hookwrapper=True, trylast=True)
def pytest_pycollect_makeitem(collector, name: str, obj: object):
    outcome = yield
    outcome.get_result()
    if not callable(obj):
        outcome.force_result(None)
        return
    unittest = getattr(obj, 'unittest', None)

    if not unittest:
        outcome.force_result(None)
        return

    if unittest is True:  # no file list to run against, just return a test item instead of a collector
        outcome.force_result(PyYAMLItem.from_parent(name=name, parent=collector, fspath=collector.fspath, function=obj))
        return

    # there's a file list; return a collector to create individual items for each
    outcome.force_result(PyYAMLCollector.from_parent(name=name, parent=collector, fspath=collector.fspath, function=obj))
    return


def pytest_collection_modifyitems(session, config, items):
    pass

def pytest_ignore_collect(path, config):
    basename = path.basename
    # ignore all Python files in this subtree for normal pytest collection
    if basename not in ['test_yaml.py', 'test_yaml_ext.py']:
        return True

    # ignore extension tests (depending on config)
    if basename == 'test_yaml_ext.py':
        require_libyaml = os.environ.get('PYYAML_FORCE_LIBYAML', None)
        if require_libyaml == '1' and not HAS_LIBYAML_EXT:
            raise RuntimeError('PYYAML_FORCE_LIBYAML envvar is set, but libyaml extension is not available')
        if require_libyaml == '0':
            return True
        if not HAS_LIBYAML_EXT:
            warnings.warn('libyaml extension is not available, skipping libyaml tests')
            return True

