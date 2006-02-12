
import unittest, os

class TestAppliance(unittest.TestCase):

    DATA = 'tests/data'

    tests = {}
    for filename in os.listdir(DATA):
        if os.path.isfile(os.path.join(DATA, filename)):
            root, ext = os.path.splitext(filename)
            tests.setdefault(root, []).append(ext)

    def add_tests(cls, method_name, *extensions):
        for test in cls.tests:
            available_extensions = cls.tests[test]
            for ext in extensions:
                if ext not in available_extensions:
                    break
            else:
                filenames = [os.path.join(cls.DATA, test+ext) for ext in extensions]
                def test_method(self, test=test, filenames=filenames):
                    getattr(self, '_'+method_name)(test, *filenames)
                test = test.replace('-', '_')
                test_method.__name__ = '%s_%s' % (method_name, test)
                setattr(cls, test_method.__name__, test_method)
    add_tests = classmethod(add_tests)

