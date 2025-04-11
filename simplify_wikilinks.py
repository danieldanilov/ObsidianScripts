"""
# Obsidian Wikilink Path Simplifier

## Purpose
This script converts full-path wikilinks to simple note name wikilinks in an Obsidian vault.
It transforms patterns like:
- [[00 - Archive/01 - Capture/💁 People/Family/Ira Gurevich]] → [[Ira Gurevich]]
- [[00 - Archive/01 - Capture/🧠 Concepts/Takeaway]] → [[Takeaway]]

The script preserves the note name while removing the folder path structure.

## Technical Implementation
- Uses recursive globbing to find all Markdown (.md) files in the vault
- Applies regex pattern matching to identify wikilinks with folder paths
- Extracts just the note name (last component after the final slash)
- Creates backups of modified files with .backup extension (optional)
- Generates a summary report of changes made
- Simple implementation that skips problematic files

## Usage
Run this script from the command line with:
    python simplify_wikilinks.py

Optional flags:
    --dry-run: Preview changes without modifying files
    --no-backup: Skip creating backup files
    --max-size: Maximum file size to process in KB (default: 1000)
    --start-at: Start processing at this file number (for resuming)
    --max-files: Maximum number of files to process

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

# Regex pattern to match wikilinks with folder paths and capture the note name
WIKILINK_PATTERN = r"\[\[([^|\]]*?/+)([^/\]|]+)(?:\|[^|\]]*?)?\]\]"


def simplify_wikilinks(file_path, create_backup=True, dry_run=False, max_size_kb=1000):
    """
    Convert full-path wikilinks to simple note name wikilinks in a file.

    Args:
        file_path (str): Path to the markdown file
        create_backup (bool): Whether to create a backup of the original file
        dry_run (bool): If True, only simulate changes without writing to files
        max_size_kb (int): Maximum file size to process in KB

    Returns:
        tuple: (bool indicating if file was modified, int count of wikilinks simplified)
    """
    # Check file size first
    try:
        file_size_kb = os.path.getsize(file_path) / 1024
        if file_size_kb > max_size_kb:
            print(
                f"Skipping large file ({file_size_kb:.1f} KB): {os.path.relpath(file_path, VAULT_PATH)}"
            )
            return False, 0

        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()

        # Find all wikilinks with paths
        matches = []
        replacements = []

        for match in re.finditer(WIKILINK_PATTERN, content):
            full_match = match.group(0)  # The entire match including [[]]
            note_name = match.group(2)  # Just the note name

            # Check if there's a pipe in the original (indicating an alias)
            if "|" in full_match:
                pipe_index = full_match.index("|")
                closing_index = full_match.rindex("]]")
                alias_part = full_match[pipe_index:closing_index]
                simplified = f"[[{note_name}{alias_part}"
            else:
                simplified = f"[[{note_name}]]"

            matches.append(full_match)
            replacements.append(simplified)

        link_count = len(matches)

        if link_count == 0:
            return False, 0

        # Replace full-path wikilinks with simplified versions
        modified_content = content
        for i in range(link_count):
            modified_content = modified_content.replace(matches[i], replacements[i])

        # Check if content was modified
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
                    f"Modified: {os.path.relpath(file_path, VAULT_PATH)} - simplified {link_count} wikilinks"
                )

            return True, link_count
        return False, 0

    except Exception as e:
        print(f"Skipping file {os.path.relpath(file_path, VAULT_PATH)}: {str(e)}")
        return False, 0


def process_vault(
    create_backup=True, dry_run=False, max_size_kb=1000, start_at=0, max_files=None
):
    """
    Process all markdown files in the vault.

    Args:
        create_backup (bool): Whether to create backups of modified files
        dry_run (bool): If True, only simulate changes without writing to files
        max_size_kb (int): Maximum file size to process in KB
        start_at (int): Start processing at this file number (for resuming)
        max_files (int): Maximum number of files to process

    Returns:
        tuple: (list of modified files, total wikilinks simplified, total files processed)
    """
    # Find all markdown files
    md_files = glob.glob(f"{VAULT_PATH}/**/*.md", recursive=True)

    # Sort files for consistent processing order
    md_files.sort()

    # Apply start_at and max_files constraints
    if start_at > 0:
        md_files = md_files[start_at:]
        print(f"Starting at file {start_at} (skipping {start_at} files)")

    if max_files is not None:
        md_files = md_files[:max_files]
        print(f"Processing at most {max_files} files")

    modified_files = []
    total_links_simplified = 0

    file_count = len(md_files)
    print(f"Found {file_count} markdown files to process")

    for i, file_path in enumerate(md_files):
        # Progress indicator
        if i % 50 == 0 or i == file_count - 1:
            print(
                f"Processing file {i+1}/{file_count}... ({((i+1)/file_count)*100:.1f}%)"
            )

        was_modified, links_simplified = simplify_wikilinks(
            file_path, create_backup, dry_run, max_size_kb
        )
        if was_modified:
            modified_files.append((file_path, links_simplified))
            total_links_simplified += links_simplified

    return modified_files, total_links_simplified, file_count


def main():
    """Main function to parse arguments and run the script."""
    parser = argparse.ArgumentParser(
        description="Simplify full-path wikilinks in Obsidian vault."
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without modifying files"
    )
    parser.add_argument(
        "--no-backup", action="store_true", help="Skip creating backup files"
    )
    parser.add_argument(
        "--max-size",
        type=int,
        default=1000,
        help="Maximum file size in KB to process (default: 1000)",
    )
    parser.add_argument(
        "--start-at",
        type=int,
        default=0,
        help="Start processing at this file number (for resuming)",
    )
    parser.add_argument(
        "--max-files", type=int, help="Maximum number of files to process"
    )
    args = parser.parse_args()

    create_backup = not args.no_backup

    print(
        f"{'[DRY RUN] ' if args.dry_run else ''}Starting to simplify wikilinks in Obsidian vault..."
    )
    print(f"Vault path: {VAULT_PATH}")
    print(f"Creating backups: {'No' if args.no_backup else 'Yes'}")
    print(f"Maximum file size: {args.max_size} KB")
    print(f"Pattern used: {WIKILINK_PATTERN}")

    start_time = datetime.now()
    modified_files, total_links_simplified, total_files = process_vault(
        create_backup, args.dry_run, args.max_size, args.start_at, args.max_files
    )
    end_time = datetime.now()

    # Generate report
    print("\n" + "=" * 50)
    print(f"SUMMARY REPORT ({end_time - start_time})")
    print("=" * 50)

    print(f"\nTotal files processed: {total_files}")
    print(f"Files modified: {len(modified_files)}")
    print(f"Total wikilinks simplified: {total_links_simplified}")

    if modified_files:
        print("\nModified files:")
        for file_path, links_simplified in modified_files:
            rel_path = os.path.relpath(file_path, VAULT_PATH)
            print(f"  - {rel_path} ({links_simplified} links)")

    if args.dry_run:
        print("\n[DRY RUN] No files were actually modified.")
        print(
            f"[DRY RUN] Total wikilinks that would be simplified: {total_links_simplified}"
        )
    else:
        print(
            f"\nACTION COMPLETE: {total_links_simplified} wikilinks were simplified in {len(modified_files)} files."
        )

    print("\nCompleted!")


if __name__ == "__main__":
    main()
