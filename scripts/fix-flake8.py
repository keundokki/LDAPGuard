#!/usr/bin/env python3
"""Auto-fix common flake8 issues."""

import os
import re
from pathlib import Path


def fix_file(filepath):
    """Fix whitespace and formatting issues in a file."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    original_content = content

    # Remove trailing whitespace on each line
    lines = content.split("\n")
    lines = [line.rstrip() for line in lines]
    content = "\n".join(lines)

    # Remove blank lines with only whitespace
    content = re.sub(r"\n[ \t]+\n", "\n\n", content)

    # Remove multiple blank lines at end of file
    content = content.rstrip() + "\n"

    # Ensure exactly 2 blank lines between top-level definitions
    # This is a simplified approach - handles common cases
    content = re.sub(r"\n(\n+)(def |class )", r"\n\n\2", content)

    if content != original_content:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    return False


def main():
    """Fix all Python files in api/ and workers/ directories."""
    fixed_count = 0

    for directory in ["api", "workers"]:
        if not Path(directory).exists():
            continue

        for py_file in Path(directory).rglob("*.py"):
            if fix_file(str(py_file)):
                print(f"Fixed: {py_file}")
                fixed_count += 1

    print(f"\nFixed {fixed_count} files")


if __name__ == "__main__":
    main()
