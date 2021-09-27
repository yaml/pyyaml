#!/usr/bin/env python3

import sys
sys.path.insert(0, 'lib')

from yaml import *

ldr = SafeLoader()

def dice_constructor1(loader, node):
    value = loader.construct_scalar(node)
    a, b = map(int, value.split('d'))
    return [a,b]

def dice_constructor2(loader, node):
    value = loader.construct_scalar(node)
    a, b = map(int, value.split('d'))
    return [b,a]

s = """
- !dice 3d4
"""



add_constructor('!dice', dice_constructor1, SafeLoader)

print()
data = load(s, SafeLoader)
print('1) SafeLoader -> %s' % data)
data = load(s, ldr)
print('1) Instance   -> %s' % data)



ldr.add_constructor('!dice', dice_constructor2)

print()
data = load(s, SafeLoader)
print('2) SafeLoader -> %s' % data)
data = load(s, ldr)
print('2) Instance   -> %s' % data)



ldr.add_constructor('!dice', None)

print()
data = load(s, SafeLoader)
print('3) SafeLoader -> %s' % data)
data = load(s, ldr)
print('3) Instance   -> %s' % data)
