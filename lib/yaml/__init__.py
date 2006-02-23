
from error import YAMLError
from reader import Reader
from scanner import Scanner
from parser import Parser
from composer import Composer
from resolver import Resolver
from constructor import Constructor

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

