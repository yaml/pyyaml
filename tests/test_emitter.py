
import test_appliance, sys

from yaml import *

class TestEmitterOnCanonical(test_appliance.TestAppliance):

    def _testEmitterOnCanonical(self, test_name, canonical_filename):
        events = list(iter(Parser(Scanner(Reader(file(canonical_filename, 'rb'))))))
        writer = sys.stdout
        emitter = Emitter(writer)
        print "-"*30
        print "ORIGINAL DATA:"
        print file(canonical_filename, 'rb').read()
        for event in events:
            emitter.emit(event)

TestEmitterOnCanonical.add_tests('testEmitterOnCanonical', '.canonical')

