#!/usr/bin/env python3
import os
import sys
import json
import argparse

# Import configuration
from config import load_config, create_default_config
import zendesk_api

def validate_config(config, mode='backup'):
    """Validate required configuration values based on the operation mode"""
    valid = True
    
    # For backup mode, we need source credentials
    if mode in ['backup', 'both']:
        if not config['source']['zendesk_api_token']:
            print("ERROR: No source Zendesk API token provided.")
            print("Please set it in config.json source section or as ZENDESK_SOURCE_API_TOKEN environment variable.")
            valid = False
    
        if not config['source']['zendesk_user_email']:
            print("ERROR: No source Zendesk user email provided.")
            print("Please set it in config.json source section or as ZENDESK_SOURCE_USER_EMAIL environment variable.")
            valid = False
    
        if not config['source']['zendesk_subdomain']:
            print("ERROR: No source Zendesk subdomain provided.")
            print("Please set it in config.json source section or as ZENDESK_SOURCE_SUBDOMAIN environment variable.")
            valid = False
    
    # For restore mode, we need target credentials
    if mode in ['restore', 'both']:
        if not config['target']['zendesk_api_token']:
            print("ERROR: No target Zendesk API token provided.")
            print("Please set it in config.json target section or as ZENDESK_TARGET_API_TOKEN environment variable.")
            valid = False
    
        if not config['target']['zendesk_user_email']:
            print("ERROR: No target Zendesk user email provided.")
            print("Please set it in config.json target section or as ZENDESK_TARGET_USER_EMAIL environment variable.")
            valid = False
    
        if not config['target']['zendesk_subdomain']:
            print("ERROR: No target Zendesk subdomain provided.")
            print("Please set it in config.json target section or as ZENDESK_TARGET_SUBDOMAIN environment variable.")
            valid = False
        
    return valid

def setup_backup_path(config):
    """Create backup directory if it doesn't exist"""
    backup_path = os.path.join(config['backup_folder'], config['language'])
    if not os.path.exists(backup_path):
        os.makedirs(backup_path)
        print(f'Created backup path: {backup_path}')
    return backup_path

def get_article_ids_from_backup(backup_path):
    """Get all article IDs from backup directory"""
    return [int(file.split('.')[0]) for file in os.listdir(backup_path) if file.endswith('.html')]

def get_article_metadata(article_id, backup_path):
    """Get article metadata from backup"""
    metadata_file = os.path.join(backup_path, f'{article_id}.json')
    if os.path.exists(metadata_file):
        try:
            with open(metadata_file, 'r', encoding='utf-8') as file:
                return json.load(file)
        except Exception as e:
            print(f"Error reading metadata for article {article_id}: {str(e)}")
            return None
    else:
        print(f"No metadata file found for article {article_id}")
        return None

def backup_articles(config, backup_path):
    """Backup all articles from Zendesk"""
    # Set up authentication for source instance
    auth = (f"{config['source']['zendesk_user_email']}/token", config['source']['zendesk_api_token'])
    subdomain = config['source']['zendesk_subdomain']
    
    # First backup categories and sections structure
    print("Backing up categories and sections structure...")
    zendesk_api.backup_categories_and_sections(
        subdomain,
        auth,
        backup_path,
        config['language']
    )
    
    # Get all public article IDs
    article_ids = zendesk_api.get_public_article_ids(subdomain, auth)
    
    # Pull each article
    for article_id in article_ids:
        zendesk_api.pull_article(
            subdomain, 
            auth, 
            article_id, 
            backup_path, 
            config['language']
        )
    
    return article_ids

def restore_articles(config, backup_path, fail_fast=False):
    """Restore articles from backup to Zendesk"""
    # Set up authentication for target instance
    auth = (f"{config['target']['zendesk_user_email']}/token", config['target']['zendesk_api_token'])
    subdomain = config['target']['zendesk_subdomain']
    
    # Get IDs of articles to restore
    article_ids = get_article_ids_from_backup(backup_path)
    if not article_ids:
        print("No articles found to restore")
        return []
    
    print(f"Found {len(article_ids)} articles to restore")
    
    # First, try to restore the categories and sections structure
    print("Restoring categories and sections structure...")
    category_id_map, section_id_map = zendesk_api.restore_structure(
        subdomain,
        auth,
        backup_path,
        config['language']
    )
    print(f"Restored structure: {len(category_id_map)} categories and {len(section_id_map)} sections mapped")
    
    # Get valid IDs for restoring (these are used as fallbacks)
    valid_section_id = zendesk_api.get_valid_section_id(
        subdomain, 
        auth, 
        config['language'], 
        config['section_id']
    )
    valid_permission_group_id = zendesk_api.get_permission_groups(
        subdomain, 
        auth, 
        config['permission_group_id']
    )
    valid_user_segment_id = zendesk_api.get_user_segments(
        subdomain, 
        auth, 
        config['user_segment_id']
    )
    
    # Test restore with a single article if fail_fast is enabled
    if fail_fast and article_ids:
        print(f"Fail-fast enabled: Testing with a single article (ID: {article_ids[0]})...")
        try:
            test_article_id = article_ids[0]
            with open(os.path.join(backup_path, f'{test_article_id}.html'), mode='r', encoding='utf-8') as file:
                content = file.read()
            
            metadata = get_article_metadata(test_article_id, backup_path)
            if not metadata:
                print(f'ERROR: No metadata found for test article {test_article_id}')
                return []
            
            success = zendesk_api.restore_article(
                subdomain,
                auth,
                test_article_id,
                content,
                metadata,
                valid_section_id,
                valid_permission_group_id,
                valid_user_segment_id,
                config['language'],
                section_id_map
            )
            
            if not success:
                print(f"Test restore failed. Aborting.")
                return []
            
            article_ids = article_ids[1:]  # Remove the test article from the list
            restored_articles = [test_article_id]
            print(f"Test restore succeeded. Continuing with remaining {len(article_ids)} articles...")
        except Exception as e:
            print(f'ERROR: Test restore failed: {str(e)}')
            return []
    else:
        restored_articles = []
    
    # Restore each article
    for article_id in article_ids:
        try:
            # Read the backed up content
            with open(os.path.join(backup_path, f'{article_id}.html'), mode='r', encoding='utf-8') as file:
                content = file.read()
                
            # Get article metadata
            metadata = get_article_metadata(article_id, backup_path)
            if not metadata:
                print(f'No metadata found for article {article_id}, skipping')
                if fail_fast:
                    print("Fail-fast enabled: Stopping due to missing metadata")
                    break
                continue
                
            # Restore the article
            success = zendesk_api.restore_article(
                subdomain,
                auth,
                article_id,
                content,
                metadata,
                valid_section_id,
                valid_permission_group_id,
                valid_user_segment_id,
                config['language'],
                section_id_map
            )
            
            if success:
                restored_articles.append(article_id)
            elif fail_fast:
                print("Fail-fast enabled: Stopping due to restore failure")
                break
                
        except Exception as e:
            print(f'Failed to restore article {article_id}: {str(e)}')
            if fail_fast:
                print("Fail-fast enabled: Stopping due to exception")
                break
    
    return restored_articles

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Zendesk article backup and restore tool')
    parser.add_argument('--mode', choices=['backup', 'restore', 'both'], default='backup',
                        help='Operation mode: backup, restore, or both (default: backup)')
    parser.add_argument('--fail-fast', action='store_true', 
                        help='Stop on first error during restore')
    return parser.parse_args()

if __name__ == "__main__":
    # Create default config file if it doesn't exist
    create_default_config()
    
    # Parse arguments first to check for help
    if '--help' in sys.argv or '-h' in sys.argv:
        parse_args()  # This will display help and exit
        sys.exit(0)
    
    # Load configuration
    config = load_config()
    
    # Normal argument parsing
    args = parse_args()
    
    # Validate configuration based on mode
    if not validate_config(config, args.mode):
        sys.exit(1)
    
    # Set up backup path
    backup_path = setup_backup_path(config)
    
    # Perform requested operations
    if args.mode in ['backup', 'both']:
        print("===== BACKUP MODE =====")
        article_ids = backup_articles(config, backup_path)
        print(f"Backed up {len(article_ids)} articles to {backup_path}")
    
    if args.mode in ['restore', 'both']:
        print("\n===== RESTORE MODE =====")
        restored_articles = restore_articles(config, backup_path, fail_fast=args.fail_fast)
        print(f"Restored {len(restored_articles)} articles")