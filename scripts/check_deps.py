#!/usr/bin/env python3
"""
check_deps.py — The gate's own dependencies are installed

`make check` used to fail on a fresh clone with `ModuleNotFoundError: No module
named 'fpdf'`, buried 35 lines into the error scenario matrix, and `/bin/sh:
.venv/bin/ruff: No such file or directory` before that. Neither says what to do
about it, and neither is a real failure of the branch.

Runs first in the gate so a missing dependency is named in milliseconds and points
at `make setup`, instead of looking like a broken PR.

Only checks what the gate itself needs. `duckdb` (export-insys) and the rest of the
native file generators (build_load_package) are not gate dependencies, so a clone
that cannot build a load package can still pass check.

Usage:
  python scripts/check_deps.py
"""

import importlib.util
import os
import shutil
import sys

PASS = "\033[32mok  \033[0m"
FAIL = "\033[31mFAIL\033[0m"

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VENV_BIN = os.path.join(ROOT, ".venv", "bin")

# module -> what stops working without it
MODULES = {
    "fpdf": "test_error_scenarios (PDF natives in the error matrix)",
}

# executable -> the gate step that shells out to it
TOOLS = {
    "ruff": "make lint",
    "mypy": "make typecheck",
}

missing: list[str] = []


def check(label, ok, detail=""):
    print(f"  [{PASS if ok else FAIL}] {label}" + (f" — {detail}" if detail else ""))
    if not ok:
        missing.append(label)


def have_tool(name):
    """Same resolution order as the Makefile: PATH first, then .venv/bin."""
    return shutil.which(name) is not None or os.access(os.path.join(VENV_BIN, name), os.X_OK)


def main():
    print("\n  Gate dependencies\n")

    for name, why in sorted(TOOLS.items()):
        check(name, have_tool(name), why)

    for name, why in sorted(MODULES.items()):
        check(name, importlib.util.find_spec(name) is not None, why)

    print()
    if missing:
        print(f"  {len(missing)} missing: {', '.join(missing)}")
        print("\n  Run 'make setup' to install them, then re-run 'make check'.\n")
        sys.exit(1)
    print(f"  All {len(TOOLS) + len(MODULES)} gate dependencies present\n")


if __name__ == "__main__":
    main()
