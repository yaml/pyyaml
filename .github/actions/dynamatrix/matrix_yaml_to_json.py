from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
import typing as t
import yaml

from collections.abc import MutableMapping, Sequence

skipped_entries = []

def _filter_omit_entries(value):
    if isinstance(value, MutableMapping):
        if (omit_value := value.pop('omit', ...)) is not ...:
            if omit_value is True or str(omit_value).lower().strip() == 'true':
                print(f'omitting {value} from matrix')
                skipped_entries.append(value)
                return ...

        return {k: v for k, v in ((k, _filter_omit_entries(v)) for k, v in value.items()) if v is not ...}

    if isinstance(value, str):
        return value

    if isinstance(value, Sequence):
        return [v for v in (_filter_omit_entries(v) for v in value) if v is not ...]

    return value

def main():
    p = argparse.ArgumentParser(description='GHA YAML matrix filter')
    required_grp = p.add_mutually_exclusive_group(required=True)
    required_grp.add_argument('--from-stdin', action='store_true', help='read input YAML from stdin')
    required_grp.add_argument('--from-file', type=pathlib.Path, help='read input YAML from file path')

    args = p.parse_args()

    path: pathlib.Path | None

    matrix_yaml: str

    if path := args.from_file:
        matrix_yaml = path.read_text()
    elif args.from_stdin:
        matrix_yaml = sys.stdin.read()
    else:
        raise Exception('no source provided for matrix yaml')

    raw_matrix = yaml.safe_load(matrix_yaml)
    filtered_matrix = _filter_omit_entries(raw_matrix)

    output_matrix_json = json.dumps(filtered_matrix)
    output_skipped_matrix_json = json.dumps(skipped_entries)

    print(f'filtered matrix: {output_matrix_json}')
    print(f'skipped entries: {output_skipped_matrix_json}')

    if (gh_output := os.environ.get('GITHUB_OUTPUT')):
        print('setting step output var matrix_json; skipped_matrix_json...')
        with pathlib.Path(gh_output).open('a') as env_fd:
            env_fd.write(f'matrix_json<<__MATRIX_EOF\n{output_matrix_json}\n__MATRIX_EOF\n')
            env_fd.write(f'skipped_matrix_json<<__MATRIX_EOF\n{output_skipped_matrix_json}\n__MATRIX_EOF\n')
    else:
        print("GITHUB_OUTPUT not set; skipping variable output")


if __name__ == '__main__':
    main()
