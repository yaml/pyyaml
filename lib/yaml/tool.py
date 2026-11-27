r"""Command-line tool to validate and pretty-print YAML

Usage::

    $ echo '{"json":"obj"}' | python -m yaml.tool
    ---
    json: obj
    $ echo '{ 1.2:3.4' | python -m yaml.tool
    while parsing a flow mapping
      in "<stdin>", line 1, column 1
    expected ',' or '}', but got '<stream end>'
      in "<stdin>", line 2, column 1


"""

import argparse

import yaml

try:
    from yaml import CSafeDumper as SafeDumper
    from yaml import CSafeLoader as SafeLoader
except ImportError:
    from yaml import SafeDumper, SafeLoader
import sys
from pathlib import Path


def main():
    prog = "python -m yaml.tool"
    description = (
        "A simple command line interface for PyYAML module "
        "to validate and pretty-print YAML objects."
    )
    parser = argparse.ArgumentParser(prog=prog, description=description)
    parser.add_argument(
        "infile",
        nargs="?",
        type=argparse.FileType(encoding="utf-8"),
        help="a YAML file to be validated or pretty-printed",
        default=sys.stdin,
    )
    parser.add_argument(
        "outfile",
        nargs="?",
        type=Path,
        help="write the output of infile to outfile",
        default=None,
    )
    parser.add_argument(
        "--sort-keys",
        action="store_true",
        default=False,
        help="sort the output of dictionaries alphabetically by key",
    )
    parser.add_argument(
        "--json-lines",
        "--yaml-lines",
        action="store_true",
        default=False,
        help="parse input using the JSON Lines format. ",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--indent",
        default=2,
        type=int,
        help="separate items with newlines and use this number "
        "of spaces for indentation",
    )
    group.add_argument(
        "--compact", action="store_true", help="suppress most whitespace separation",
    )

    options = parser.parse_args()

    dump_args = {
        "explicit_start": True,
        "sort_keys": options.sort_keys,
        "indent": options.indent,
        "Dumper": SafeDumper,
    }
    if options.compact:
        dump_args["explicit_start"] = False
        dump_args["default_flow_style"] = True

    with options.infile as infile:
        try:
            if options.json_lines:
                objs = (yaml.load(line, Loader=SafeLoader) for line in infile)
            else:
                objs = yaml.load_all(infile, Loader=SafeLoader)

            if options.outfile is None:
                out = sys.stdout
            else:
                out = options.outfile.open("w", encoding="utf-8")
            with out as outfile:
                yaml.dump_all(objs, outfile, **dump_args)
        except yaml.error.YAMLError as e:
            raise SystemExit(e)


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError as exc:
        sys.exit(exc.errno)
