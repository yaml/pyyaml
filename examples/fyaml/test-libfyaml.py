#!/usr/bin/env python3

if __name__ == '__main__':

    # import the yaml module in the build/lib directory
    import sys, os, distutils.util
    build_lib = 'build/lib'
    build_lib_ext = os.path.join('build', 'lib.{}-{}.{}'.format(distutils.util.get_platform(), *sys.version_info))
    sys.path.insert(0, build_lib)
    sys.path.insert(0, build_lib_ext)

    import yaml._fyaml, yaml
    import types, pprint, tempfile, sys, os

    version = yaml._fyaml.get_version_string()

    print("libfyaml version:", version)

    obj = yaml.load("""
        - Hesperiidae
        - Papilionidae
        - Apatelodidae
        - Epiplemidae
        """, Loader=yaml.FLoader)
    assert (obj != None)
    print(obj)

    obj = yaml.load("""
        foo
        """, Loader=yaml.FLoader)
    assert (obj != None)
    print(obj)

    obj = yaml.load("""
        foo: bar
        """, Loader=yaml.FLoader)
    assert (obj != None)
    print(obj)

    obj = yaml.load("""
        foo: bar
        baz: frooz
        seq: [ 1, 2, 3 ]
        """, Loader=yaml.FLoader)
    assert (obj != None)
    print(obj)

    obj = yaml.load("""
        - &foo Hesperiidae
        - *foo
        """, Loader=yaml.FLoader)
    assert (obj != None)
    print(obj)

    obj = yaml.load("""
        - Hesperiidae
        - !!str "10"
        """, Loader=yaml.FLoader)
    assert (obj != None)
    print(obj)

    document = """
                foo: bar
                "bar":
                  - baz
                  - 1
                test: |
                  literal
               """

    print("scan, python loader")
    tokens = yaml.scan(document, Loader=yaml.Loader)
    for token in tokens:
        print("  ", token)

    print("scan, f loader")
    tokens = yaml.scan(document, Loader=yaml.FLoader)
    for token in tokens:
        print("  ", token)

    print("parse, python loader")
    events = yaml.parse(document, Loader=yaml.Loader)
    for event in events:
        print("  ", event)

    print("parse, f loader")
    events = yaml.parse(document, Loader=yaml.FLoader)
    for event in events:
        print("  ", event)

    document = """
        ? |-
          foo
        : |-
          bar
        """

    print("parse, python loader")
    events = yaml.parse(document, Loader=yaml.Loader)
    for event in events:
        print("  ", event)

    print("parse, f loader")
    events = yaml.parse(document, Loader=yaml.FLoader)
    for event in events:
        print("  ", event)

    print("test, native emitter")
    print(yaml.dump('scalar'))

    print("test, f emitter")
    print(yaml.dump('scalar', Dumper=yaml.FDumper))

    print("test, f emitter (2)")
    print(yaml.dump({'name': 'Silenthand Olleander', 'race': 'Human', 'traits': ['ONE_HAND', 'ONE_EYE']}, Dumper=yaml.FDumper))

