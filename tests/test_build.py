
def main():
    import sys, os, distutils.util
    #build_lib = os.path.join('build', 'lib.%s-%s' % (distutils.util.get_platform(), sys.version[0:3]))
    build_lib = 'build/lib'
    sys.path.insert(0, build_lib)
    import test_yaml
    test_yaml.main('test_yaml')

if __name__ == '__main__':
    main()

