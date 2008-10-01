
NAME = 'PyYAML'
VERSION = '3.06'
DESCRIPTION = "YAML parser and emitter for Python"
LONG_DESCRIPTION = """\
YAML is a data serialization format designed for human readability and
interaction with scripting languages.  PyYAML is a YAML parser and
emitter for Python.

PyYAML features a complete YAML 1.1 parser, Unicode support, pickle
support, capable extension API, and sensible error messages.  PyYAML
supports standard YAML tags and provides Python-specific tags that allow
to represent an arbitrary Python object.

PyYAML is applicable for a broad range of tasks from complex
configuration files to object serialization and persistance."""
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
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: Text Processing :: Markup",
]


from distutils.core import setup, Command
from distutils.core import Distribution as _Distribution
from distutils.core import Extension as _Extension
from distutils.command.build_ext import build_ext as _build_ext

try:
    from Pyrex.Distutils import Extension as _Extension
    from Pyrex.Distutils import build_ext as _build_ext
    with_pyrex = True
except ImportError:
    with_pyrex = False

import sys, os.path


class Distribution(_Distribution):

    def __init__(self, attrs=None):
        _Distribution.__init__(self, attrs)
        if not self.ext_modules:
            return
        for ext in reversed(self.ext_modules):
            if not isinstance(ext, Extension):
                continue
            setattr(self, ext.attr_name, None)
            self.global_options = [
                    (ext.option_name, None,
                        "include %s" % ext.feature_description),
                    (ext.neg_option_name, None,
                        "exclude %s (default)" % ext.feature_description),
            ] + self.global_options
            self.negative_opt = self.negative_opt.copy()
            self.negative_opt[ext.neg_option_name] = ext.option_name


class Extension(_Extension):

    def __init__(self, name, sources, feature_name, feature_description, **kwds):
        if not with_pyrex:
            for filename in sources[:]:
                base, ext = os.path.splitext(filename)
                if ext == 'pyx':
                    sources.replace(filename, '%s.c' % base)
        _Extension.__init__(self, name, sources, **kwds)
        self.feature_name = feature_name
        self.feature_description = feature_description
        self.attr_name = 'with_' + feature_name.replace('-', '_')
        self.option_name = 'with-' + feature_name
        self.neg_option_name = 'without-' + feature_name


class build_ext(_build_ext):

    def get_source_files(self):
        self.check_extensions_list(self.extensions)
        filenames = []
        for ext in self.extensions:
            if with_pyrex:
                self.pyrex_sources(ext.sources, ext)
            for filename in ext.sources:
                filenames.append(filename)
                base = os.path.splitext(filename)[0]
                for ext in ['c', 'h', 'pyx', 'pxd']:
                    filename = '%s.%s' % (base, ext)
                    if filename not in filenames and os.path.isfile(filename):
                        filenames.append(filename)
        return filenames

    def build_extensions(self):
        self.check_extensions_list(self.extensions)
        for ext in self.extensions:
            if isinstance(ext, Extension):
                if not getattr(self.distribution, ext.attr_name):
                    continue
            if with_pyrex:
                ext.sources = self.pyrex_sources(ext.sources, ext)
            self.build_extension(ext)


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
        sys.path.insert(0, 'tests')
        import test_all
        test_all.main()


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
            Extension('yaml/_yaml', ['ext/_yaml.pyx'],
                'libyaml', "LibYAML bindings",
                libraries=['yaml']),
        ],

        distclass=Distribution,
        cmdclass={
            'build_ext': build_ext,
            'test': test,
        },
    )

