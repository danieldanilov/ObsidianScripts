#!/usr/bin/env python3
"""
Duplicate Note Finder for Obsidian

This script identifies markdown notes with identical filenames across different
folders in an Obsidian vault. It traverses the entire vault directory structure,
collects all markdown files (*.md), and reports any duplicate filenames along with
their full paths.

Technical Implementation:
- Uses os.walk() to recursively traverse all directories in the vault
- Maintains a dictionary to track filenames and their paths
- Ignores specified directories (like .git, .trash, etc.)
- Outputs results to console, showing duplicate filenames and their locations
- Can be customized to ignore specific directories via the IGNORED_DIRS list
"""

import os
import sys
from typing import Dict, List, Set
from pathlib import Path


def find_duplicate_notes(
    vault_path: str, ignored_dirs: Set[str]
) -> Dict[str, List[str]]:
    """
    Find markdown notes with identical filenames across the vault.

    Args:
        vault_path (str): Path to the Obsidian vault root
        ignored_dirs (Set[str]): Set of directory names to ignore

    Returns:
        Dict[str, List[str]]: Dictionary mapping duplicate filenames to lists of their paths
    """
    # Dictionary to track filenames and their paths
    file_paths: Dict[str, List[str]] = {}

    # Walk through the vault directory structure
    for root, dirs, files in os.walk(vault_path):
        # Skip ignored directories
        dirs[:] = [d for d in dirs if d not in ignored_dirs]

        # Process only markdown files
        md_files = [f for f in files if f.endswith(".md")]

        for filename in md_files:
            full_path = os.path.join(root, filename)

            # Track the file
            if filename not in file_paths:
                file_paths[filename] = []
            file_paths[filename].append(full_path)

    # Filter to keep only duplicates
    duplicates = {
        filename: paths for filename, paths in file_paths.items() if len(paths) > 1
    }

    return duplicates


def main() -> None:
    """
    Main function to run the duplicate note finder.
    """
    # Define the vault path (current directory by default)
    vault_path = os.path.expanduser("~/Obsidian")

    # Directories to ignore
    ignored_dirs = {
        ".git",
        ".obsidian",
        ".trash",
        "node_modules",
        ".github",
        "__pycache__",
        ".DS_Store",
    }

    print(f"Searching for duplicate notes in: {vault_path}")

    # Find duplicates
    duplicates = find_duplicate_notes(vault_path, ignored_dirs)

    # Display results
    if not duplicates:
        print("No duplicate notes found.")
    else:
        print(f"\nFound {len(duplicates)} duplicate note names:")
        for filename, paths in duplicates.items():
            print(f"\n• {filename}")
            for path in paths:
                # Get relative path to make output cleaner
                rel_path = os.path.relpath(path, vault_path)
                print(f"  - {rel_path}")


if __name__ == "__main__":
    main()
