
from error import *
from reader import *
from scanner import *
from parser import *
from composer import *
from resolver import *
from constructor import *
from emitter import *

from tokens import *
from events import *
from nodes import *

def parse(data, Reader=Reader, Scanner=Scanner, Parser=Parser):
    reader = Reader(data)
    scanner = Scanner(reader)
    parser = Parser(scanner)
    return parser

def load(data, Reader=Reader, Scanner=Scanner, Parser=Parser,
        Composer=Composer, Resolver=Resolver, Constructor=Constructor):
    reader = Reader(data)
    scanner = Scanner(reader)
    parser = Parser(scanner)
    composer = Composer(parser)
    resolver = Resolver(composer)
    constructor = Constructor(resolver)
    return constructor

def load_document(*args, **kwds):
    for document in load(*args, **kwds):
        return document

