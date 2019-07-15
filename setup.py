
NAME = 'PyYAML'
VERSION = '3.12'
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
URL = "http://pyyaml.org/wiki/PyYAML"
DOWNLOAD_URL = "http://pyyaml.org/download/pyyaml/%s-%s.tar.gz" % (NAME, VERSION)
CLASSIFIERS = [
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Programming Language :: Python :: 2",
    "Programming Language :: Python :: 2.6",
    "Programming Language :: Python :: 2.7",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.4",
    "Programming Language :: Python :: 3.5",
    "Programming Language :: Python :: 3.6",
    "Programming Language :: Python :: Implementation :: CPython",
    "Programming Language :: Python :: Implementation :: PyPy",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: Text Processing :: Markup",
]


import sys, os.path, platform

from distutils import log
from distutils.core import setup, Command
from distutils.core import Distribution as _Distribution
from distutils.core import Extension as _Extension
from distutils.dir_util import mkpath
from distutils.errors import DistutilsError, CompileError, LinkError, DistutilsPlatformError

class Distribution(_Distribution):

    def __init__(self, attrs=None):
        _Distribution.__init__(self, attrs)
        if not self.ext_modules:
            return
        for idx in range(len(self.ext_modules)-1, -1, -1):
            ext = self.ext_modules[idx]
            if not isinstance(ext, Extension):
                continue
            setattr(self, ext.attr_name, None)
            self.global_options = [
                    (ext.option_name, None,
                        "include %s (default if %s is available)"
                        % (ext.feature_description, ext.feature_name)),
                    (ext.neg_option_name, None,
                        "exclude %s" % ext.feature_description),
            ] + self.global_options
            self.negative_opt = self.negative_opt.copy()
            self.negative_opt[ext.neg_option_name] = ext.option_name

    def has_ext_modules(self):
        if not self.ext_modules:
            return False
        for ext in self.ext_modules:
            with_ext = self.ext_status(ext)
            if with_ext is None or with_ext:
                return True
        return False

    def ext_status(self, ext):
        implementation = platform.python_implementation()
        if implementation != 'CPython':
            return False
        if isinstance(ext, Extension):
            with_ext = getattr(self, ext.attr_name)
            return with_ext
        else:
            return True


class Extension(_Extension):

    def __init__(self, name, sources, feature_name, feature_description,
            feature_check, **kwds):
        if not with_cython:
            for filename in sources[:]:
                base, ext = os.path.splitext(filename)
                if ext == '.pyx':
                    sources.remove(filename)
                    sources.append('%s.c' % base)
        _Extension.__init__(self, name, sources, **kwds)
        self.feature_name = feature_name
        self.feature_description = feature_description
        self.feature_check = feature_check
        self.attr_name = 'with_' + feature_name.replace('-', '_')
        self.option_name = 'with-' + feature_name
        self.neg_option_name = 'without-' + feature_name


class test(Command):

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        build_cmd = self.get_finalized_command('build')
        build_cmd.run()
        sys.path.insert(0, build_cmd.build_lib)
        sys.path.insert(0, 'tests/lib')
        import test_all
        if not test_all.main([]):
            raise DistutilsError("Tests failed")


cmdclass = {
    'test': test,
}

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

        cmdclass=cmdclass,
    )
