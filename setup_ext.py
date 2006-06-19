
from distutils.core import setup
from distutils.extension import Extension
from Pyrex.Distutils import build_ext

setup(
    name = '_yaml',
    ext_modules=[
        Extension("_yaml", ["ext/_yaml.pyx"], libraries=['yaml']),
    ],
    cmdclass = {'build_ext': build_ext}
)

