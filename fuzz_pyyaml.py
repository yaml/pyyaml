#!/usr/bin/env python3
"""Fuzz harness for PyYAML — YAML parser (4 GHSA advisories)."""
import sys
import atheris

with atheris.instrument_imports():
    import yaml


def TestOneInput(data):
    # YAML parsing with arbitrary bytes — classic parser fuzz
    try:
        yaml.safe_load(data)
    except yaml.YAMLError:
        pass
    except Exception:
        pass


def main():
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
