
import yaml
import test_constructor
import pprint

def test_representer_types(code_filename, verbose=False):
    test_constructor._make_objects()
    for allow_unicode in [False, True]:
        for encoding in ['utf-8', 'utf-16-be', 'utf-16-le']:
            with open(code_filename, 'rb') as file:
                native1 = test_constructor._load_code(file.read())
            native2 = None
            try:
                output = yaml.dump(native1, Dumper=test_constructor.MyDumper,
                            allow_unicode=allow_unicode, encoding=encoding)
                native2 = yaml.load(output, Loader=test_constructor.MyLoader)
                try:
                    if native1 == native2:
                        continue
                except TypeError:
                    pass
                value1 = test_constructor._serialize_value(native1)
                value2 = test_constructor._serialize_value(native2)
                if verbose:
                    print("SERIALIZED NATIVE1:")
                    print(value1)
                    print("SERIALIZED NATIVE2:")
                    print(value2)
                assert value1 == value2, (native1, native2)
            finally:
                if verbose:
                    print("NATIVE1:")
                    pprint.pprint(native1)
                    print("NATIVE2:")
                    pprint.pprint(native2)
                    print("OUTPUT:")
                    print(output)

test_representer_types.unittest = ['.code']

def test_representer_inheritance(verbose=False):
    class Widget:
        pass

    class Gizmo:
        pass

    def represent_widget(representer, obj):
        return representer.represent_scalar("!widget", "widget")

    def represent_gizmo1(representer, obj):
        return representer.represent_scalar("!gizmo", "gizmo1")

    def represent_gizmo2(representer, obj):
        return representer.represent_scalar("!gizmo", "gizmo2")

    def represent_gizmo3(representer, obj):
        return representer.represent_scalar("!gizmo", "gizmo3")

    class DumperParent(yaml.Dumper):
        pass

    class DumperChild(DumperParent):
        pass

    # Add a representer to the child.  Note that no representer has been added
    # to the parent yet.
    DumperChild.add_representer(Widget, represent_widget)
    if verbose:
        print("After adding a representer to the child Dumper:")
        print(f"  {DumperParent.yaml_representers=}")
        print(f"  {DumperChild.yaml_representers=}")
    assert DumperChild.yaml_representers[Widget] is represent_widget
    assert Widget not in DumperParent.yaml_representers

    # A representer is now added to the parent.  The child should be able to see
    # this new representer even though it was added after a representer was
    # added to the child above.
    DumperParent.add_representer(Gizmo, represent_gizmo1)
    if verbose:
        print("After adding a representer to the parent Dumper:")
        print(f"  {DumperParent.yaml_representers=}")
        print(f"  {DumperChild.yaml_representers=}")
    assert DumperChild.yaml_representers[Widget] is represent_widget
    assert Widget not in DumperParent.yaml_representers
    assert DumperParent.yaml_representers[Gizmo] is represent_gizmo1
    assert DumperChild.yaml_representers[Gizmo] is represent_gizmo1

    # Override a parent representer in the child.
    DumperChild.add_representer(Gizmo, represent_gizmo2)
    if verbose:
        print("After overriding a parent's representer:")
        print(f"  {DumperParent.yaml_representers=}")
        print(f"  {DumperChild.yaml_representers=}")
    assert DumperChild.yaml_representers[Widget] is represent_widget
    assert Widget not in DumperParent.yaml_representers
    assert DumperParent.yaml_representers[Gizmo] is represent_gizmo1
    assert DumperChild.yaml_representers[Gizmo] is represent_gizmo2

    # Changing the parent's overridden representer should not affect the child.
    DumperParent.add_representer(Gizmo, represent_gizmo3)
    if verbose:
        print("After changing the parent's overridden representer:")
        print(f"  {DumperParent.yaml_representers=}")
        print(f"  {DumperChild.yaml_representers=}")
    assert DumperChild.yaml_representers[Widget] is represent_widget
    assert Widget not in DumperParent.yaml_representers
    assert DumperParent.yaml_representers[Gizmo] is represent_gizmo3
    assert DumperChild.yaml_representers[Gizmo] is represent_gizmo2

test_representer_inheritance.unittest = True

if __name__ == '__main__':
    import test_appliance
    test_appliance.run(globals())

