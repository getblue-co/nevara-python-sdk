#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path


SDK_DIR = Path(__file__).resolve().parents[1]
PYPROJECT = SDK_DIR / "pyproject.toml"
VERSION_PATTERN = re.compile(r'(?m)^version = "(\d+)\.(\d+)\.(\d+)"$')


def bump_version(version: str, increment: str) -> str:
    major, minor, patch = [int(part) for part in version.split(".")]
    if increment == "major":
        return f"{major + 1}.0.0"
    if increment == "minor":
        return f"{major}.{minor + 1}.0"
    if increment == "patch":
        return f"{major}.{minor}.{patch + 1}"
    raise ValueError(f"Unsupported increment: {increment}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Bump the Nevara Python SDK version.")
    parser.add_argument("--increment", choices=["patch", "minor", "major"], default="patch")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    contents = PYPROJECT.read_text()
    match = VERSION_PATTERN.search(contents)
    if not match:
        raise SystemExit("Could not find project.version in sdk/python/pyproject.toml")

    current = ".".join(match.groups())
    next_version = bump_version(current, args.increment)
    if not args.dry_run:
        updated = VERSION_PATTERN.sub(f'version = "{next_version}"', contents, count=1)
        PYPROJECT.write_text(updated)

    print(next_version)


if __name__ == "__main__":
    main()
