# Script Definition, Details, and Technical Implementation:
#
# **Purpose:**
# This script scans a specified directory (an Obsidian vault) for all Markdown files (.md)
# and uses the OpenAI API to generate or update YAML front matter according to defined rules.
# It references the rules specified in "How to write YAML in Obsidian.md" to ensure consistency.
#
# **Functionality:**
# 1. Recursively walks through the specified root directory (Obsidian vault).
# 2. Identifies all files with the '.md' extension.
# 3. For EACH file (regardless of whether it already has YAML or not):
#    a. Extracts any existing YAML front matter and main content.
#    b. Reads the YAML rules from "How to write YAML in Obsidian.md".
#    c. Calls OpenAI API to generate new YAML based on file content and existing YAML (if any),
#       following the rules in "How to write YAML in Obsidian.md".
#    d. Replaces the original file content with new YAML and original body content.
# 4. Reports which files were modified.
#
# **Technical Implementation:**
# - Uses the `os` module for directory traversal and path manipulation.
# - Uses standard file I/O operations for reading and writing file content.
# - Uses the `openai` library to interact with the OpenAI API.
# - Uses `python-dotenv` to load the API key from a .env.local file.
# - Includes error handling for file operations and API calls.
# - The root directory to scan is determined dynamically based on the script's location.

import os
import sys
import datetime
import re
import shutil
from pathlib import Path
from typing import List, Optional, Tuple, Dict

# Import the OpenAI library and dotenv for loading environment variables
# You can install them using pip with the following command:
# pip install openai python-dotenv

import openai  # type: ignore
from dotenv import load_dotenv  # type: ignore

# --- Load Environment Variables ---

# Look for .env.local file in the script's directory
script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, ".env.local")

# Load environment variables from .env.local
load_dotenv(env_path)

# Configure OpenAI with the API key
api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    print("Error: OPENAI_API_KEY not found in .env.local file.", file=sys.stderr)
    sys.exit(1)

# Set the API key for the OpenAI library
openai.api_key = api_key
print("OpenAI API configured successfully.")

# --- Helper Functions ---


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
            # Look for the closing '---' within the next ~30 lines
            for i, line in enumerate(f):
                if line.strip() == "---":
                    return True
                if i > 30:  # Stop checking after a reasonable number of lines
                    break
            return False
    except FileNotFoundError:
        print(f"Error: File not found during YAML check: {filepath}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Error reading file {filepath} during YAML check: {e}", file=sys.stderr)
        return False


def extract_content_parts(filepath: str) -> Tuple[str, str]:
    """
    Extracts YAML front matter and main content from a Markdown file.

    Args:
        filepath (str): The path to the file.

    Returns:
        Tuple[str, str]: A tuple containing (yaml_content, main_content).
        If no YAML exists, yaml_content will be an empty string.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Check if file has YAML front matter
        if content.startswith("---"):
            # Find the second '---' that closes the YAML block
            parts = content.split("---", 2)
            if len(parts) >= 3:
                yaml_content = parts[1].strip()
                main_content = parts[2].strip()
                return yaml_content, main_content

        # If no YAML or invalid format, return empty YAML and full content
        return "", content.strip()
    except Exception as e:
        print(f"Error extracting content from {filepath}: {e}", file=sys.stderr)
        return "", ""


def read_yaml_rules() -> str:
    """
    Read the YAML rules from the "How to write YAML in Obsidian.md" file.

    Returns:
        str: The content of the rules file, or an empty string if not found.
    """
    # Find the path to the rules file
    script_location = os.path.dirname(os.path.abspath(__file__))
    vault_root = os.path.dirname(os.path.dirname(script_location))
    rules_path = os.path.join(vault_root, "How to write YAML in Obsidian.md")

    try:
        with open(rules_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract just the rules section (after the YAML front matter)
        if "---" in content:
            parts = content.split("---", 2)
            if len(parts) >= 3:
                return parts[2].strip()

        # If no YAML or format issues, return the whole content
        return content
    except FileNotFoundError:
        print(f"Warning: YAML rules file not found at {rules_path}", file=sys.stderr)
        return ""
    except Exception as e:
        print(f"Error reading YAML rules file: {e}", file=sys.stderr)
        return ""


def extract_content_summary(content: str, max_length: int = 3000) -> str:
    """
    Extract a meaningful summary of the content for the AI prompt.

    Args:
        content (str): The full content of the file.
        max_length (int): Maximum length to include.

    Returns:
        str: Summarized content suitable for the AI prompt.
    """
    # If the content is short enough, just return it
    if len(content) <= max_length:
        return content

    # Otherwise, take the first part + some middle + last part
    first_portion = max_length // 2
    last_portion = max_length // 4
    middle_sample = max_length - first_portion - last_portion

    first_part = content[:first_portion]
    middle_part = content[
        len(content) // 2 - middle_sample // 2 : len(content) // 2 + middle_sample // 2
    ]
    last_part = content[-last_portion:]

    return f"{first_part}\n\n[...content truncated...]\n\n{middle_part}\n\n[...content truncated...]\n\n{last_part}"


def create_backup(filepath: str) -> bool:
    """
    Creates a backup of the specified file before modifying it.

    Args:
        filepath (str): Path to the file to back up.

    Returns:
        bool: True if backup was successful, False otherwise.
    """
    backup_path = f"{filepath}.bak"
    try:
        shutil.copy2(filepath, backup_path)
        return True
    except Exception as e:
        print(f"Warning: Failed to create backup of {filepath}: {e}", file=sys.stderr)
        return False


# --- OpenAI Integration ---


def generate_yaml_with_ai(
    file_content: str,
    filename: str,
    filepath: str = "",
    existing_yaml: str = "",
    yaml_rules: str = "",
) -> str:
    """
    Generates YAML front matter content using OpenAI's API.

    Args:
        file_content (str): The main content of the Markdown file (without YAML).
        filename (str): The name of the file.
        filepath (str, optional): The relative path of the file.
        existing_yaml (str, optional): Any existing YAML in the file.
        yaml_rules (str, optional): The YAML formatting rules.

    Returns:
        str: The generated YAML content (without the '---' markers).
             Returns an empty string if generation fails.
    """
    # Extract potential title from filename or first H1 heading
    title = filename.replace(".md", "").replace("_", " ").title()  # Basic title guess

    lines = file_content.strip().split("\n")
    if lines and lines[0].startswith("# "):
        title = lines[0][2:].strip()

    # Determine relative path and folder structure for context
    file_location = ""
    if filepath:
        file_location = f"Located in: {filepath}"

    # Extract folder structure for potential tag suggestions
    folders = []
    if filepath:
        path_parts = Path(filepath).parts
        if len(path_parts) > 1:
            folders = [
                part for part in path_parts[:-1] if not part.startswith((".", "_"))
            ]

    # Prepare content summary for the AI
    content_summary = extract_content_summary(file_content, 2500)

    try:
        # Create a detailed prompt for the OpenAI API
        prompt = f"""Analyze the following Markdown note and generate appropriate YAML front matter that's consistent with the provided YAML rules.

NOTE INFORMATION:
Filename: {filename}
{file_location}
Folder structure: {', '.join(folders) if folders else 'Root directory'}

EXISTING YAML (if any):
{existing_yaml}

YAML RULES:
{yaml_rules}

NOTE CONTENT:
{content_summary}

TASK:
Generate YAML front matter for this note following EXACTLY the rules provided.
If existing YAML is present, update and improve it according to the rules.
If there's no existing YAML, create new YAML following the rules.

IMPORTANT REQUIREMENTS:
1. Follow ALL the numbered rules provided in the YAML RULES section.
2. Use wikilinks with double brackets for most fields as specified in the rules.
3. Use the specified date format (YYYY-MM-DD) for all date fields.
4. Include ALL mandatory fields (title, date_created_at, type, tags).
5. DO NOT include any field that isn't relevant to the note's content.
6. Follow the exact formatting patterns shown in the examples.
7. Output ONLY the YAML content, without the triple-dash markers.
"""

        # Call the OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-4o",  # Use GPT-4 for best results
            messages=[
                {
                    "role": "system",
                    "content": "You are a specialized AI that generates YAML front matter for Obsidian Markdown notes. You strictly follow the conventions specified and only output the requested YAML content. You are an expert in Obsidian knowledge management and understand precisely how to structure metadata according to provided rules.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,  # Lower temperature for more consistent results
            max_tokens=600,  # Allow for longer YAML responses
        )

        # Extract the generated YAML content
        generated_yaml = response["choices"][0]["message"]["content"].strip()
        print(f"Successfully generated YAML for {filename} via OpenAI.")

        return generated_yaml

    except Exception as e:
        print(f"Error calling OpenAI API for {filename}: {e}", file=sys.stderr)

        # Fallback to basic YAML if API call fails
        fallback_yaml = f"""title:
  - {title}
date_created_at: {datetime.date.today().isoformat()}
type:
  - "[[Notes]]"
tags:
  - "#untagged"
"""
        print(f"Using fallback YAML for {filename}")
        return fallback_yaml


# --- Main Script Logic ---


def process_all_markdown_files(root_dir: str):
    """
    Scans a directory for ALL Markdown files and updates their YAML front matter.

    Args:
        root_dir (str): The root directory to scan (the Obsidian vault path).
    """
    files_modified = []
    files_skipped = []
    files_error = []

    abs_root_dir = os.path.abspath(root_dir)
    print(f"Scanning directory for Markdown files: {abs_root_dir}")

    if not os.path.isdir(abs_root_dir):
        print(f"Error: Directory not found: {abs_root_dir}", file=sys.stderr)
        return

    # Read the YAML rules once
    yaml_rules = read_yaml_rules()
    if not yaml_rules:
        print("Warning: YAML rules could not be loaded. Using default rules.")
        yaml_rules = "Use standard YAML formatting with wikilinks in double brackets and dates in YYYY-MM-DD format."

    # Exclude the script's own directory
    script_dir = os.path.abspath(os.path.dirname(__file__))

    # Find the rules file to exclude it from processing
    rules_file = os.path.join(abs_root_dir, "How to write YAML in Obsidian.md")
    rules_file_abs = os.path.abspath(rules_file)

    for subdir, _, files in os.walk(abs_root_dir):
        # Skip the script directory itself
        if os.path.abspath(subdir).startswith(script_dir):
            continue

        for filename in files:
            if filename.lower().endswith(".md"):
                filepath = os.path.join(subdir, filename)
                abs_filepath = os.path.abspath(filepath)

                # Skip the YAML rules file itself
                if abs_filepath == rules_file_abs:
                    print(f"Skipping YAML rules file: {filename}")
                    continue

                relative_path = os.path.relpath(filepath, abs_root_dir)

                print(f"Processing: {relative_path}")
                try:
                    # Extract existing YAML and main content
                    existing_yaml, main_content = extract_content_parts(filepath)

                    # Create a backup of the file
                    if not create_backup(filepath):
                        print(f"  -> Skipping {relative_path} (backup failed)")
                        files_skipped.append(relative_path)
                        continue

                    # Generate new YAML using AI
                    yaml_content = generate_yaml_with_ai(
                        main_content, filename, relative_path, existing_yaml, yaml_rules
                    )

                    if yaml_content:
                        # Create new file content with updated YAML
                        new_content = (
                            f"---\n{yaml_content.strip()}\n---\n\n{main_content}"
                        )

                        # Write back to the file
                        with open(filepath, "w", encoding="utf-8") as f:
                            f.write(new_content)
                        files_modified.append(relative_path)
                        print(f"  -> Updated YAML for {relative_path}")
                    else:
                        print(f"  -> Skipped {relative_path} (failed to generate YAML)")
                        files_skipped.append(relative_path)

                except Exception as e:
                    print(f"Error processing file {filepath}: {e}", file=sys.stderr)
                    files_error.append(relative_path)

    print("\n--- Update Complete ---")
    print(f"Files modified: {len(files_modified)}")
    if files_modified:
        for file in sorted(files_modified):
            print(f"- {file}")

    print(f"\nFiles skipped (YAML generation failed): {len(files_skipped)}")
    if files_skipped:
        for file in sorted(files_skipped):
            print(f"- {file}")

    print(f"\nFiles with errors during processing: {len(files_error)}")
    if files_error:
        for file in sorted(files_error):
            print(f"- {file}")
    print("-----------------------\n")


if __name__ == "__main__":
    # Determine vault root based on script location
    script_location = os.path.dirname(os.path.abspath(__file__))
    vault_root = os.path.dirname(
        os.path.dirname(script_location)
    )  # Assumes script is in VAULT_ROOT/99 - Meta/99 - Scripts/

    # Add a confirmation step before modifying files
    print(f"This script will scan '{vault_root}' and update YAML front matter")
    print(
        f"for ALL Markdown files using the rules from 'How to write YAML in Obsidian.md'."
    )
    print("It will create backups (.bak files) and then OVERWRITE the original files.")
    confirm = input("Are you sure you want to proceed? (yes/no): ")

    if confirm.lower() == "yes":
        process_all_markdown_files(vault_root)
    else:
        print("Operation cancelled.")
