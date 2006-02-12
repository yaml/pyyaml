
import test_appliance

from yaml.scanner import Scanner

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
        'DIRECTIVE': '%',
        'DOCUMENT_START': '---',
        'DOCUMENT_END': '...',
        'ALIAS': '*',
        'ANCHOR': '&',
        'TAG': '!',
        'SCALAR': '_',
        'BLOCK_SEQ_START': '[[',
        'BLOCK_MAP_START': '{{',
        'BLOCK_END': ']}',
        'FLOW_SEQ_START': '[',
        'FLOW_SEQ_END': ']',
        'FLOW_MAP_START': '{',
        'FLOW_MAP_END': '}',
        'ENTRY': ',',
        'KEY': '?',
        'VALUE': ':',
    }

    def _testTokens(self, test_name, data_filename, tokens_filename):
        tokens1 = None
        tokens2 = file(tokens_filename, 'rb').read().split()
        try:
            scanner = Scanner()
            tokens1 = scanner.scan(data_filename, file(data_filename, 'rb').read())
            tokens1 = [self.replaces[t] for t in tokens1]
            self.failUnlessEqual(tokens1, tokens2)
        except:
            print
            print "TOKENS1:", tokens1
            print "TOKENS2:", tokens2
            raise

TestTokens.add_tests('testTokens', '.data', '.tokens')

