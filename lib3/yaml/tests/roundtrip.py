# coding: utf-8

from __future__ import print_function

"""
helper routines for testing round trip of commented YAML data
"""
import sys
import textwrap
from pathlib import Path

enforce = object()


def dedent(data):
    try:
        position_of_first_newline = data.index('\n')
        for idx in range(position_of_first_newline):
            if not data[idx].isspace():
                raise ValueError
    except ValueError:
        pass
    else:
        data = data[position_of_first_newline + 1 :]
    return textwrap.dedent(data)


def diff(inp, outp, file_name='stdin'):
    import difflib

    inl = inp.splitlines(True)  # True for keepends
    outl = outp.splitlines(True)
    diff = difflib.unified_diff(inl, outl, file_name, 'round trip YAML')
    # 2.6 difflib has trailing space on filename lines %-)
    strip_trailing_space = sys.version_info < (2, 7)
    for line in diff:
        if strip_trailing_space and line[:4] in ['--- ', '+++ ']:
            line = line.rstrip() + '\n'
        sys.stdout.write(line)




def save_and_run(program, base_dir=None, output=None, file_name=None, optimized=False):
    """
    safe and run a python program, thereby circumventing any restrictions on module level
    imports
    """
    from subprocess import STDOUT, CalledProcessError, check_output

    if not hasattr(base_dir, 'hash'):
        base_dir = Path(str(base_dir))
    if file_name is None:
        file_name = 'safe_and_run_tmp.py'
    file_name = base_dir / file_name
    file_name.write_text(dedent(program))

    try:
        cmd = [sys.executable]
        if optimized:
            cmd.append('-O')
        cmd.append(str(file_name))
        print('running:', *cmd)
        res = check_output(cmd, stderr=STDOUT, universal_newlines=True)
        if output is not None:
            if '__pypy__' in sys.builtin_module_names:
                res = res.splitlines(True)
                res = [line for line in res if 'no version info' not in line]
                res = ''.join(res)
            print('result:  ', res, end='')
            print('expected:', output, end='')
            assert res == output
    except CalledProcessError as exception:
        print("##### Running '{} {}' FAILED #####".format(sys.executable, file_name))
        print(exception.output)
        return exception.returncode
    return 0
