
import unittest
from yaml import *

RECURSIVE = """
--- &A
- *A: *A
"""

class TestRecursive(unittest.TestCase):

    def testRecursive(self):
        node = compose(RECURSIVE)
        self._check(node)
        document = serialize(node)
        node = compose(document)
        self._check(node)

    def _check(self, node):
        self.failUnless(node in node.value[0].value)
        self.failUnless(node.value[0].value[node] is node)

