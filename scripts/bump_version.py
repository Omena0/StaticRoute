"""Bump the patch version in pyproject.toml by 1.

Usage: python scripts/bump_version.py <pyproject_path>
"""

import sys


def bump_patch(path: str):
    with open(path) as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        if line.startswith("version = "):
            current = line.split('"')[1]
            parts = current.split(".")
            parts[-1] = str(int(parts[-1]) + 1)
            new_version = ".".join(parts)
            lines[i] = f'version = "{new_version}"\n'
            print(f"Bumped version: {current} -> {new_version}")
            break

    with open(path, "w") as f:
        f.writelines(lines)


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "pyproject.toml"
    bump_patch(path)
