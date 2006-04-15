
import test_appliance

from yaml import *

class TestTokens(test_appliance.TestAppliance):

    # Tokens mnemonic:
    # directive:            %
    # document_start:       ---
    # document_end:         ...
    # alias:                *
    # anchor:               &
    # tag:                  !
    # scalar                _
    # block_sequence_start: [[
    # block_mapping_start:  {{
    # block_end:            ]}
    # flow_sequence_start:  [
    # flow_sequence_end:    ]
    # flow_mapping_start:   {
    # flow_mapping_end:     }
    # entry:                ,
    # key:                  ?
    # value:                :

    replaces = {
        DirectiveToken: '%',
        DocumentStartToken: '---',
        DocumentEndToken: '...',
        AliasToken: '*',
        AnchorToken: '&',
        TagToken: '!',
        ScalarToken: '_',
        BlockSequenceStartToken: '[[',
        BlockMappingStartToken: '{{',
        BlockEndToken: ']}',
        FlowSequenceStartToken: '[',
        FlowSequenceEndToken: ']',
        FlowMappingStartToken: '{',
        FlowMappingEndToken: '}',
        BlockEntryToken: ',',
        FlowEntryToken: ',',
        KeyToken: '?',
        ValueToken: ':',
    }

    def _testTokens(self, test_name, data_filename, tokens_filename):
        tokens1 = None
        tokens2 = file(tokens_filename, 'rb').read().split()
        try:
            tokens1 = []
            for token in scan(file(data_filename, 'rb')):
                if not isinstance(token, (StreamStartToken, StreamEndToken)):
                    tokens1.append(token)
            tokens1 = [self.replaces[t.__class__] for t in tokens1]
            self.failUnlessEqual(tokens1, tokens2)
        except:
            print
            print "DATA:"
            print file(data_filename, 'rb').read()
            print "TOKENS1:", tokens1
            print "TOKENS2:", tokens2
            raise

TestTokens.add_tests('testTokens', '.data', '.tokens')

class TestScanner(test_appliance.TestAppliance):

    def _testScanner(self, test_name, data_filename, canonical_filename):
        for filename in [canonical_filename, data_filename]:
            tokens = None
            try:
                tokens = []
                for token in scan(file(filename, 'rb')):
                    if not isinstance(token, (StreamStartToken, StreamEndToken)):
                        tokens.append(token.__class__.__name__)
            except:
                print
                print "DATA:"
                print file(data_filename, 'rb').read()
                print "TOKENS:", tokens
                raise

TestScanner.add_tests('testScanner', '.data', '.canonical')

