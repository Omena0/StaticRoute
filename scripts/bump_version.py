"""Bump the patch version in pyproject.toml by 1.

If the package already exists on PyPI, query the latest version and bump from there.
Otherwise, bump the version currently in pyproject.toml.

Usage: python scripts/bump_version.py <pyproject_path> [package_name]
"""

import json
import sys
import urllib.request


def get_latest_pypi_version(package_name: str) -> str | None:
    """Fetch the latest version from PyPI."""
    try:
        url = f"https://pypi.org/pypi/{package_name}/json"
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())
        return data["info"]["version"]
    except Exception:
        return None


def bump_patch_ver(version: str) -> str:
    """Bump the patch version of a SemVer string."""
    parts = version.split(".")
    parts[-1] = str(int(parts[-1]) + 1)
    return ".".join(parts)


def get_current_version(path: str) -> str | None:
    """Read the current version from pyproject.toml."""
    with open(path) as f:
        for line in f:
            if line.startswith("version = "):
                return line.split('"')[1]
    return None


def bump_version(path: str, package_name: str | None = None):
    # Try to get the latest version from PyPI
    current = None
    if package_name:
        pypi_ver = get_latest_pypi_version(package_name)
        if pypi_ver:
            current = pypi_ver
            print(f"Latest PyPI version: {current}")

    # Fall back to local version
    if not current:
        current = get_current_version(path)
        if not current:
            print("ERROR: Could not determine version", file=sys.stderr)
            sys.exit(1)
        print(f"Local version: {current}")

    new_version = bump_patch_ver(current)
    print(f"Bumping version: {current} -> {new_version}")

    with open(path) as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        if line.startswith("version = "):
            lines[i] = f'version = "{new_version}"\n'
            break

    with open(path, "w") as f:
        f.writelines(lines)


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "pyproject.toml"
    package = sys.argv[2] if len(sys.argv) > 2 else None
    bump_version(path, package)
