# Zendesk Article Backup Tool

A utility for backing up and restoring Zendesk help center articles.

## Features

- Backup all public articles from a Zendesk Help Center
- Store article content, metadata, and structure separately
- Restore articles to the same or different Zendesk instance
- Preserves original category and section structure
- Compatible with both Help Center API and Guide API

## Setup

1. Create a Python virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```
   pip install requests
   ```

3. Configure the tool:
   ```
   cp config.json.template config.json
   ```
   
4. Edit `config.json` to add your Zendesk credentials:
   - Source instance (for backup):
     - `source.zendesk_api_token`: Your source Zendesk API token
     - `source.zendesk_user_email`: Your source Zendesk email address
     - `source.zendesk_subdomain`: Your source Zendesk subdomain URL
   - Target instance (for restore, can be the same as source):
     - `target.zendesk_api_token`: Your target Zendesk API token
     - `target.zendesk_user_email`: Your target Zendesk email address
     - `target.zendesk_subdomain`: Your target Zendesk subdomain URL
   - Other configuration options as needed

## Usage

### Backing up articles

```
python backup.py
```

This will create backup files in the configured backup folder, including:
- HTML content for each article
- JSON metadata for each article
- JSON files containing category and section structure information

### Restoring articles

To restore articles from backups:

```
python backup.py --mode restore
```

This will restore the entire knowledge base structure (categories, sections, and articles) to the target instance.

### Running both backup and restore

To run both operations in sequence:

```
python backup.py --mode both
```

### Debugging with fail-fast

To stop on first error during restore (helpful for debugging):

```
python backup.py --mode restore --fail-fast
```

## Configuration

You can configure the tool in three ways (in order of precedence):

1. Environment variables:
   - For source instance:
     - `ZENDESK_SOURCE_API_TOKEN`
     - `ZENDESK_SOURCE_USER_EMAIL`
     - `ZENDESK_SOURCE_SUBDOMAIN`
   - For target instance:
     - `ZENDESK_TARGET_API_TOKEN`
     - `ZENDESK_TARGET_USER_EMAIL`
     - `ZENDESK_TARGET_SUBDOMAIN`
   - Legacy (will be used for both source and target if specific variables aren't set):
     - `ZENDESK_API_TOKEN`
     - `ZENDESK_USER_EMAIL`
     - `ZENDESK_SUBDOMAIN`

2. Configuration file (`config.json`)

3. Default values in the code

## Backup Structure

The backup is organized as follows:

- `<backup_folder>/<language>/` - Root of the backup
  - `<article_id>.html` - Article content
  - `<article_id>.json` - Article metadata
  - `structure/` - Knowledge base structure
    - `categories.json` - Categories data
    - `sections.json` - Sections data