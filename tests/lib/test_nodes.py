# TODO this is 
from yaml import nodes

def test_scalar(verbose):
    assert repr(nodes.ScalarNode("value", "tag")) \
        == "ScalarNode(tag='tag', value='value')"
test_scalar.unittest = True

def test_null(verbose):
    assert repr(nodes.NullNode()) \
        == "ScalarNode(tag='tag:yaml.org,2002:null', value='null')"
test_null.unittest = True

def test_seq(verbose):
    assert repr(nodes.SequenceNode(value="value")) \
        == "SequenceNode(tag='tag:yaml.org,2002:seq', value='value')"
test_seq.unittest = True 

def test_map(verbose):
    assert repr(nodes.MappingNode(value="value")) \
        == "MappingNode(tag='tag:yaml.org,2002:map', value='value')"
test_map.unittest = True 

if __name__ == '__main__':
    import sys
    sys.modules['test_load'] = sys.modules['__main__']
    import test_appliance
    test_appliance.run(globals())
