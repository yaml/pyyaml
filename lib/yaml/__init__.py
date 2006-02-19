
from reader import Reader
from scanner import Scanner
from parser import Parser

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

