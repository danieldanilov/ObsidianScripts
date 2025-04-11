"""
# Obsidian Tag to Wikilink Converter

## Purpose
This script converts specific tags to wikilinks throughout your Obsidian vault.
It allows for targeted conversion of individual tags or tag patterns based on
your conversion plan.

## Technical Implementation
- Uses recursive globbing to find all Markdown (.md) files in the vault
- Replaces specified tags with corresponding wikilinks
- Creates backups of modified files
- Generates a summary report of changes made
- Handles YAML frontmatter appropriately

## Usage
Run this script from the command line with:
    python convert_tags_to_wikilinks.py --tag "#tag/to/convert" --wikilink "Replacement Note"

Required arguments:
    --tag: The tag to convert (include the # prefix)
    --wikilink: The note name to use in the wikilink (without [[]])

Optional flags:
    --dry-run: Preview changes without modifying files
    --no-backup: Skip creating backup files
    --convert-yaml: Also convert tags in YAML frontmatter to wikilinks
    --exact-match: Only convert exact tag matches (not nested tags)

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


def convert_tag_to_wikilink(
    file_path,
    tag,
    wikilink,
    create_backup=True,
    dry_run=False,
    convert_yaml=False,
    exact_match=False,
):
    """
    Convert a specific tag to a wikilink in a file.

    Args:
        file_path (str): Path to the markdown file
        tag (str): The tag to convert (with # prefix)
        wikilink (str): The note name to use in the wikilink (without [[]])
        create_backup (bool): Whether to create a backup of the original file
        dry_run (bool): If True, only simulate changes without writing to files
        convert_yaml (bool): Whether to convert tags in YAML frontmatter
        exact_match (bool): Only convert exact tag matches

    Returns:
        tuple: (bool indicating if file was modified, int count of tags converted)
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()

        # Check if file contains the tag
        if tag not in content:
            return False, 0

        # Split content into YAML frontmatter and body
        yaml_end = None
        if content.startswith("---"):
            yaml_end = content.find("---", 3)

        if yaml_end is not None and yaml_end > 0:
            yaml_content = content[: yaml_end + 3]
            body_content = content[yaml_end + 3 :]
        else:
            yaml_content = ""
            body_content = content

        # Process body content (always convert in main content)
        if exact_match:
            # Exact match pattern
            tag_pattern = r"(?<!\w)" + re.escape(tag) + r"(?!\w)"
        else:
            # Also match nested tags that start with this tag
            tag_pattern = r"(?<!\w)" + re.escape(tag) + r"(?:/[a-zA-Z0-9_.-]+)*(?!\w)"

        # Count occurrences
        body_matches = re.findall(tag_pattern, body_content)
        tag_count = len(body_matches)

        # Replace tags with wikilinks in body
        body_content = re.sub(tag_pattern, f"[[{wikilink}]]", body_content)

        # Process YAML frontmatter if requested
        yaml_count = 0
        if convert_yaml and yaml_content:
            # This is more complex - we need to handle YAML tag arrays
            yaml_lines = yaml_content.split("\n")
            modified_yaml_lines = []

            in_tags_block = False
            for line in yaml_lines:
                if line.strip().startswith("tags:"):
                    in_tags_block = True
                    modified_yaml_lines.append(line)
                elif in_tags_block and line.strip().startswith("-"):
                    tag_in_line = line.strip()[1:].strip()
                    if tag_in_line == tag.strip() or (
                        not exact_match and tag_in_line.startswith(tag.strip())
                    ):
                        # Convert this tag to related YAML entry
                        related_line = f'related:\n  - "[[{wikilink}]]"'
                        if "related:" not in yaml_content:
                            modified_yaml_lines.append(related_line)
                        else:
                            # Skip this line as we'll add to existing related
                            yaml_count += 1
                            continue
                    else:
                        modified_yaml_lines.append(line)
                else:
                    in_tags_block = False

                    # If this is the related: line, add our wikilink
                    if line.strip().startswith("related:") and yaml_count > 0:
                        modified_yaml_lines.append(line)
                        modified_yaml_lines.append(f'  - "[[{wikilink}]]"')
                        yaml_count = 0  # Reset so we don't add multiple times
                    else:
                        modified_yaml_lines.append(line)

            yaml_content = "\n".join(modified_yaml_lines)

        # Combine content back together
        modified_content = yaml_content + body_content

        # Only proceed if content actually changed
        if content != modified_content:
            if not dry_run:
                # Create backup if requested
                if create_backup:
                    backup_path = file_path + f".{tag.replace('#', '')}.backup"
                    with open(backup_path, "w", encoding="utf-8") as backup_file:
                        backup_file.write(content)

                # Write modified content
                with open(file_path, "w", encoding="utf-8") as file:
                    file.write(modified_content)

                print(
                    f"Converted {tag_count + yaml_count} tags in: {os.path.relpath(file_path, VAULT_PATH)}"
                )

            return True, tag_count + yaml_count
        return False, 0

    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")
        return False, 0


def process_vault(
    tag,
    wikilink,
    create_backup=True,
    dry_run=False,
    convert_yaml=False,
    exact_match=False,
):
    """
    Process all markdown files in the vault to convert a specific tag.

    Args:
        tag (str): The tag to convert (with # prefix)
        wikilink (str): The note name to use in the wikilink (without [[]])
        create_backup (bool): Whether to create backups of modified files
        dry_run (bool): If True, only simulate changes without writing to files
        convert_yaml (bool): Whether to convert tags in YAML frontmatter
        exact_match (bool): Only convert exact tag matches

    Returns:
        tuple: (list of modified files, total tags converted, total files processed)
    """
    # Find all markdown files
    md_files = glob.glob(f"{VAULT_PATH}/**/*.md", recursive=True)

    modified_files = []
    total_tags_converted = 0

    file_count = len(md_files)
    print(f"Found {file_count} markdown files to process")

    for i, file_path in enumerate(md_files):
        # Progress indicator
        if i % 100 == 0:
            print(
                f"Processing file {i+1}/{file_count}... ({((i+1)/file_count)*100:.1f}%)"
            )

        was_modified, tags_converted = convert_tag_to_wikilink(
            file_path, tag, wikilink, create_backup, dry_run, convert_yaml, exact_match
        )
        if was_modified:
            modified_files.append((file_path, tags_converted))
            total_tags_converted += tags_converted

    return modified_files, total_tags_converted, file_count


def main():
    """Main function to parse arguments and run the script."""
    parser = argparse.ArgumentParser(
        description="Convert tags to wikilinks in an Obsidian vault."
    )
    parser.add_argument(
        "--tag", required=True, help="The tag to convert (include the # prefix)"
    )
    parser.add_argument(
        "--wikilink",
        required=True,
        help="The note name to use in the wikilink (without [[]])",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without modifying files"
    )
    parser.add_argument(
        "--no-backup", action="store_true", help="Skip creating backup files"
    )
    parser.add_argument(
        "--convert-yaml",
        action="store_true",
        help="Also convert tags in YAML frontmatter to wikilinks",
    )
    parser.add_argument(
        "--exact-match",
        action="store_true",
        help="Only convert exact tag matches (not nested tags)",
    )
    args = parser.parse_args()

    create_backup = not args.no_backup

    # Validate the tag
    if not args.tag.startswith("#"):
        print("Error: Tag must start with # prefix")
        return

    print(f"{'[DRY RUN] ' if args.dry_run else ''}Starting tag conversion...")
    print(f"Converting: {args.tag} → [[{args.wikilink}]]")
    print(f"Vault path: {VAULT_PATH}")
    print(f"Creating backups: {'No' if args.no_backup else 'Yes'}")
    print(f"Converting in YAML: {'Yes' if args.convert_yaml else 'No'}")
    print(f"Using exact matching: {'Yes' if args.exact_match else 'No'}")

    start_time = datetime.now()
    modified_files, total_tags_converted, total_files = process_vault(
        args.tag,
        args.wikilink,
        create_backup,
        args.dry_run,
        args.convert_yaml,
        args.exact_match,
    )
    end_time = datetime.now()

    # Generate report
    print("\n" + "=" * 50)
    print(f"SUMMARY REPORT ({end_time - start_time})")
    print("=" * 50)

    print(f"\nTotal files processed: {total_files}")
    print(f"Files modified: {len(modified_files)}")
    print(f"Total tags converted: {total_tags_converted}")

    if modified_files:
        print("\nModified files:")
        for file_path, tags_converted in modified_files:
            rel_path = os.path.relpath(file_path, VAULT_PATH)
            print(f"  - {rel_path} ({tags_converted} tags)")

    if args.dry_run:
        print("\n[DRY RUN] No files were actually modified.")
    else:
        print(
            f"\nACTION COMPLETE: Converted {total_tags_converted} tags to [[{args.wikilink}]] in {len(modified_files)} files."
        )

    print("\nCompleted!")


if __name__ == "__main__":
    main()
