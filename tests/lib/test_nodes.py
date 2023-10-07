from yaml import nodes

def test_scalar(verbose):
    assert repr(nodes.ScalarNode("value", "tag")) \
        == "ScalarNode(tag='tag', value='value')"
test_scalar.unittest = True

def test_string(verbose):
    assert repr(nodes.StringNode("value")) \
        == "ScalarNode(tag='tag:yaml.org,2002:str', value='value')"
test_string.unittest = True

def test_empty_string(verbose):
    assert repr(nodes.StringNode()) \
        == "ScalarNode(tag='tag:yaml.org,2002:str', value='')"
test_empty_string.unittest = True

def test_null(verbose):
    assert repr(nodes.NullNode()) \
        == "ScalarNode(tag='tag:yaml.org,2002:null', value='null')"
test_null.unittest = True

def test_seq(verbose):
    assert repr(nodes.SequenceNode(value=(nodes.NullNode(),))) \
        == "SequenceNode(tag='tag:yaml.org,2002:seq', value=[ScalarNode(tag='tag:yaml.org,2002:null', value='null')])"
test_seq.unittest = True 

def test_empty_seq(verbose):
    assert repr(nodes.SequenceNode()) \
        == "SequenceNode(tag='tag:yaml.org,2002:seq', value=[])"
test_empty_seq.unittest = True 

def test_map(verbose):
    left = nodes.StringNode()
    right = nodes.NullNode()
    assert repr(nodes.MappingNode({left: right})) \
        == "MappingNode(tag='tag:yaml.org,2002:map', value={ScalarNode(tag='tag:yaml.org,2002:str', value=''): ScalarNode(tag='tag:yaml.org,2002:null', value='null')})"
test_map.unittest = True 

def test_empty_map(verbose):
    assert repr(nodes.MappingNode()) \
        == "MappingNode(tag='tag:yaml.org,2002:map', value={})"
test_empty_map.unittest = True 

if __name__ == '__main__':
    import sys
    sys.modules['test_load'] = sys.modules['__main__']
    import test_appliance
    test_appliance.run(globals())
