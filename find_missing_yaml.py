# Script Definition, Details, and Technical Implementation:
#
# **Purpose:**
# This script scans a specified directory (intended to be an Obsidian vault) for Markdown files (.md).
# It identifies which files lack YAML front matter at the beginning. YAML front matter is defined as
# content enclosed between two '---' lines at the very start of the file.
#
# **Functionality:**
# 1. Recursively walks through the specified root directory.
# 2. Identifies all files with the '.md' extension.
# 3. For each Markdown file, it reads the first few lines to check for the presence of YAML front matter.
#    - A file is considered to have YAML front matter if it starts with a line exactly equal to '---'
#      and contains another line exactly equal to '---' within the first ~15 lines (to avoid reading huge files unnecessarily if YAML is missing).
# 4. Compiles a list of files that *do not* contain YAML front matter.
# 5. Counts the total number of Markdown files found.
# 6. Counts the number of files with and without YAML front matter.
# 7. Calculates the percentage of files with and without YAML front matter relative to the total Markdown files.
# 8. Prints a summary report including:
#    - The list of files missing YAML.
#    - Total Markdown file count.
#    - Count of files with YAML.
#    - Count of files without YAML.
#    - Percentage of files with YAML.
#    - Percentage of files without YAML.
#
# **Technical Implementation:**
# - Uses the `os` module, specifically `os.walk`, to traverse the directory structure.
# - Uses standard file I/O operations to read the beginning of each Markdown file.
# - Implements simple string checking ('---') to detect YAML boundaries.
# - Calculates percentages and formats the output for readability.
# - The root directory to scan is hardcoded but can be easily modified.

import os
import sys


def has_yaml_front_matter(filepath: str) -> bool:
    """
    Checks if a file starts with YAML front matter.

    Args:
        filepath (str): The path to the file.

    Returns:
        bool: True if YAML front matter is detected, False otherwise.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            first_line = f.readline().strip()
            if first_line != "---":
                return False
            # Look for the closing '---' within the next ~15 lines
            for i, line in enumerate(f):
                if line.strip() == "---":
                    return True
                if i > 45:  # Stop checking after a reasonable number of lines
                    break
            return False
    except Exception as e:
        print(f"Error reading file {filepath}: {e}", file=sys.stderr)
        return False  # Treat errors as missing YAML for safety


def find_missing_yaml(root_dir: str):
    """
    Scans a directory for Markdown files and reports on YAML front matter presence.

    Args:
        root_dir (str): The root directory to scan (e.g., the Obsidian vault path).
    """
    markdown_files = []
    files_with_yaml = 0
    files_without_yaml = []

    # Use absolute path for the root directory
    abs_root_dir = os.path.abspath(root_dir)
    print(f"Scanning directory: {abs_root_dir}")

    if not os.path.isdir(abs_root_dir):
        print(f"Error: Directory not found: {abs_root_dir}", file=sys.stderr)
        return

    # Exclude the script's own directory if it's within the vault
    script_dir = os.path.abspath(os.path.join(abs_root_dir, "99 - Meta/99 - Scripts"))

    for subdir, _, files in os.walk(abs_root_dir):
        # Skip the script directory itself
        if os.path.abspath(subdir).startswith(script_dir):
            print(f"Skipping script directory: {subdir}")
            continue

        for filename in files:
            if filename.lower().endswith(".md"):
                filepath = os.path.join(subdir, filename)
                relative_path = os.path.relpath(filepath, abs_root_dir)
                markdown_files.append(relative_path)
                if has_yaml_front_matter(filepath):
                    files_with_yaml += 1
                else:
                    files_without_yaml.append(relative_path)

    total_files = len(markdown_files)
    files_missing_count = len(files_without_yaml)

    print("\n--- Scan Complete ---")

    if not markdown_files:
        print("No Markdown files found.")
        return

    print(f"\nFiles Missing YAML Front Matter ({files_missing_count}):")
    if files_without_yaml:
        for file in sorted(files_without_yaml):
            print(f"- {file}")
    else:
        print("None - All Markdown files have YAML front matter.")

    print("\n--- Statistics ---")
    print(f"Total Markdown Files Found: {total_files}")
    print(f"Files With YAML:            {files_with_yaml}")
    print(f"Files Without YAML:         {files_missing_count}")

    if total_files > 0:
        percent_with_yaml = (files_with_yaml / total_files) * 100
        percent_without_yaml = (files_missing_count / total_files) * 100
        print(f"Percentage With YAML:       {percent_with_yaml:.2f}%")
        print(f"Percentage Without YAML:    {percent_without_yaml:.2f}%")
    print("--------------------\n")


if __name__ == "__main__":
    # Set the root directory to the parent directory of the script's location
    # Assumes the script is in a subdirectory of the vault root
    # e.g., /Users/danildanilov/Obsidian/99 - Meta/99 - Scripts/find_missing_yaml.py
    # Vault root would be /Users/danildanilov/Obsidian
    script_location = os.path.dirname(os.path.abspath(__file__))
    # Go up two levels from script location (99 - Scripts -> 99 - Meta -> Vault Root)
    vault_root = os.path.dirname(os.path.dirname(script_location))

    # Or, uncomment and set the path explicitly if the script is elsewhere:
    # vault_root = "/Users/danildanilov/Obsidian"

    find_missing_yaml(vault_root)
