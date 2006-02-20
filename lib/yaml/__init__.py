
from error import YAMLError
from reader import Reader
from scanner import Scanner
from parser import Parser
from composer import Composer
from resolver import Resolver

from tokens import *
from events import *

def scan(data, Reader=Reader, Scanner=Scanner):
    reader = Reader(data)
    scanner = Scanner(reader)
    return iter(scanner)

def parse(data, Reader=Reader, Scanner=Scanner, Parser=Parser):
    reader = Reader(data)
    scanner = Scanner(reader)
    parser = Parser(scanner)
    return iter(parser)

def compose(data, Reader=Reader, Scanner=Scanner, Parser=Parser,
        Composer=Composer):
    reader = Reader(data)
    scanner = Scanner(reader)
    parser = Parser(scanner)
    composer = Composer(parser)
    return iter(composer)

def compose_document(*args, **kwds):
    try:
        return compose(*args, **kwds).next()
    except StopIteration:
        return None

def resolve(data, Reader=Reader, Scanner=Scanner, Parser=Parser,
        Composer=Composer, Resolver=Resolver):
    reader = Reader(data)
    scanner = Scanner(reader)
    parser = Parser(scanner)
    composer = Composer(parser)
    resolver = Resolver(composer)
    return iter(resolver)

def resolve_document(*args, **kwds):
    try:
        return resolve(*args, **kwds).next()
    except StopIteration:
        return None

