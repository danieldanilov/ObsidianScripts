#!/usr/bin/env python3

"""
# NotePlan Calendar Notes Migration Tool
#
# Purpose:
# This script migrates calendar notes from NotePlan backup files to Obsidian with proper
# formatting and organization. It handles different types of calendar notes (daily, weekly,
# monthly, quarterly, yearly) and their associated attachments.
#
# Technical Implementation:
# - Processes calendar notes with various formats (e.g. 20220325.md → 2022-03-25.md)
# - Migrates notes to appropriate folders based on their type (daily, weekly, monthly, etc.)
# - Merges content when files with the same date already exist in destination
# - Processes attachment folders (e.g. 20210708_attachments) and categorizes files by type
# - Copies files to maintain originals in the backup location
# - Tracks all modified files for potential recovery if needed
# - Provides a dry-run option and detailed logging
#
# Usage:
# - Basic: python migrate_noteplan_calendar_notes.py
# - Dry run: python migrate_noteplan_calendar_notes.py --dry-run
# - Skip attachments: python migrate_noteplan_calendar_notes.py --skip-attachments
#
# Author: Created with assistance from Claude
# Date: Created in 2024
"""

import os
import re
import shutil
import logging
from datetime import datetime
import argparse
import mimetypes
import pathlib
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("migration_log.txt"), logging.StreamHandler()],
)

# File pattern matchers
PATTERNS = {
    "daily": r"^(\d{8})\.md$",  # 20220325.md
    "monthly": r"^(\d{4})[-.](\d{2})\.md$",  # 2023-01.md or 2023.01.md
    "weekly": r"^(\d{4})[-.]?W(\d{1,2})\.md$",  # 2023-W27.md or 2023W27.md
    "quarterly": r"^(\d{4})[-.]?Q([1-4])\.md$",  # 2023-Q1.md or 2023Q1.md
    "yearly": r"^(\d{4})\.md$",  # 2024.md
}

# Define destination paths
DEST_PATHS = {
    "daily": "/Users/danildanilov/Obsidian/01 - Calendar/Daily",
    "weekly": "/Users/danildanilov/Obsidian/01 - Calendar/Weekly",
    "monthly": "/Users/danildanilov/Obsidian/01 - Calendar/Monthly",
    "quarterly": "/Users/danildanilov/Obsidian/01 - Calendar/Quarterly",
    "yearly": "/Users/danildanilov/Obsidian/01 - Calendar/Yearly",
}

# Define attachment paths
ATTACHMENT_PATHS = {
    "audio": "/Users/danildanilov/Obsidian/99 - Meta/99 - Files/Audio",
    "image": "/Users/danildanilov/Obsidian/99 - Meta/99 - Files/Images",
    "document": "/Users/danildanilov/Obsidian/99 - Meta/99 - Files/PDFs",
    "video": "/Users/danildanilov/Obsidian/99 - Meta/99 - Files/Videos",
}

# File extensions by type
FILE_TYPES = {
    "audio": [".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac"],
    "image": [
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".webp",
        ".svg",
        ".heic",
        ".heif",
        ".bmp",
        ".tiff",
        ".tif",
    ],
    "document": [
        ".pdf",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".ppt",
        ".pptx",
        ".txt",
        ".rtf",
        ".csv",
        ".epub",
    ],
    "video": [".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv", ".webm", ".m4v"],
}

# Track modified files for potential recovery
MODIFIED_FILES = {"created": [], "modified": [], "attachments_moved": []}


def setup_argument_parser():
    parser = argparse.ArgumentParser(
        description="Migrate NotePlan notes to Obsidian format"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what will happen without making changes",
    )
    parser.add_argument(
        "--skip-attachments",
        action="store_true",
        help="Skip processing of attachment folders",
    )
    return parser


def identify_file_type(filename):
    """Identify the type of note file based on filename pattern."""
    for file_type, pattern in PATTERNS.items():
        if re.match(pattern, filename):
            return file_type
    return None


def get_attachment_type(file_path):
    """Determine the attachment type based on file extension."""
    extension = os.path.splitext(file_path)[1].lower()

    for file_type, extensions in FILE_TYPES.items():
        if extension in extensions:
            return file_type

    # If extension not in predefined list, use mimetypes
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type:
        if mime_type.startswith("audio/"):
            return "audio"
        elif mime_type.startswith("image/"):
            return "image"
        elif mime_type.startswith("video/"):
            return "video"
        elif mime_type.startswith("application/"):
            return "document"

    # Default to document
    return "document"


def convert_filename(old_filename, file_type):
    """Convert filename to the appropriate format based on the file type."""
    if file_type == "daily":
        # Convert 20220325.md to 2022-03-25.md
        date_part = old_filename[:8]
        return f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}.md"

    elif file_type == "monthly":
        # Normalize to YYYY-MM.md
        match = re.match(PATTERNS["monthly"], old_filename)
        if match:
            year, month = match.groups()
            return f"{year}-{month}.md"

    elif file_type == "weekly":
        # Normalize to YYYY-W##.md
        match = re.match(PATTERNS["weekly"], old_filename)
        if match:
            year, week = match.groups()
            return f"{year}-W{week.zfill(2)}.md"

    elif file_type == "quarterly":
        # Normalize to YYYY-Q#.md
        match = re.match(PATTERNS["quarterly"], old_filename)
        if match:
            year, quarter = match.groups()
            return f"{year}-Q{quarter}.md"

    elif file_type == "yearly":
        # Keep as YYYY.md
        return old_filename

    # If no conversion needed or possible, return original
    return old_filename


def merge_file_contents(source_path, dest_path):
    """Merge contents of source file into destination file with a clear separator."""
    try:
        # Read source content
        with open(source_path, "r", encoding="utf-8") as source_file:
            source_content = source_file.read()

        # Read destination content
        with open(dest_path, "r", encoding="utf-8") as dest_file:
            dest_content = dest_file.read()

        # Create a separator with filename and date
        source_filename = os.path.basename(source_path)
        separator = f"\n\n---\n\n**Content imported from NotePlan ({source_filename}) on {datetime.now().strftime('%Y-%m-%d')}:**\n\n"

        # Write merged content
        with open(dest_path, "w", encoding="utf-8") as merged_file:
            merged_file.write(dest_content + separator + source_content)

        # Track the modified file
        MODIFIED_FILES["modified"].append(dest_path)

        return True
    except Exception as e:
        logging.error(f"Error merging files {source_path} and {dest_path}: {str(e)}")
        return False


def ensure_directory_exists(directory_path, dry_run=False):
    """Ensure the directory exists, create if it doesn't."""
    if not os.path.exists(directory_path):
        if dry_run:
            logging.info(f"Would create directory: {directory_path}")
        else:
            try:
                os.makedirs(directory_path, exist_ok=True)
                logging.info(f"Created directory: {directory_path}")
            except Exception as e:
                logging.error(f"Failed to create directory {directory_path}: {str(e)}")
                return False
    return True


def process_note_file(source_path, file_type, dry_run=False):
    """Process a single note file based on its type."""
    filename = os.path.basename(source_path)
    new_filename = convert_filename(filename, file_type)
    dest_dir = DEST_PATHS[file_type]
    dest_path = os.path.join(dest_dir, new_filename)

    # Ensure destination directory exists
    if not ensure_directory_exists(dest_dir, dry_run):
        return False

    try:
        # Handle existing files
        if os.path.exists(dest_path):
            if dry_run:
                logging.info(f"Would merge contents: {source_path} → {dest_path}")
            else:
                if merge_file_contents(source_path, dest_path):
                    logging.info(f"Merged contents: {source_path} → {dest_path}")
                    return True
                else:
                    return False
        else:
            if dry_run:
                logging.info(f"Would copy file: {source_path} → {dest_path}")
            else:
                shutil.copy2(source_path, dest_path)
                logging.info(f"Copied file: {source_path} → {dest_path}")
                # Track the created file
                MODIFIED_FILES["created"].append(dest_path)
                return True
    except Exception as e:
        logging.error(f"Error processing {filename}: {str(e)}")
        return False


def process_attachment_file(file_path, dry_run=False):
    """Process a single attachment file, moving it to the appropriate folder."""
    attachment_type = get_attachment_type(file_path)
    dest_dir = ATTACHMENT_PATHS[attachment_type]
    filename = os.path.basename(file_path)
    dest_path = os.path.join(dest_dir, filename)

    # Ensure destination directory exists
    if not ensure_directory_exists(dest_dir, dry_run):
        return False

    # Handle filename conflict
    counter = 1
    original_filename = filename
    while os.path.exists(dest_path) and not dry_run:
        name, ext = os.path.splitext(original_filename)
        filename = f"{name}_{counter}{ext}"
        dest_path = os.path.join(dest_dir, filename)
        counter += 1

    try:
        if dry_run:
            logging.info(f"Would move attachment: {file_path} → {dest_path}")
        else:
            shutil.copy2(file_path, dest_path)
            logging.info(f"Moved attachment: {file_path} → {dest_path}")
            # Track the moved attachment
            MODIFIED_FILES["attachments_moved"].append(dest_path)
        return True
    except Exception as e:
        logging.error(f"Error processing attachment {file_path}: {str(e)}")
        return False


def process_attachment_folder(folder_path, dry_run=False):
    """Process an attachment folder and all its contents."""
    processed = 0
    errors = 0

    if not os.path.exists(folder_path):
        logging.error(f"Attachment folder does not exist: {folder_path}")
        return 0, 0

    for root, _, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            if process_attachment_file(file_path, dry_run):
                processed += 1
            else:
                errors += 1

    return processed, errors


def save_modified_files_list(dry_run=False):
    """Save the list of modified files to a JSON file for recovery purposes."""
    if dry_run:
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"migration_modified_files_{timestamp}.json"

    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(MODIFIED_FILES, f, indent=2)
        logging.info(f"Saved list of modified files to {filename}")
    except Exception as e:
        logging.error(f"Error saving modified files list: {str(e)}")


def migrate_files(source_dir, dry_run=False, skip_attachments=False):
    """Migrate all files from source directory."""
    if not os.path.exists(source_dir):
        logging.error(f"Source directory does not exist: {source_dir}")
        return

    # Statistics counters
    stats = {
        "daily": {"processed": 0, "errors": 0},
        "weekly": {"processed": 0, "errors": 0},
        "monthly": {"processed": 0, "errors": 0},
        "quarterly": {"processed": 0, "errors": 0},
        "yearly": {"processed": 0, "errors": 0},
        "attachments": {"processed": 0, "errors": 0},
        "skipped": 0,
    }

    # First, process all the note files
    for item in os.listdir(source_dir):
        item_path = os.path.join(source_dir, item)

        # Handle attachment folders
        if os.path.isdir(item_path) and "_attachments" in item:
            if skip_attachments:
                logging.info(f"Skipping attachment folder: {item_path}")
            else:
                logging.info(f"Processing attachment folder: {item_path}")
                processed, errors = process_attachment_folder(item_path, dry_run)
                stats["attachments"]["processed"] += processed
                stats["attachments"]["errors"] += errors
            continue

        # Skip directories that are not attachment folders
        if os.path.isdir(item_path):
            logging.debug(f"Skipping non-attachment directory: {item_path}")
            continue

        # Process note files
        if item.endswith(".md"):
            file_type = identify_file_type(item)
            if file_type:
                if process_note_file(item_path, file_type, dry_run):
                    stats[file_type]["processed"] += 1
                else:
                    stats[file_type]["errors"] += 1
            else:
                logging.info(f"Skipping file with unrecognized format: {item}")
                stats["skipped"] += 1
        else:
            logging.debug(f"Skipping non-markdown file: {item}")
            stats["skipped"] += 1

    # Save the list of modified files for recovery
    save_modified_files_list(dry_run)

    # Print summary
    logging.info("\nMigration Summary:")
    logging.info(
        f"Daily notes: {stats['daily']['processed']} processed, {stats['daily']['errors']} errors"
    )
    logging.info(
        f"Weekly notes: {stats['weekly']['processed']} processed, {stats['weekly']['errors']} errors"
    )
    logging.info(
        f"Monthly notes: {stats['monthly']['processed']} processed, {stats['monthly']['errors']} errors"
    )
    logging.info(
        f"Quarterly notes: {stats['quarterly']['processed']} processed, {stats['quarterly']['errors']} errors"
    )
    logging.info(
        f"Yearly notes: {stats['yearly']['processed']} processed, {stats['yearly']['errors']} errors"
    )
    logging.info(
        f"Attachments: {stats['attachments']['processed']} processed, {stats['attachments']['errors']} errors"
    )
    logging.info(f"Skipped files: {stats['skipped']}")

    # Print recovery information
    if not dry_run:
        total_modified = (
            len(MODIFIED_FILES["created"])
            + len(MODIFIED_FILES["modified"])
            + len(MODIFIED_FILES["attachments_moved"])
        )
        logging.info(f"\nTotal files modified: {total_modified}")
        logging.info(f"  - Files created: {len(MODIFIED_FILES['created'])}")
        logging.info(f"  - Files modified: {len(MODIFIED_FILES['modified'])}")
        logging.info(
            f"  - Attachments moved: {len(MODIFIED_FILES['attachments_moved'])}"
        )
        logging.info(
            f"A list of all modified files has been saved to migration_modified_files_*.json"
        )

    if dry_run:
        logging.info("This was a dry run. No files were actually modified.")


if __name__ == "__main__":
    # Initialize mimetypes
    mimetypes.init()

    # Parse command line arguments
    parser = setup_argument_parser()
    args = parser.parse_args()

    # Define source directory
    source_dir = "/Users/danildanilov/Obsidian/99 - 2025-01-09 NotePlan Backup/NotePlanCalendarBackUp"

    logging.info(f"Starting migration from {source_dir}")
    logging.info(f"Dry run: {args.dry_run}")
    logging.info(f"Skip attachments: {args.skip_attachments}")

    # Run the migration
    migrate_files(source_dir, args.dry_run, args.skip_attachments)
