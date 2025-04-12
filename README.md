# ObsidianScripts

A collection of utility scripts for managing Obsidian vaults. These scripts automate common maintenance tasks, help with note organization, and can simplify vault management.

## Scripts

- **add_yaml_to_files_without_yaml.py**: Generates/updates YAML front matter for Markdown files using OpenAI to analyze content.
- **clean_done_tags_vault.py**: Removes all #done tags from notes (with or without datetime information).
- **convert_tags_to_wikilinks.py**: Converts specific tags to wikilinks throughout a vault.
- **duplicate_note_finder.py**: Identifies markdown notes with identical filenames across different folders.
- **find_missing_yaml.py**: Scans vault for Markdown files without YAML front matter.
- **fix_daily_navigation.py**: Repairs broken navigation links in daily notes.
- **migrate_noteplan_calendar_notes.py**: Migrates calendar notes from NotePlan to Obsidian with proper formatting.
- **organize_obsidian_attachments.py**: Organizes attachment files into folders by type (audio, images, documents, videos).
- **remove_backup_files.py**: Cleans up backup (.bak) files in a vault.
- **simplify_wikilinks.py**: Converts full-path wikilinks to simple note name wikilinks (e.g., [[folder/note]] → [[note]]).
- **tag_inventory.py**: Creates an inventory of all unique tags, sorted by frequency of use.

## Usage

Each script includes detailed documentation within its header. Scripts can be run directly from the command line:

```bash
python script_name.py [options]
```

Most scripts support a `--dry-run` option to preview changes without modifying files.

## Note

These scripts were created for personal use but may be helpful to other Obsidian users. Always back up your vault before running scripts that modify files.