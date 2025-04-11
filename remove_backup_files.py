"""
# Obsidian Backup File Cleaner

## Purpose
This script is designed to clean up backup files within an Obsidian vault. It identifies all files with a `.bak` extension and removes them if a corresponding original file exists. This helps in maintaining a clean and organized vault by eliminating unnecessary backup files.

## Technical Implementation
- The script searches recursively through the specified vault directory for files ending with `.bak`.
- For each backup file found, it checks if the original file (same name without the `.bak` extension) exists.
- If the original file exists, the backup file is deleted.
- If the original file does not exist, the backup file is retained.
- The script can be run in a "dry run" mode where it simulates the deletion process without actually removing any files.

## Usage
Run this script from the command line with:
    python remove_backup_files.py

Optional flags:
    --vault-path: Specify the path to the Obsidian vault (default is set in the script)
    --dry-run: Preview changes without deleting files

## Dependencies
- os: For file operations and path handling
- glob: For finding files recursively
- argparse: For command-line argument parsing
"""

import os
import glob
from pathlib import Path

# Define the root directory of your Obsidian vault - change this to your vault path
VAULT_PATH = "/Users/danildanilov/Obsidian"  # Update this path


def find_and_remove_backup_files(vault_path, dry_run=False):
    """
    Find all .bak files and remove those that have a corresponding original file.

    Args:
        vault_path: Path to the Obsidian vault
        dry_run: If True, only simulate deletion without actually removing files
    """
    # Find all backup files
    backup_files = glob.glob(f"{vault_path}/**/*.bak", recursive=True)

    total_backups = len(backup_files)
    print(f"Found {total_backups} backup files.")

    deleted_files = []
    kept_files = []

    for backup_path in backup_files:
        # Get the path of the corresponding original file
        original_path = backup_path[:-4]  # Remove .bak extension

        # Check if original file exists
        if os.path.exists(original_path):
            # Original exists, so this backup can be deleted
            if not dry_run:
                try:
                    os.remove(backup_path)
                    deleted_files.append(backup_path)
                    print(f"Deleted: {os.path.relpath(backup_path, vault_path)}")
                except Exception as e:
                    print(f"Error deleting {backup_path}: {e}")
            else:
                deleted_files.append(backup_path)
                print(f"Would delete: {os.path.relpath(backup_path, vault_path)}")
        else:
            # No original, keep the backup
            kept_files.append(backup_path)
            print(
                f"Keeping: {os.path.relpath(backup_path, vault_path)} (no original file)"
            )

    # Summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"Total backup files found: {total_backups}")
    print(f"Backup files deleted: {len(deleted_files)}")
    print(f"Backup files kept: {len(kept_files)}")

    if kept_files:
        print("\nBackup files kept (no original file exists):")
        for file_path in kept_files:
            print(f"  - {os.path.relpath(file_path, vault_path)}")

    return deleted_files, kept_files


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Clean up backup files in Obsidian vault"
    )
    parser.add_argument(
        "--vault-path", type=str, default=VAULT_PATH, help="Path to Obsidian vault"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without deleting files"
    )

    args = parser.parse_args()

    print(
        f"{'[DRY RUN] ' if args.dry_run else ''}Searching for backup files in {args.vault_path}"
    )
    find_and_remove_backup_files(args.vault_path, args.dry_run)

    if args.dry_run:
        print(
            "\n[DRY RUN] No files were actually deleted. Run without --dry-run to perform deletion."
        )
