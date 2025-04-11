#!/usr/bin/env python3

"""
# Obsidian Attachment Organizer
#
# Purpose:
# This script organizes all attachment files across your entire Obsidian vault into appropriate
# folders based on file type (audio, images, documents, videos).
#
# Technical Implementation:
# - Recursively scans the entire Obsidian vault directory
# - Identifies attachment files by extension and MIME type
# - Categorizes files into audio, image, document, or video types
# - Moves (not copies) each file to its appropriate destination folder
# - Handles file naming conflicts by adding suffixes (_1, _2, etc.)
# - Maintains detailed logs of all operations
# - Generates a JSON report of successful moves and failures
# - Provides a dry-run option to preview changes without actually moving files
#
# Usage:
# - Basic: python organize_obsidian_attachments.py
# - Dry run: python organize_obsidian_attachments.py --dry-run
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
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("attachment_organization_log.txt"),
        logging.StreamHandler(),
    ],
)

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

# Track files for reporting
PROCESSED_FILES = {
    "moved": [],  # Successfully moved files
    "failed": [],  # Files that couldn't be moved
    "skipped": [],  # Files that were skipped
}


def setup_argument_parser():
    parser = argparse.ArgumentParser(
        description="Organize all attachments in Obsidian vault into appropriate folders by type"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what will happen without making changes",
    )
    return parser


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


def process_attachment_file(file_path, dry_run=False):
    """Process a single attachment file, moving it to the appropriate folder."""
    # Skip markdown and certain other files
    if file_path.endswith((".md", ".txt", ".json", ".DS_Store")):
        PROCESSED_FILES["skipped"].append(f"{file_path} (not an attachment file)")
        return False

    # Get the destination based on file type
    attachment_type = get_attachment_type(file_path)
    dest_dir = ATTACHMENT_PATHS[attachment_type]

    # Check if file is already in correct destination folder
    if file_path.startswith(dest_dir):
        PROCESSED_FILES["skipped"].append(f"{file_path} (already in correct location)")
        return False

    # Generate destination path
    filename = os.path.basename(file_path)
    dest_path = os.path.join(dest_dir, filename)

    # Ensure destination directory exists
    if not ensure_directory_exists(dest_dir, dry_run):
        PROCESSED_FILES["failed"].append(
            f"{file_path} (destination directory creation failed)"
        )
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
            return True
        else:
            # Actually move the file instead of copying
            shutil.move(file_path, dest_path)
            logging.info(f"Moved attachment: {file_path} → {dest_path}")
            # Track the moved file
            PROCESSED_FILES["moved"].append(f"{file_path} → {dest_path}")
            return True
    except Exception as e:
        error_msg = str(e)
        logging.error(f"Error moving attachment {file_path}: {error_msg}")
        PROCESSED_FILES["failed"].append(f"{file_path} ({error_msg})")
        return False


def save_processed_files_report(dry_run=False):
    """Save the list of processed files to a JSON file for reference."""
    if dry_run:
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"attachment_organization_report_{timestamp}.json"

    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(PROCESSED_FILES, f, indent=2)
        logging.info(f"Saved processing report to {filename}")
    except Exception as e:
        logging.error(f"Error saving processing report: {str(e)}")


def should_skip_directory(dirpath):
    """Check if a directory should be skipped."""
    # Skip system and config directories
    skip_dirs = [
        ".git",
        "__pycache__",
        ".obsidian",  # Obsidian settings folder
        "node_modules",
    ]

    for skip_dir in skip_dirs:
        if f"/{skip_dir}" in dirpath or dirpath.endswith(f"/{skip_dir}"):
            return True

    # Skip the destination folders themselves - we don't want to process files already
    # in their correct locations
    for dest_dir in ATTACHMENT_PATHS.values():
        if dirpath == dest_dir or dirpath.startswith(dest_dir + "/"):
            return True

    return False


def organize_attachments(vault_dir, dry_run=False):
    """Organize all attachment files in the Obsidian vault into appropriate folders by type."""
    if not os.path.exists(vault_dir):
        logging.error(f"Vault directory does not exist: {vault_dir}")
        return

    # Statistics counters
    processed = 0
    errors = 0
    skipped = 0
    skipped_dirs = 0

    # Process attachments in all subdirectories
    for root, dirs, files in os.walk(vault_dir):
        # Skip certain directories
        if should_skip_directory(root):
            logging.debug(f"Skipping directory: {root}")
            skipped_dirs += 1
            # Modify dirs in-place to prevent os.walk from traversing skipped directories
            dirs[:] = []
            continue

        for file in files:
            file_path = os.path.join(root, file)

            # Process the file if it's an attachment
            if process_attachment_file(file_path, dry_run):
                processed += 1
            else:
                if file_path in PROCESSED_FILES["failed"]:
                    errors += 1
                else:
                    skipped += 1

    # Save the report of processed files
    save_processed_files_report(dry_run)

    # Print summary
    logging.info("\nAttachment Organization Summary:")
    logging.info(f"Processed: {processed}")
    logging.info(f"Errors: {errors}")
    logging.info(f"Skipped files: {skipped}")
    logging.info(f"Skipped directories: {skipped_dirs}")

    # Print files that couldn't be moved
    if not dry_run and PROCESSED_FILES["failed"]:
        logging.warning("\nThe following files could not be moved:")
        for failed_file in PROCESSED_FILES["failed"]:
            logging.warning(f"  - {failed_file}")
        logging.warning("Please check these files manually.")

    # Print summary information
    if not dry_run:
        logging.info(f"\nTotal attachments moved: {len(PROCESSED_FILES['moved'])}")
        logging.info(
            f"Total files that couldn't be moved: {len(PROCESSED_FILES['failed'])}"
        )
        logging.info(
            f"A detailed report has been saved to attachment_organization_report_*.json"
        )

    if dry_run:
        logging.info("This was a dry run. No files were actually modified.")


if __name__ == "__main__":
    # Initialize mimetypes
    mimetypes.init()

    # Parse command line arguments
    parser = setup_argument_parser()
    args = parser.parse_args()

    # Define source directory - your entire Obsidian vault
    vault_dir = "/Users/danildanilov/Obsidian"

    logging.info(f"Starting attachment organization for Obsidian vault: {vault_dir}")
    logging.info(f"Dry run: {args.dry_run}")

    # Run the organization
    organize_attachments(vault_dir, args.dry_run)
