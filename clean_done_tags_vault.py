"""
# Obsidian #done Tag Cleaner

## Purpose
This script removes all instances of "#done" tags from Markdown files in an Obsidian vault.
It handles two formats:
1. #done tags with datetime information: #done(2021-11-23 19:20)
2. Plain #done tags without parentheses: #done

The script preserves the rest of the content while removing these tags.

## Technical Implementation
- Uses recursive globbing to find all Markdown (.md) files in the vault
- Applies regex pattern matching to identify and remove both formats of #done tags
- Creates backups of modified files with .backup extension
- Generates a summary report of changes made
- Handles different text encodings to maximize compatibility

## Usage
Run this script from the command line with:
    python clean_done_tags_vault.py

Optional flags:
    --dry-run: Preview changes without modifying files
    --no-backup: Skip creating backup files (not recommended)
    --verbose: Show detailed debugging information

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

# Two patterns: one for #done with parentheses, one for standalone #done
DONE_WITH_PARENS_PATTERN = r"#done\s*\([^)]*\)"
DONE_STANDALONE_PATTERN = (
    r"#done\b(?!\s*\()"  # Matches #done not followed by parentheses
)


def clean_done_tags(file_path, create_backup=True, dry_run=False, verbose=False):
    """
    Remove #done tags from a file.

    Args:
        file_path (str): Path to the markdown file
        create_backup (bool): Whether to create a backup of the original file
        dry_run (bool): If True, only simulate changes without writing to files
        verbose (bool): If True, print detailed debugging information

    Returns:
        tuple: (bool indicating if file was modified, int count of tags removed)
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()

        if verbose and "#done" in content:
            rel_path = os.path.relpath(file_path, VAULT_PATH)
            print(f"\nDEBUG: Found '#done' in {rel_path}")

        # Count regex pattern matches for both types
        matches_with_parens = re.findall(DONE_WITH_PARENS_PATTERN, content)
        matches_standalone = re.findall(DONE_STANDALONE_PATTERN, content)

        total_matches = matches_with_parens + matches_standalone
        tag_count = len(total_matches)

        if verbose and tag_count > 0:
            print(f"  - Found {len(matches_with_parens)} #done tags with parentheses")
            print(f"  - Found {len(matches_standalone)} standalone #done tags")
            for match in total_matches:
                print(f"    - '{match}'")

        if tag_count == 0:
            return False, 0

        # Replace #done tags - first those with parentheses, then standalone
        modified_content = content
        for match in matches_with_parens:
            modified_content = modified_content.replace(match, "")

        # For standalone #done, we need to be more careful to avoid removing part of other text
        for match in matches_standalone:
            # Make sure we only replace exact standalone #done tags (with word boundary)
            modified_content = re.sub(
                r"\b" + re.escape(match) + r"\b", "", modified_content
            )

        # Double-check if content was modified
        if content != modified_content:
            if not dry_run:
                # Create backup if requested
                if create_backup:
                    backup_path = file_path + ".backup"
                    with open(backup_path, "w", encoding="utf-8") as backup_file:
                        backup_file.write(content)

                # Write modified content
                with open(file_path, "w", encoding="utf-8") as file:
                    file.write(modified_content)

                # Report modification
                print(
                    f"Modified: {os.path.relpath(file_path, VAULT_PATH)} - removed {tag_count} tags"
                )

            return True, tag_count
        else:
            # This shouldn't happen if we found matches but is a good safety check
            if tag_count > 0:
                print(
                    f"Warning: Found {tag_count} tags in {os.path.relpath(file_path, VAULT_PATH)} but content was not modified"
                )
            return False, 0

    except UnicodeDecodeError:
        # Try with a different encoding if UTF-8 fails
        try:
            with open(file_path, "r", encoding="latin-1") as file:
                content = file.read()

            # Repeat the pattern matching and replacement with this encoding
            matches_with_parens = re.findall(DONE_WITH_PARENS_PATTERN, content)
            matches_standalone = re.findall(DONE_STANDALONE_PATTERN, content)

            total_matches = matches_with_parens + matches_standalone
            tag_count = len(total_matches)

            if tag_count == 0:
                return False, 0

            modified_content = content
            for match in matches_with_parens:
                modified_content = modified_content.replace(match, "")

            for match in matches_standalone:
                modified_content = re.sub(
                    r"\b" + re.escape(match) + r"\b", "", modified_content
                )

            if content != modified_content:
                if not dry_run:
                    if create_backup:
                        backup_path = file_path + ".backup"
                        with open(backup_path, "w", encoding="latin-1") as backup_file:
                            backup_file.write(content)

                    with open(file_path, "w", encoding="latin-1") as file:
                        file.write(modified_content)

                    print(
                        f"Modified (latin-1): {os.path.relpath(file_path, VAULT_PATH)} - removed {tag_count} tags"
                    )

                return True, tag_count
            return False, 0

        except Exception as e:
            print(f"Error processing {file_path} with alternate encoding: {str(e)}")
            return False, 0
    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")
        return False, 0


def process_vault(create_backup=True, dry_run=False, verbose=False):
    """
    Process all markdown files in the vault.

    Args:
        create_backup (bool): Whether to create backups of modified files
        dry_run (bool): If True, only simulate changes without writing to files
        verbose (bool): If True, print detailed debugging information

    Returns:
        tuple: (list of modified files, total tags removed, total files processed)
    """
    # Find all markdown files
    md_files = glob.glob(f"{VAULT_PATH}/**/*.md", recursive=True)

    modified_files = []
    total_tags_removed = 0

    file_count = len(md_files)
    print(f"Found {file_count} markdown files to process")

    # Check if any files contain #done
    if verbose:
        sample_files = []
        for file_path in md_files:
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    content = file.read()
                    if "#done" in content:
                        sample_files.append(file_path)
                        if len(sample_files) >= 5:  # Limit to 5 examples
                            break
            except:
                continue  # Skip files that can't be read

        if sample_files:
            print(
                f"\nFound {len(sample_files)} files containing '#done' string (showing up to 5):"
            )
            for file_path in sample_files:
                print(f"  - {os.path.relpath(file_path, VAULT_PATH)}")
        else:
            print("\nWARNING: No files containing '#done' string were found!")

    for i, file_path in enumerate(md_files):
        # Progress indicator for large vaults
        if i % 100 == 0:
            print(f"Processing file {i+1}/{file_count}...")

        was_modified, tags_removed = clean_done_tags(
            file_path, create_backup, dry_run, verbose
        )
        if was_modified:
            modified_files.append((file_path, tags_removed))
            total_tags_removed += tags_removed

    return modified_files, total_tags_removed, len(md_files)


def main():
    """Main function to parse arguments and run the cleaning process."""
    parser = argparse.ArgumentParser(
        description="Clean #done tags from Obsidian vault."
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without modifying files"
    )
    parser.add_argument(
        "--no-backup", action="store_true", help="Skip creating backup files"
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Show detailed debugging information"
    )
    args = parser.parse_args()

    create_backup = not args.no_backup

    print(
        f"{'[DRY RUN] ' if args.dry_run else ''}Starting to clean #done tags from Obsidian vault..."
    )
    print(f"Vault path: {VAULT_PATH}")
    print(f"Creating backups: {'No' if args.no_backup else 'Yes'}")
    print(
        f"Patterns used: \n  1. {DONE_WITH_PARENS_PATTERN} (with parentheses)\n  2. {DONE_STANDALONE_PATTERN} (standalone)"
    )

    start_time = datetime.now()
    modified_files, total_tags_removed, total_files = process_vault(
        create_backup, args.dry_run, args.verbose
    )
    end_time = datetime.now()

    # Generate report
    print("\n" + "=" * 50)
    print(f"SUMMARY REPORT ({end_time - start_time})")
    print("=" * 50)

    print(f"\nTotal files processed: {total_files}")
    print(f"Files modified: {len(modified_files)}")
    print(f"Total #done tags removed: {total_tags_removed}")

    if modified_files:
        print("\nModified files:")
        for file_path, tags_removed in modified_files:
            rel_path = os.path.relpath(file_path, VAULT_PATH)
            print(f"  - {rel_path} ({tags_removed} tags)")

    if args.dry_run:
        print("\n[DRY RUN] No files were actually modified.")
    else:
        print(
            f"\nACTION COMPLETE: {total_tags_removed} tags were removed from {len(modified_files)} files."
        )

    print("\nCompleted!")


if __name__ == "__main__":
    main()
