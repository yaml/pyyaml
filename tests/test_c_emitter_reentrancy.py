import os
from pathlib import Path
import subprocess
import sys
import textwrap

import pytest
import yaml


@pytest.mark.skipif(not yaml.__with_libyaml__, reason="requires LibYAML")
@pytest.mark.parametrize("emitter_type", ["CEmitter", "CBaseDumper", "CSafeDumper", "CDumper"])
@pytest.mark.parametrize("operation", ["open", "close", "emit", "serialize", "__init__"])
@pytest.mark.parametrize("catch_error", [False, True])
def test_reentrant_write(emitter_type, operation, catch_error):
    # Keep regressions in the native emitter from crashing the test runner.
    script = textwrap.dedent("""
        import io
        import sys
        import yaml
        from yaml._yaml import CEmitter
        from yaml.emitter import EmitterError
        from yaml.serializer import SerializerError

        emitter_type, operation, catch_error = sys.argv[1:]
        emitter_class = CEmitter if emitter_type == 'CEmitter' else getattr(yaml, emitter_type)
        node = yaml.ScalarNode('tag:yaml.org,2002:str', 'value')

        def write_document(emitter, node):
            if emitter_type == 'CEmitter':
                emitter.emit(yaml.DocumentStartEvent())
                emitter.emit(yaml.ScalarEvent(None, node.tag, (True, True), node.value))
                emitter.emit(yaml.DocumentEndEvent())
            else:
                emitter.serialize(node)

        class Stream(io.StringIO):
            attempted = False
            rejected = False

            def write(self, value):
                if not self.attempted:
                    self.attempted = True
                    args = {
                        'open': (), 'close': (),
                        'emit': (yaml.StreamEndEvent(),),
                        'serialize': (node,), '__init__': (self,),
                    }[operation]
                    try:
                        getattr(self.emitter, operation)(*args)
                    except EmitterError as error:
                        assert 'reentrant' in str(error)
                        self.rejected = True
                        if catch_error == 'False':
                            raise
                return super().write(value)

        stream = Stream()
        emitter = stream.emitter = emitter_class(stream)
        try:
            emitter.open()
            write_document(emitter, node)
            write_document(emitter, yaml.ScalarNode('tag:yaml.org,2002:str', 'next'))
            emitter.close()
        except EmitterError:
            assert catch_error == 'False'
            # The guard must be released even when stream.write() raises.
            try:
                emitter.open()
            except SerializerError:
                pass
            else:
                raise AssertionError('serializer should already be open')
        else:
            assert catch_error == 'True'
            assert list(yaml.safe_load_all(stream.getvalue())) == ['value', 'next']
        finally:
            emitter.dispose()
        assert stream.attempted and stream.rejected

        # A failed callback must not affect a separate emitter.
        clean = io.StringIO()
        other = emitter_class(clean)
        try:
            other.open()
            write_document(other, node)
            other.close()
        finally:
            other.dispose()
        assert yaml.safe_load(clean.getvalue()) == 'value'
        print('ok')
    """)
    env = os.environ.copy()
    # Use the exact build under test, including when pytest adds it to sys.path.
    env["PYTHONPATH"] = str(Path(yaml.__file__).resolve().parent.parent)
    result = subprocess.run(
        [sys.executable, "-c", script, emitter_type, operation, str(catch_error)],
        env=env, capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "ok"
