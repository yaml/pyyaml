
from setup import *

from distutils.core import setup
from distutils.extension import Extension
from Pyrex.Distutils import build_ext

if __name__ == '__main__':

    setup(
        name=NAME,
        version=VERSION,
        description=DESCRIPTION,
        long_description=LONG_DESCRIPTION,
        author=AUTHOR,
        author_email=AUTHOR_EMAIL,
        license=LICENSE,
        platforms=PLATFORMS,
        url=URL,
        download_url=DOWNLOAD_URL,
        classifiers=CLASSIFIERS,

        package_dir={'': 'lib'},
        packages=['yaml'],
        ext_modules=[
            Extension("_yaml", ["ext/_yaml.pyx"], libraries=['yaml']),
        ],

        cmdclass = {'build_ext': build_ext}
    )

