#!/usr/bin/env python3
"""
check_imports.py — Import cycle check for scripts/

eci-ui gates every PR on `npm run check:circular-deps`, which runs madge over the
frontend. There is no madge for Python, and these scripts already import each other
(`build_load_package` and `validate_load_package` both pull in `error_natives`,
`generate_mock_metadata` pulls in `edge_cases`), so the same failure mode is
available here: a cycle that imports cleanly at module scope and then blows up the
first time someone reorders an import.

Parses the AST rather than importing, so a missing third-party dependency does not
turn into a false failure.

Usage:
  python scripts/check_imports.py
"""

import ast
import os
import sys

SCRIPTS = os.path.dirname(os.path.abspath(__file__))


def local_modules():
    return {f[:-3] for f in os.listdir(SCRIPTS)
            if f.endswith(".py") and not f.startswith("_")}


def imports_of(path, local):
    with open(path, encoding="utf-8") as f:
        tree = ast.parse(f.read(), path)
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                head = a.name.split(".")[0]
                if head in local:
                    found.add(head)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            head = node.module.split(".")[0]
            if head in local:
                found.add(head)
    return found


def find_cycles(graph):
    cycles, stack, seen = [], [], set()

    def walk(node):
        if node in stack:                       # closed a loop
            cycles.append(stack[stack.index(node):] + [node])
            return
        if node in seen:
            return
        seen.add(node)
        stack.append(node)
        for nxt in sorted(graph.get(node, ())):
            walk(nxt)
        stack.pop()

    for node in sorted(graph):
        walk(node)
    return cycles


def main():
    local = local_modules()
    graph = {m: imports_of(os.path.join(SCRIPTS, m + ".py"), local) for m in sorted(local)}

    print("\n  Local imports between scripts\n")
    for mod in sorted(graph):
        if graph[mod]:
            print(f"    {mod} -> {', '.join(sorted(graph[mod]))}")

    cycles = find_cycles(graph)
    print()
    if cycles:
        print(f"  {len(cycles)} import cycle(s):")
        for c in cycles:
            print("    " + " -> ".join(c))
        print()
        sys.exit(1)
    print(f"  No cycles across {len(graph)} modules\n")


if __name__ == "__main__":
    main()
