
import unittest

from test_marker import *
from test_reader import *
from test_canonical import *
from test_tokens import *
from test_structure import *
from test_errors import *
from test_syck import *

def main(module='__main__'):
    unittest.main(module)

if __name__ == '__main__':
    main()

