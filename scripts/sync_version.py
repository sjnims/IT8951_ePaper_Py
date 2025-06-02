#!/usr/bin/env python3
"""Synchronize version between __init__.py and pyproject.toml.

This script reads the version from src/IT8951_ePaper_Py/__init__.py
and updates pyproject.toml to match. This ensures version consistency
across the project.

Usage:
    python scripts/sync_version.py
"""

import re
import sys
from pathlib import Path


def get_version_from_init() -> str:
    """Extract version from __init__.py."""
    init_file = Path("src/IT8951_ePaper_Py/__init__.py")
    if not init_file.exists():
        print(f"Error: {init_file} not found")
        sys.exit(1)

    content = init_file.read_text()
    match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
    if not match:
        print("Error: __version__ not found in __init__.py")
        sys.exit(1)

    return match.group(1)


def update_pyproject_toml(version: str) -> None:
    """Update version in pyproject.toml."""
    pyproject_file = Path("pyproject.toml")
    if not pyproject_file.exists():
        print(f"Error: {pyproject_file} not found")
        sys.exit(1)

    content = pyproject_file.read_text()

    # Update the poetry version
    new_content = re.sub(
        r'^\[tool\.poetry\]\nversion = "[^"]*"',
        f'[tool.poetry]\nversion = "{version}"',
        content,
        flags=re.MULTILINE,
    )

    if new_content == content:
        print(f"Version already synchronized at {version}")
    else:
        pyproject_file.write_text(new_content)
        print(f"Updated pyproject.toml version to {version}")


def main() -> None:
    """Main entry point."""
    version = get_version_from_init()
    print(f"Version in __init__.py: {version}")
    update_pyproject_toml(version)


if __name__ == "__main__":
    main()
