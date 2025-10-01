
NAME = 'PyYAML'
VERSION = '6.0.1'
DESCRIPTION = "YAML parser and emitter for Python"
LONG_DESCRIPTION = """\
YAML is a data serialization format designed for human readability
and interaction with scripting languages.  PyYAML is a YAML parser
and emitter for Python.

PyYAML features a complete YAML 1.1 parser, Unicode support, pickle
support, capable extension API, and sensible error messages.  PyYAML
supports standard YAML tags and provides Python-specific tags that
allow to represent an arbitrary Python object.

PyYAML is applicable for a broad range of tasks from complex
configuration files to object serialization and persistence."""
AUTHOR = "Kirill Simonov"
AUTHOR_EMAIL = 'xi@resolvent.net'
LICENSE = "MIT"
PLATFORMS = "Any"
URL = "https://pyyaml.org/"
DOWNLOAD_URL = "https://pypi.org/project/PyYAML/"
CLASSIFIERS = [
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Cython",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.6",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: Implementation :: CPython",
    "Programming Language :: Python :: Implementation :: PyPy",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: Text Processing :: Markup",
]
PROJECT_URLS = {
   'Bug Tracker': 'https://github.com/yaml/pyyaml/issues',
   'CI': 'https://github.com/yaml/pyyaml/actions',
   'Documentation': 'https://pyyaml.org/wiki/PyYAMLDocumentation',
   'Mailing lists': 'http://lists.sourceforge.net/lists/listinfo/yaml-core',
   'Source Code': 'https://github.com/yaml/pyyaml',
}

LIBYAML_CHECK = """
#include <yaml.h>

int main(void) {
    yaml_parser_t parser;
    yaml_emitter_t emitter;

    yaml_parser_initialize(&parser);
    yaml_parser_delete(&parser);

    yaml_emitter_initialize(&emitter);
    yaml_emitter_delete(&emitter);

    return 0;
}
"""


import sys, os, os.path, pathlib, platform, shutil, tempfile, warnings

# for newer setuptools, enable the embedded distutils before importing setuptools/distutils to avoid warnings
os.environ['SETUPTOOLS_USE_DISTUTILS'] = 'local'

from setuptools import setup, Command, Distribution, Extension
from setuptools.command.build_ext import build_ext
# NB: distutils imports must remain below setuptools to ensure we use the embedded version
from distutils import log
from distutils.errors import DistutilsError, CompileError, LinkError, DistutilsPlatformError

with_cython = False
if 'sdist' in sys.argv or os.environ.get('PYYAML_FORCE_CYTHON') == '1':
    # we need cython here
    with_cython = True
try:
    from Cython.Distutils.extension import Extension as _Extension
    try:
        from Cython.Distutils.old_build_ext import old_build_ext as _build_ext
    except ImportError:
        from Cython.Distutils import build_ext as _build_ext

    with_cython = True
except ImportError:
    if with_cython:
        raise

try:
    from wheel.bdist_wheel import bdist_wheel
except ImportError:
    bdist_wheel = None


# on Windows, disable wheel generation warning noise
windows_ignore_warnings = [
"Unknown distribution option: 'python_requires'",
"Config variable 'Py_DEBUG' is unset",
"Config variable 'WITH_PYMALLOC' is unset",
"Config variable 'Py_UNICODE_SIZE' is unset",
"Cython directive 'language_level' not set"
]

if platform.system() == 'Windows':
    for w in windows_ignore_warnings:
        warnings.filterwarnings('ignore', w)


class test(Command):

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        build_cmd = self.get_finalized_command('build')
        build_cmd.run()

        # running the tests this way can pollute the post-MANIFEST build sources
        # (see https://github.com/yaml/pyyaml/issues/527#issuecomment-921058344)
        # until we remove the test command, run tests from an ephemeral copy of the intermediate build sources
        tempdir = tempfile.TemporaryDirectory(prefix='test_pyyaml')

        try:
            # have to create a subdir since we don't get dir_exists_ok on copytree until 3.8
            temp_test_path = pathlib.Path(tempdir.name) / 'pyyaml'
            shutil.copytree(build_cmd.build_lib, temp_test_path)
            sys.path.insert(0, str(temp_test_path))
            sys.path.insert(0, 'tests/lib')

            import test_all
            if not test_all.main([]):
                raise DistutilsError("Tests failed")
        finally:
            try:
                # this can fail under Windows; best-effort cleanup
                tempdir.cleanup()
            except Exception:
                pass


cmdclass = {
    'build_ext': build_ext,
    'test': test,
}
if bdist_wheel:
    cmdclass['bdist_wheel'] = bdist_wheel


if __name__ == '__main__':
    from Cython.Build import cythonize

    ext_modules = cythonize([
        Extension(
            name='yaml._yaml',
            sources=['yaml/_yaml.pyx'],
            libraries=['yaml'],
        )
    ])

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
        project_urls=PROJECT_URLS,

        package_dir={'': 'lib'},
        packages=['yaml', '_yaml'],
        ext_modules=ext_modules,

        distclass=Distribution,
        cmdclass=cmdclass,
        python_requires='>=3.6',
    )
