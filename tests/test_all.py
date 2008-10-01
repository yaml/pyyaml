
import unittest

def main():
    import yaml
    names = ['test_yaml']
    if yaml.__libyaml__:
        names.append('test_yaml_ext')
    suite = unittest.defaultTestLoader.loadTestsFromNames(names)
    runner = unittest.TextTestRunner()
    runner.run(suite)

if __name__ == '__main__':
    main()

