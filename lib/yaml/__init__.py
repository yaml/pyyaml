
from error import *

from reader import *
from scanner import *
from parser import *
from composer import *
from resolver import *
from constructor import *

from emitter import *
from serializer import *
from representer import *

from detector import *

from tokens import *
from events import *
from nodes import *

from yaml_object import *

def parse(data, Reader=Reader, Scanner=Scanner, Parser=Parser):
    reader = Reader(data)
    scanner = Scanner(reader)
    parser = Parser(scanner)
    return parser

def load_all(data, Reader=Reader, Scanner=Scanner, Parser=Parser,
        Composer=Composer, Resolver=Resolver, Constructor=Constructor):
    reader = Reader(data)
    scanner = Scanner(reader)
    parser = Parser(scanner)
    composer = Composer(parser)
    resolver = Resolver(composer)
    constructor = Constructor(resolver)
    return constructor

def safe_load_all(data, Reader=Reader, Scanner=Scanner, Parser=Parser,
        Composer=Composer, Resolver=Resolver, Constructor=SafeConstructor):
    return load_all(data, Reader, Scanner, Parser, Composer, Resolver,
            Constructor)

def load(data, *args, **kwds):
    for document in load_all(data, *args, **kwds):
        return document

def safe_load(data, *args, **kwds):
    for document in safe_load_all(data, *args, **kwds):
        return document

def emit(events, writer=None, Emitter=Emitter):
    if writer is None:
        try:
            from cStringIO import StringIO
        except ImportError:
            from StringIO import StringIO
        writer = StringIO()
        return_value = True
    else:
        return_value = False
    emitter = Emitter(writer)
    for event in events:
        emitter.emit(event)
    if return_value:
        return writer.getvalue()

def dump_all(natives, writer=None, Emitter=Emitter,
        Serializer=Serializer, Representer=Representer,
        encoding='utf-8', line_break=None, canonical=None,
        indent=None, width=None, allow_unicode=None):
    if writer is None:
        try:
            from cStringIO import StringIO
        except ImportError:
            from StringIO import StringIO
        writer = StringIO()
        return_value = True
    else:
        return_value = False
    emitter = Emitter(writer)
    serializer = Serializer(emitter, encoding=encoding, line_break=line_break,
            canonical=canonical, indent=indent, width=width,
            allow_unicode=allow_unicode)
    representer = Representer(serializer)
    for native in natives:
        representer.represent(native)
    representer.close()
    if return_value:
        return writer.getvalue()

def safe_dump_all(natives, writer=None, Emitter=Emitter,
        Serializer=Serializer, Representer=SafeRepresenter,
        encoding='utf-8', line_break=None, canonical=None,
        indent=None, width=None, allow_unicode=None):
    return dump_all(natives, writer, Emitter, Serializer, Representer,
            encoding, line_break, canonical, indent, width, allow_unicode)

def dump(native, *args, **kwds):
    return dump_all([native], *args, **kwds)

def safe_dump(native, *args, **kwds):
    return safe_dump_all([native], *args, **kwds)

