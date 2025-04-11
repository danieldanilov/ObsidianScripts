"""
# Obsidian Daily Notes Navigation Fixer

## Purpose
This script repairs navigation links in daily notes that were broken by the wikilink simplification.
It restores paths like:
- [[2025-W12 |THIS WEEK → [[01 - Calendar/Weekly/2025-W12 |THIS WEEK]]
- [[2025-03-21 |-1D → [[01 - Calendar/Daily/2025-03-21 |-1D]]

The script specifically targets the broken navigation row in daily notes without affecting other simplified wikilinks.

## Technical Implementation
- Focuses only on files in the daily notes directory
- Uses regex to identify and fix the specific broken navigation pattern
- Creates backups of modified files
- Generates a summary report of changes made

## Usage
Run this script from the command line with:
    python fix_daily_navigation.py

Optional flags:
    --dry-run: Preview changes without modifying files
    --no-backup: Skip creating backup files

## Dependencies
- os: For file operations and path handling
- re: For regular expression pattern matching
- glob: For finding files recursively
- argparse: For command-line argument parsing
"""

import os
import re
import glob
import argparse
from datetime import datetime

# Define the root directory of your Obsidian vault
VAULT_PATH = "/Users/danildanilov/Obsidian"

# Define the daily notes directory (to limit scope of changes)
DAILY_NOTES_DIR = "01 - Calendar/Daily"
WEEKLY_NOTES_DIR = "01 - Calendar/Weekly"

# Updated regex pattern to find broken navigation links in daily notes
# This pattern matches the broken format with missing closing brackets
BROKEN_NAV_PATTERN = r"←←\s*\[\[([^\]/|]+)(?:\s*\|([^\]/]+))?\s*\/\s*\[\[([^\]/|]+)(?:\s*\|([^\]/]+))?\s*\/\s*\[\[([^\]/|]+)(?:\s*\|([^\]/]+))?\s*\/\s*\[\[([^\]/|]+)(?:\s*\|([^\]/]+))?\s*→→"


def fix_navigation_links(file_path, create_backup=True, dry_run=False):
    """
    Fix navigation links in a daily note file.

    Args:
        file_path (str): Path to the markdown file
        create_backup (bool): Whether to create a backup of the original file
        dry_run (bool): If True, only simulate changes without writing to files

    Returns:
        tuple: (bool indicating if file was modified, number of fixes made)
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()

        # Check if this file contains the broken navigation pattern
        nav_match = re.search(BROKEN_NAV_PATTERN, content)
        if not nav_match:
            return False, 0

        # Extract all parts
        nav_row = nav_match.group(0)
        week1 = nav_match.group(1).strip()  # First weekly note
        week1_alias = nav_match.group(2)  # Alias for first weekly note
        day1 = nav_match.group(3).strip()  # Previous day
        day1_alias = nav_match.group(4)  # Alias for previous day
        day2 = nav_match.group(5).strip()  # Next day
        day2_alias = nav_match.group(6)  # Alias for next day
        week2 = nav_match.group(7).strip()  # Next weekly note
        week2_alias = nav_match.group(8)  # Alias for next weekly note

        # Fix aliases by stripping whitespace if they exist
        if week1_alias:
            week1_alias = week1_alias.strip()
        if day1_alias:
            day1_alias = day1_alias.strip()
        if day2_alias:
            day2_alias = day2_alias.strip()
        if week2_alias:
            week2_alias = week2_alias.strip()

        # Create fixed navigation row
        fixed_nav_row = (
            f"←← [[{WEEKLY_NOTES_DIR}/{week1}"
            + (f" |{week1_alias}" if week1_alias else "")
            + f"]] / [[{DAILY_NOTES_DIR}/{day1}"
            + (f" |{day1_alias}" if day1_alias else "")
            + f"]] / [[{DAILY_NOTES_DIR}/{day2}"
            + (f" |{day2_alias}" if day2_alias else "")
            + f"]] / [[{WEEKLY_NOTES_DIR}/{week2}"
            + (f" |{week2_alias}" if week2_alias else "")
            + "]] →→"
        )

        # Apply the fix
        modified_content = content.replace(nav_row, fixed_nav_row)

        # Check if content was modified
        if content != modified_content:
            if not dry_run:
                # Create backup if requested
                if create_backup:
                    backup_path = file_path + ".navfix.backup"
                    with open(backup_path, "w", encoding="utf-8") as backup_file:
                        backup_file.write(content)

                # Write modified content
                with open(file_path, "w", encoding="utf-8") as file:
                    file.write(modified_content)

                print(f"Fixed navigation in: {os.path.relpath(file_path, VAULT_PATH)}")

            return True, 1
        return False, 0

    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")
        return False, 0


def process_daily_notes(create_backup=True, dry_run=False):
    """
    Process all daily note files in the vault.

    Args:
        create_backup (bool): Whether to create backups of modified files
        dry_run (bool): If True, only simulate changes without writing to files

    Returns:
        tuple: (list of modified files, total number of fixes, total files processed)
    """
    # Find all daily note files
    daily_notes_path = os.path.join(VAULT_PATH, DAILY_NOTES_DIR)
    daily_files = glob.glob(f"{daily_notes_path}/*.md")

    modified_files = []
    total_fixes = 0

    file_count = len(daily_files)
    print(f"Found {file_count} daily note files to process")

    for i, file_path in enumerate(daily_files):
        # Progress indicator
        if i % 20 == 0 or i == file_count - 1:
            print(
                f"Processing file {i+1}/{file_count}... ({((i+1)/file_count)*100:.1f}%)"
            )

        was_modified, fixes = fix_navigation_links(file_path, create_backup, dry_run)
        if was_modified:
            modified_files.append(file_path)
            total_fixes += fixes

    return modified_files, total_fixes, file_count


def main():
    """Main function to parse arguments and run the script."""
    parser = argparse.ArgumentParser(
        description="Fix navigation links in Obsidian daily notes."
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without modifying files"
    )
    parser.add_argument(
        "--no-backup", action="store_true", help="Skip creating backup files"
    )
    args = parser.parse_args()

    create_backup = not args.no_backup

    print(
        f"{'[DRY RUN] ' if args.dry_run else ''}Starting to fix navigation links in daily notes..."
    )
    print(f"Vault path: {VAULT_PATH}")
    print(f"Daily notes directory: {DAILY_NOTES_DIR}")
    print(f"Creating backups: {'No' if args.no_backup else 'Yes'}")

    start_time = datetime.now()
    modified_files, total_fixes, total_files = process_daily_notes(
        create_backup, args.dry_run
    )
    end_time = datetime.now()

    # Generate report
    print("\n" + "=" * 50)
    print(f"SUMMARY REPORT ({end_time - start_time})")
    print("=" * 50)

    print(f"\nTotal files processed: {total_files}")
    print(f"Files fixed: {len(modified_files)}")
    print(f"Total navigation rows fixed: {total_fixes}")

    if args.dry_run:
        print("\n[DRY RUN] No files were actually modified.")
    else:
        print(
            f"\nACTION COMPLETE: Fixed navigation in {len(modified_files)} daily notes."
        )

    print("\nCompleted!")


if __name__ == "__main__":
    main()
