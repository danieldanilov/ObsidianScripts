"""
# Obsidian Tag Inventory

## Purpose
This script scans an entire Obsidian vault and creates an inventory of all unique tags,
sorted by frequency of use. This helps in planning a systematic conversion from
tags to wikilinks by identifying which tags to prioritize.

## Technical Implementation
- Uses recursive globbing to find all Markdown (.md) files in the vault
- Uses regex to identify all #tags (including nested tags)
- Counts occurrences of each tag and sorts by frequency
- Generates a detailed report showing tag usage patterns
- Creates a conversion plan Markdown file

## Usage
Run this script from the command line with:
    python tag_inventory.py

Optional flags:
    --output: Custom path for the output report (default: "99 - Meta/Tag Conversion Plan.md")
    --min-count: Minimum number of occurrences to include in report (default: 1)
    --exclude-done: Exclude #done tags from the report

## Dependencies
- os: For file operations and path handling
- re: For regular expression pattern matching
- glob: For finding files recursively
- argparse: For command-line argument parsing
- collections: For counting and sorting tags
"""

import os
import re
import glob
import argparse
from datetime import datetime
from collections import Counter

# Define the root directory of your Obsidian vault
VAULT_PATH = "/Users/danildanilov/Obsidian"

# Regex pattern to match tags, including nested tags
TAG_PATTERN = r"#[a-zA-Z0-9_/.-]+"


def scan_file_for_tags(file_path):
    """
    Scan a markdown file for all tags.

    Args:
        file_path (str): Path to the markdown file

    Returns:
        list: List of tags found in the file
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()

        # Find all tags using regex
        tags = re.findall(TAG_PATTERN, content)
        return tags

    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")
        return []


def inventory_tags(exclude_done=False):
    """
    Create a complete inventory of all tags in the vault.

    Args:
        exclude_done (bool): Whether to exclude #done tags from the inventory

    Returns:
        tuple: (Counter object with tag counts, total number of files processed)
    """
    # Find all markdown files
    md_files = glob.glob(f"{VAULT_PATH}/**/*.md", recursive=True)

    tag_counter = Counter()
    file_count = len(md_files)

    print(f"Scanning {file_count} markdown files for tags...")

    for i, file_path in enumerate(md_files):
        # Progress indicator
        if i % 100 == 0:
            print(
                f"Processing file {i+1}/{file_count}... ({((i+1)/file_count)*100:.1f}%)"
            )

        file_tags = scan_file_for_tags(file_path)

        # Filter out #done tags if requested
        if exclude_done:
            file_tags = [tag for tag in file_tags if not tag.startswith("#done")]

        tag_counter.update(file_tags)

    return tag_counter, file_count


def generate_tag_report(tag_counter, file_count, min_count=1):
    """
    Generate a Markdown report of tag usage.

    Args:
        tag_counter (Counter): Counter object with tag counts
        file_count (int): Total number of files processed
        min_count (int): Minimum count to include in report

    Returns:
        str: Markdown-formatted report
    """
    # Filter tags by minimum count
    filtered_tags = {
        tag: count for tag, count in tag_counter.items() if count >= min_count
    }

    # Sort tags by count (descending) and then alphabetically
    sorted_tags = sorted(filtered_tags.items(), key=lambda x: (-x[1], x[0]))

    # Generate report
    report = "# Tag to Wikilink Conversion Plan\n\n"
    report += f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n"
    report += f"## Summary\n\n"
    report += f"- Total files scanned: {file_count}\n"
    report += f"- Unique tags found: {len(tag_counter)}\n"
    report += f"- Tags with at least {min_count} occurrences: {len(filtered_tags)}\n\n"

    # Add tag hierarchy analysis
    root_tags = {}
    for tag in tag_counter.keys():
        parts = tag.split("/")
        root = parts[0]
        if root not in root_tags:
            root_tags[root] = []
        if len(parts) > 1:
            root_tags[root].append(tag)

    report += f"## Tag Hierarchies\n\n"
    for root, nested_tags in sorted(root_tags.items()):
        report += f"### {root}\n\n"
        if nested_tags:
            report += "Nested tags:\n"
            for tag in sorted(nested_tags):
                report += f"- {tag} ({tag_counter[tag]} occurrences)\n"
        else:
            report += f"No nested tags. Root occurrence count: {tag_counter[root]}\n"
        report += "\n"

    # Add detailed tag list
    report += f"## Complete Tag List (sorted by frequency)\n\n"
    report += "| Tag | Occurrences | Suggested Wikilink | Status |\n"
    report += "|-----|-------------|-------------------|--------|\n"

    for tag, count in sorted_tags:
        # Create suggested wikilink name
        suggested_wikilink = tag.replace("#", "").replace("/", " - ")
        report += f"| `{tag}` | {count} | [[{suggested_wikilink}]] | 🔄 To Convert |\n"

    # Add conversion instructions
    report += "\n## Conversion Instructions\n\n"
    report += (
        "1. Review the tag list above and adjust the suggested wikilinks as needed\n"
    )
    report += "2. For each tag, create a corresponding note (if it doesn't exist)\n"
    report += "3. Use the `convert_tags_to_wikilinks.py` script to convert each tag\n"
    report += "4. Update the Status column in this document as you go\n"

    return report


def save_report(report, output_path):
    """Save the tag report to the specified file."""
    try:
        # Create directories if they don't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as file:
            file.write(report)

        print(f"\nTag inventory report saved to: {output_path}")
        return True
    except Exception as e:
        print(f"Error saving report: {str(e)}")
        return False


def main():
    """Main function to parse arguments and run the script."""
    parser = argparse.ArgumentParser(
        description="Create an inventory of all tags in an Obsidian vault."
    )
    parser.add_argument(
        "--output",
        default=os.path.join(VAULT_PATH, "99 - Meta", "Tag Conversion Plan.md"),
        help="Path to save the output report (default: 99 - Meta/Tag Conversion Plan.md)",
    )
    parser.add_argument(
        "--min-count",
        type=int,
        default=1,
        help="Minimum number of occurrences to include in report (default: 1)",
    )
    parser.add_argument(
        "--exclude-done", action="store_true", help="Exclude #done tags from the report"
    )
    args = parser.parse_args()

    print("Starting tag inventory...")

    start_time = datetime.now()
    tag_counter, file_count = inventory_tags(args.exclude_done)
    end_time = datetime.now()

    print(f"\nFound {len(tag_counter)} unique tags across {file_count} files")
    print(f"Time taken: {end_time - start_time}")

    # Generate and save the report
    report = generate_tag_report(tag_counter, file_count, args.min_count)
    save_report(report, args.output)

    # Show top 10 tags as a preview
    print("\nTop 10 most common tags:")
    for tag, count in tag_counter.most_common(10):
        print(f"  {tag}: {count} occurrences")

    print("\nCompleted!")


if __name__ == "__main__":
    main()
