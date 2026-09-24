"""Extract version from the latest commit message.

Commit message format: `<ver> - <msg>`
where <ver> is e.g. 0A, 4C, etc.

The version is major + letter, where:
- major is the digit part (0, 4, etc.)
- letter is the alpha part (A, B, C, etc.)

SemVer conversion: <major>.<letter_position>.<0>
where letter_position = A=1, B=2, C=3, D=4, ...

If the commit message does not start with a version pattern, outputs
skip=true to the GITHUB_OUTPUT file.

Usage: python scripts/extract_version.py <github_output_file>
"""

import re
import subprocess
import sys


def extract_version(commit_msg: str):
    """Returns (original_version, semver, commit_message) or None."""
    match = re.match(r"^([0-9]+)([A-Z])\s*-\s*(.+)$", commit_msg.strip(), re.DOTALL)
    if not match:
        return None

    major = int(match.group(1))
    letter = match.group(2)
    original = match.group(1) + match.group(2)
    msg = match.group(3).strip()

    minor = ord(letter) - ord("A") + 1
    semver = f"{major}.{minor}.0"

    return original, semver, msg


def main():
    output_file = sys.argv[1] if len(sys.argv) > 1 else None

    result = subprocess.run(["git", "log", "-1", "--pretty=%B"], capture_output=True, text=True, check=True)
    commit_msg = result.stdout

    parsed = extract_version(commit_msg)
    if parsed is None:
        if output_file:
            with open(output_file, "a") as f:
                f.write("skip=true\n")
        print("No version found in commit message.", file=sys.stderr)
        sys.exit(0)

    original, semver, msg = parsed

    if output_file:
        with open(output_file, "a") as f:
            f.write("skip=false\n")
            f.write(f"original_version={original}\n")
            f.write(f"semver={semver}\n")
            # Multi-line output for release message
            f.write("release_msg<<EOF\n")
            f.write(f"{msg}\n")
            f.write("EOF\n")
    else:
        print(f"original: {original}")
        print(f"semver: {semver}")
        print(f"message: {msg}")


if __name__ == "__main__":
    main()
