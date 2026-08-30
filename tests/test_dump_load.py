import subprocess
import sys
import textwrap

import pytest
import yaml


def test_dump():
    assert yaml.dump(['foo'])


def test_load_no_loader():
    with pytest.raises(TypeError):
        yaml.load("- foo\n")


def test_load_safeloader():
    assert yaml.load("- foo\n", Loader=yaml.SafeLoader)


@pytest.mark.skipif(not yaml.__with_libyaml__,
                     reason="requires the libyaml C extension")
def test_cdumper_reentrant_close_from_write_raises_instead_of_crashing():
    # A stream write() callback that calls close() on the dumper it's
    # writing for used to corrupt the C emitter's internal state badly
    # enough to abort the process during cleanup, instead of raising.
    # Runs in a subprocess so a regression here crashes that process,
    # not this test run.
    script = textwrap.dedent("""
        import yaml

        class ReentrantStream:
            def __init__(self):
                self.dumper = None
                self.called = False

            def write(self, value):
                if not self.called:
                    self.called = True
                    self.dumper.close()

        class ReentrantDumper(yaml.CDumper):
            def __init__(self, stream, *args, **kwargs):
                super().__init__(stream, *args, **kwargs)
                stream.dumper = self

        try:
            yaml.dump("value", ReentrantStream(), Dumper=ReentrantDumper)
        except RuntimeError:
            print("raised-cleanly")
        else:
            print("no-error-raised")
    """)
    result = subprocess.run(
        [sys.executable, '-c', script],
        capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, (
        f"subprocess terminated abnormally (returncode={result.returncode}): "
        f"{result.stderr}")
    assert result.stdout.strip() == "raised-cleanly"
