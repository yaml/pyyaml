#!/bin/sh
find ./ -name '*.pyx' -exec cython \{\} \;
