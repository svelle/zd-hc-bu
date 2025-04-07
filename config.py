import os
import json

CONFIG_FILE = 'config.json'

# Default configuration with empty values
DEFAULT_CONFIG = {
    # Source (backup from) instance configuration
    'source': {
        'zendesk_api_token': '',
        'zendesk_user_email': '',
        'zendesk_subdomain': ''
    },
    # Target (restore to) instance configuration - defaults to same as source if not specified
    'target': {
        'zendesk_api_token': '',
        'zendesk_user_email': '',
        'zendesk_subdomain': ''
    },
    # Common configuration
    'backup_folder': 'backup',
    'language': 'en-us',
    'section_id': None,
    'permission_group_id': None,
    'user_segment_id': None
}

def load_config():
    """Load configuration from file, fall back to environment variables or defaults"""
    config = DEFAULT_CONFIG.copy()
    
    # Try to load from config file
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                file_config = json.load(f)
                
                # Handle both new and old config format
                if 'source' in file_config:
                    # New format with separate source and target
                    config.update(file_config)
                else:
                    # Old format with single set of credentials
                    # Migrate to new format
                    source = {
                        'zendesk_api_token': file_config.get('zendesk_api_token', ''),
                        'zendesk_user_email': file_config.get('zendesk_user_email', ''),
                        'zendesk_subdomain': file_config.get('zendesk_subdomain', '')
                    }
                    
                    # Update source config
                    config['source'] = source
                    
                    # If target isn't specified, use same as source
                    if 'target' not in file_config:
                        config['target'] = source.copy()
                    
                    # Update other common configs
                    for key in file_config:
                        if key not in ['zendesk_api_token', 'zendesk_user_email', 'zendesk_subdomain']:
                            config[key] = file_config[key]
                
                print(f"Loaded configuration from {CONFIG_FILE}")
        except Exception as e:
            print(f"Error loading config file: {str(e)}")
    
    # Override with environment variables if present
    # Source credentials from environment
    if os.getenv('ZENDESK_SOURCE_API_TOKEN'):
        config['source']['zendesk_api_token'] = os.getenv('ZENDESK_SOURCE_API_TOKEN')
    elif os.getenv('ZENDESK_API_TOKEN'):  # Fallback to generic env var
        config['source']['zendesk_api_token'] = os.getenv('ZENDESK_API_TOKEN')
    
    if os.getenv('ZENDESK_SOURCE_USER_EMAIL'):
        config['source']['zendesk_user_email'] = os.getenv('ZENDESK_SOURCE_USER_EMAIL')
    elif os.getenv('ZENDESK_USER_EMAIL'):  # Fallback to generic env var
        config['source']['zendesk_user_email'] = os.getenv('ZENDESK_USER_EMAIL')
    
    if os.getenv('ZENDESK_SOURCE_SUBDOMAIN'):
        config['source']['zendesk_subdomain'] = os.getenv('ZENDESK_SOURCE_SUBDOMAIN')
    elif os.getenv('ZENDESK_SUBDOMAIN'):  # Fallback to generic env var
        config['source']['zendesk_subdomain'] = os.getenv('ZENDESK_SUBDOMAIN')
    
    # Target credentials from environment
    if os.getenv('ZENDESK_TARGET_API_TOKEN'):
        config['target']['zendesk_api_token'] = os.getenv('ZENDESK_TARGET_API_TOKEN')
    elif os.getenv('ZENDESK_API_TOKEN') and not config['target']['zendesk_api_token']:
        config['target']['zendesk_api_token'] = os.getenv('ZENDESK_API_TOKEN')
    
    if os.getenv('ZENDESK_TARGET_USER_EMAIL'):
        config['target']['zendesk_user_email'] = os.getenv('ZENDESK_TARGET_USER_EMAIL')
    elif os.getenv('ZENDESK_USER_EMAIL') and not config['target']['zendesk_user_email']:
        config['target']['zendesk_user_email'] = os.getenv('ZENDESK_USER_EMAIL')
    
    if os.getenv('ZENDESK_TARGET_SUBDOMAIN'):
        config['target']['zendesk_subdomain'] = os.getenv('ZENDESK_TARGET_SUBDOMAIN')
    elif os.getenv('ZENDESK_SUBDOMAIN') and not config['target']['zendesk_subdomain']:
        config['target']['zendesk_subdomain'] = os.getenv('ZENDESK_SUBDOMAIN')
    
    # If target is empty, use source as default
    if not config['target']['zendesk_api_token']:
        config['target']['zendesk_api_token'] = config['source']['zendesk_api_token']
    
    if not config['target']['zendesk_user_email']:
        config['target']['zendesk_user_email'] = config['source']['zendesk_user_email']
    
    if not config['target']['zendesk_subdomain']:
        config['target']['zendesk_subdomain'] = config['source']['zendesk_subdomain']
    
    return config

def create_default_config():
    """Create a default config file if none exists"""
    if not os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(DEFAULT_CONFIG, f, indent=2)
                print(f"Created default config file at {CONFIG_FILE}")
                print("Please edit this file to add your Zendesk API credentials")
        except Exception as e:
            print(f"Error creating default config file: {str(e)}")