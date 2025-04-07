import os
import requests
from bs4 import BeautifulSoup

def normalize_url(url):
    """Remove trailing slashes from URLs"""
    if url and url.endswith('/'):
        return url.rstrip('/')
    return url

def get_valid_section_id(zendesk_subdomain, auth, language, section_id):
    """Get a valid section ID from the Zendesk API"""
    # Normalize the subdomain URL
    zendesk_subdomain = normalize_url(zendesk_subdomain)
    
    url = f'{zendesk_subdomain}/api/v2/help_center/{language}/sections.json'
    headers = {
        "Content-Type": "application/json",
    }
    
    try:
        response = requests.get(url, auth=auth, headers=headers)
        if response.status_code == 200:
            sections = response.json().get('sections', [])
            if sections:
                # Return the ID of the first section found
                first_section = sections[0]
                print(f"Using section: {first_section['name']} (ID: {first_section['id']})")
                return first_section['id']
        
        # If that fails, try alternative endpoint
        url = f'{zendesk_subdomain}/api/v2/guide/sections.json'
        response = requests.get(url, auth=auth, headers=headers)
        if response.status_code == 200:
            sections = response.json().get('sections', [])
            if sections:
                first_section = sections[0]
                print(f"Using section from Guide API: {first_section['name']} (ID: {first_section['id']})")
                return first_section['id']
                
        print("No sections found. Will use general articles endpoint.")
        return section_id  # Use the default section ID
    except Exception as e:
        print(f"Error fetching sections: {str(e)}")
        return section_id  # Use the default section ID

def get_permission_groups(zendesk_subdomain, auth, default_permission_group_id):
    """Get permission group IDs from the Zendesk API"""
    # Normalize the subdomain URL
    zendesk_subdomain = normalize_url(zendesk_subdomain)
    
    # First try standard API endpoint
    url = f'{zendesk_subdomain}/api/v2/help_center/permission_groups.json'
    headers = {
        "Content-Type": "application/json",
    }
    
    try:
        response = requests.get(url, auth=auth, headers=headers)
        if response.status_code == 200:
            groups = response.json().get('permission_groups', [])
            if groups:
                # Print all available permission groups
                print("Available permission groups:")
                for group in groups:
                    print(f"  - {group['name']} (ID: {group['id']})")
                # Use the first group by default
                return groups[0]['id']
        
        # If that fails, try Guide-specific endpoint
        url = f'{zendesk_subdomain}/api/v2/guide/permission_groups.json'
        response = requests.get(url, auth=auth, headers=headers)
        if response.status_code == 200:
            groups = response.json().get('permission_groups', [])
            if groups:
                print("Available permission groups from Guide API:")
                for group in groups:
                    print(f"  - {group['name']} (ID: {group['id']})")
                return groups[0]['id']
        
        print(f"Failed to fetch permission groups. Using default ID: {default_permission_group_id}")
        return default_permission_group_id
    except Exception as e:
        print(f"Error fetching permission groups: {str(e)}")
        return default_permission_group_id

def get_user_segments(zendesk_subdomain, auth, default_user_segment_id):
    """Get user segment IDs from the Zendesk API"""
    # Normalize the subdomain URL
    zendesk_subdomain = normalize_url(zendesk_subdomain)
    
    # First try standard API endpoint
    url = f'{zendesk_subdomain}/api/v2/help_center/user_segments.json'
    headers = {
        "Content-Type": "application/json",
    }
    
    try:
        response = requests.get(url, auth=auth, headers=headers)
        if response.status_code == 200:
            segments = response.json().get('user_segments', [])
            if segments:
                # Print all available user segments
                print("Available user segments:")
                for segment in segments:
                    print(f"  - {segment['name']} (ID: {segment['id']})")
                # Find "Everyone" segment or use the first one
                for segment in segments:
                    if segment['name'].lower() in ['everyone', 'all', 'signed-in users']:
                        return segment['id']
                return segments[0]['id']
        
        # If that fails, try Guide-specific endpoint
        url = f'{zendesk_subdomain}/api/v2/guide/user_segments.json'
        response = requests.get(url, auth=auth, headers=headers)
        if response.status_code == 200:
            segments = response.json().get('user_segments', [])
            if segments:
                print("Available user segments from Guide API:")
                for segment in segments:
                    print(f"  - {segment['name']} (ID: {segment['id']})")
                # Find "Everyone" segment or use the first one
                for segment in segments:
                    if segment['name'].lower() in ['everyone', 'all', 'signed-in users']:
                        return segment['id']
                return segments[0]['id']
                
        print("No user segments found or API access denied. Using default NULL value.")
        return default_user_segment_id
    except Exception as e:
        print(f"Error fetching user segments: {str(e)}")
        return default_user_segment_id

def backup_categories_and_sections(zendesk_subdomain, auth, backup_path, language):
    """Backup categories and sections data"""
    # Normalize the subdomain URL
    zendesk_subdomain = normalize_url(zendesk_subdomain)
    
    # Create structure backup directory
    structure_path = os.path.join(backup_path, 'structure')
    if not os.path.exists(structure_path):
        os.makedirs(structure_path)
        
    # Get all categories
    categories_url = f'{zendesk_subdomain}/api/v2/help_center/{language}/categories.json'
    headers = {"Content-Type": "application/json"}
    
    categories = []
    try:
        response = requests.get(categories_url, auth=auth, headers=headers)
        if response.status_code == 200:
            categories_data = response.json().get('categories', [])
            categories = categories_data
            
            # Save categories to file
            with open(os.path.join(structure_path, 'categories.json'), 'w', encoding='utf-8') as f:
                import json
                json.dump(categories_data, f, indent=2)
                
            print(f"Backed up {len(categories_data)} categories")
    except Exception as e:
        print(f"Error backing up categories: {str(e)}")
    
    # Get all sections for each category
    sections = []
    for category in categories:
        try:
            sections_url = f'{zendesk_subdomain}/api/v2/help_center/{language}/categories/{category["id"]}/sections.json'
            response = requests.get(sections_url, auth=auth, headers=headers)
            
            if response.status_code == 200:
                sections_data = response.json().get('sections', [])
                sections.extend(sections_data)
        except Exception as e:
            print(f"Error fetching sections for category {category['id']}: {str(e)}")
    
    # Also get sections without categories
    try:
        all_sections_url = f'{zendesk_subdomain}/api/v2/help_center/{language}/sections.json' 
        response = requests.get(all_sections_url, auth=auth, headers=headers)
        
        if response.status_code == 200:
            all_sections = response.json().get('sections', [])
            
            # Add any sections not already in our list
            existing_ids = {section['id'] for section in sections}
            for section in all_sections:
                if section['id'] not in existing_ids:
                    sections.append(section)
    except Exception as e:
        print(f"Error fetching all sections: {str(e)}")
    
    # Save sections to file
    with open(os.path.join(structure_path, 'sections.json'), 'w', encoding='utf-8') as f:
        import json
        json.dump(sections, f, indent=2)
        
    print(f"Backed up {len(sections)} sections")
    return categories, sections

def get_public_article_ids(zendesk_subdomain, auth):
    """Get all public article IDs from the Zendesk API"""
    # Normalize the subdomain URL
    zendesk_subdomain = normalize_url(zendesk_subdomain)
    
    # Try standard endpoint
    url = f'{zendesk_subdomain}/api/v2/help_center/articles.json'
    headers = {
        "Content-Type": "application/json",
    }
    all_article_ids = []
    
    try:
        while url:
            response = requests.get(url, auth=auth, headers=headers)
            if response.status_code == 200:
                data = response.json()
                articles = data['articles']
                all_article_ids.extend([article['id'] for article in articles if article['draft'] is False])
                
                # Check if there's a next page
                url = data.get('next_page')
            else:
                print('Failed to fetch articles with error {}, {}'.format(response.status_code, response.text))
                break
    
        # If we didn't get any articles, try the Guide API endpoint
        if not all_article_ids:
            url = f'{zendesk_subdomain}/api/v2/guide/articles.json'
            while url:
                response = requests.get(url, auth=auth, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    articles = data['articles']
                    all_article_ids.extend([article['id'] for article in articles if article['draft'] is False])
                    
                    # Check if there's a next page
                    url = data.get('next_page')
                else:
                    print('Failed to fetch articles from Guide API with error {}, {}'.format(response.status_code, response.text))
                    break
    except Exception as e:
        print(f"Error fetching articles: {str(e)}")
    
    print(f'Found {len(all_article_ids)} public articles')
    return all_article_ids

def pull_article(zendesk_subdomain, auth, article_id, backup_path, language):
    """Pull a single article from the Zendesk API"""
    # Normalize the subdomain URL
    zendesk_subdomain = normalize_url(zendesk_subdomain)
    
    # Try standard endpoint
    url = f'{zendesk_subdomain}/api/v2/help_center/articles/{article_id}.json'
    headers = {
        "Content-Type": "application/json",
    }
    
    try:
        response = requests.get(url, auth=auth, headers=headers)
        
        # If that fails, try Guide API
        if response.status_code != 200:
            url = f'{zendesk_subdomain}/api/v2/guide/articles/{article_id}.json'
            response = requests.get(url, auth=auth, headers=headers)
        
        if response.status_code == 200:
            article = response.json()['article']
            
            # Store the HTML body content
            with open(os.path.join(backup_path, f'{article_id}.html'), mode='w', encoding='utf-8') as file:
                file.write(article['body'])
            
            # Store the metadata in a separate JSON file
            metadata = {
                'title': article.get('title', f'Article {article_id}'),
                'section_id': article.get('section_id'),
                'user_segment_id': article.get('user_segment_id'),
                'permission_group_id': article.get('permission_group_id'),
                'locale': article.get('locale', language)
            }
            
            with open(os.path.join(backup_path, f'{article_id}.json'), mode='w', encoding='utf-8') as file:
                import json
                json.dump(metadata, file, indent=2)
            
            print(f'Article {article_id} pulled with metadata')
            return True
        else:
            print('Failed to fetch article {} with error {}, {}'.format(article_id, response.status_code, response.text))
            return False
    except Exception as e:
        print(f'Error fetching article {article_id}: {str(e)}')
        return False

def restore_structure(zendesk_subdomain, auth, backup_path, language):
    """Restore categories and sections structure from backup"""
    # Normalize the subdomain URL
    zendesk_subdomain = normalize_url(zendesk_subdomain)
    
    # Load backup data
    structure_path = os.path.join(backup_path, 'structure')
    if not os.path.exists(structure_path):
        print("No structure backup found to restore")
        return {}, {}
    
    # Authentication headers
    headers = {
        "Content-Type": "application/json",
    }
    
    # Dictionary to map old IDs to new IDs
    category_id_map = {}
    section_id_map = {}
    
    # Restore categories first
    categories_file = os.path.join(structure_path, 'categories.json')
    if os.path.exists(categories_file):
        try:
            with open(categories_file, 'r', encoding='utf-8') as f:
                import json
                categories = json.load(f)
                
            print(f"Found {len(categories)} categories to restore")
            
            # Get existing categories to avoid duplicates
            existing_categories = []
            existing_url = f'{zendesk_subdomain}/api/v2/help_center/{language}/categories.json'
            response = requests.get(existing_url, auth=auth, headers=headers)
            if response.status_code == 200:
                existing_categories = response.json().get('categories', [])
                print(f"Found {len(existing_categories)} existing categories")
            
            # Create categories
            for category in categories:
                old_id = category['id']
                category_name = category['name']
                
                # Check if similar category already exists
                category_exists = False
                for existing in existing_categories:
                    if existing['name'].lower() == category_name.lower():
                        print(f"Category '{category_name}' already exists, using ID: {existing['id']}")
                        category_id_map[old_id] = existing['id']
                        category_exists = True
                        break
                
                if not category_exists:
                    # Create new category
                    create_url = f'{zendesk_subdomain}/api/v2/help_center/{language}/categories.json'
                    payload = {
                        'category': {
                            'name': category_name,
                            'description': category.get('description', ''),
                            'locale': language
                        }
                    }
                    
                    response = requests.post(create_url, auth=auth, headers=headers, json=payload)
                    
                    if response.status_code in [200, 201]:
                        new_category = response.json().get('category', {})
                        new_id = new_category.get('id')
                        category_id_map[old_id] = new_id
                        print(f"Created category '{category_name}' with ID: {new_id}")
                    else:
                        print(f"Failed to create category '{category_name}': {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Error restoring categories: {str(e)}")
    
    # Restore sections
    sections_file = os.path.join(structure_path, 'sections.json')
    if os.path.exists(sections_file):
        try:
            with open(sections_file, 'r', encoding='utf-8') as f:
                import json
                sections = json.load(f)
                
            print(f"Found {len(sections)} sections to restore")
            
            # Get existing sections to avoid duplicates
            existing_sections = []
            existing_url = f'{zendesk_subdomain}/api/v2/help_center/{language}/sections.json'
            response = requests.get(existing_url, auth=auth, headers=headers)
            if response.status_code == 200:
                existing_sections = response.json().get('sections', [])
                print(f"Found {len(existing_sections)} existing sections")
            
            # Create sections
            for section in sections:
                old_id = section['id']
                section_name = section['name']
                old_category_id = section.get('category_id')
                
                # See if we have a new mapped category ID
                new_category_id = None
                if old_category_id in category_id_map:
                    new_category_id = category_id_map[old_category_id]
                elif existing_categories and len(existing_categories) > 0:
                    new_category_id = existing_categories[0]['id']
                    print(f"Using first available category ID {new_category_id} for section '{section_name}'")
                
                # Check if similar section already exists
                section_exists = False
                for existing in existing_sections:
                    if existing['name'].lower() == section_name.lower():
                        print(f"Section '{section_name}' already exists, using ID: {existing['id']}")
                        section_id_map[old_id] = existing['id']
                        section_exists = True
                        break
                
                if not section_exists:
                    # Only create if we have a valid category
                    if new_category_id:
                        # Create new section
                        create_url = f'{zendesk_subdomain}/api/v2/help_center/{language}/categories/{new_category_id}/sections.json'
                        payload = {
                            'section': {
                                'name': section_name,
                                'description': section.get('description', ''),
                                'locale': language
                            }
                        }
                        
                        response = requests.post(create_url, auth=auth, headers=headers, json=payload)
                        
                        if response.status_code in [200, 201]:
                            new_section = response.json().get('section', {})
                            new_id = new_section.get('id')
                            section_id_map[old_id] = new_id
                            print(f"Created section '{section_name}' with ID: {new_id}")
                        else:
                            print(f"Failed to create section '{section_name}': {response.status_code} - {response.text}")
                    else:
                        print(f"No valid category found for section '{section_name}', skipping")
        except Exception as e:
            print(f"Error restoring sections: {str(e)}")
    
    return category_id_map, section_id_map

def restore_article(zendesk_subdomain, auth, article_id, content, metadata, valid_section_id, valid_permission_group_id, valid_user_segment_id, language, section_id_map=None):
    """Restore a single article to the Zendesk API"""
    # Normalize the subdomain URL
    zendesk_subdomain = normalize_url(zendesk_subdomain)
    
    # Authentication headers
    headers = {
        "Content-Type": "application/json",
    }
    
    # Try to use original section ID from metadata if we have a mapping for it
    section_id = metadata.get('section_id')
    if section_id_map and section_id in section_id_map:
        section_id = section_id_map[section_id]  # Use mapped section ID
        print(f"Using mapped section ID {section_id} for article {article_id}")
    else:
        section_id = valid_section_id  # Fallback to any valid section
    
    # Validate section_id - this is required
    if not section_id:
        print(f"Cannot create article {article_id} - no valid section found")
        return False
        
    # Get other metadata
    title = metadata.get('title', f'Article {article_id}')
    article_locale = metadata.get('locale', language)
    
    # Use valid values for permission and segment
    permission_group_id = valid_permission_group_id
    user_segment_id = valid_user_segment_id
        
    # Prepare payload - for both update and create operations
    article_payload = {
        'title': title,
        'body': content,
        'locale': article_locale,
        'draft': False,  # Ensure article is not in draft
        'promoted': True  # Make it promoted for visibility
    }
    
    if permission_group_id is not None:
        article_payload['permission_group_id'] = permission_group_id
        
    if user_segment_id is not None:
        article_payload['user_segment_id'] = user_segment_id
    
    # First, try to check if the article exists
    check_url = f'{zendesk_subdomain}/api/v2/help_center/articles/{article_id}.json'
    
    try:
        check_response = requests.get(check_url, auth=auth, headers=headers)
        article_exists = check_response.status_code == 200
        
        if not article_exists:
            # Try Guide API format
            check_url = f'{zendesk_subdomain}/api/v2/guide/articles/{article_id}.json'
            check_response = requests.get(check_url, auth=auth, headers=headers)
            article_exists = check_response.status_code == 200
        
        if article_exists:
            # Update existing article
            print(f"Article {article_id} exists, updating...")
            
            # Try regular update endpoint
            update_url = f'{zendesk_subdomain}/api/v2/help_center/articles/{article_id}.json'
            update_payload = {'article': article_payload}
            response = requests.put(update_url, auth=auth, headers=headers, json=update_payload)
            
            if response.status_code != 200:
                # Try Guide API format
                update_url = f'{zendesk_subdomain}/api/v2/guide/articles/{article_id}.json'
                response = requests.put(update_url, auth=auth, headers=headers, json=update_payload)
            
            if response.status_code == 200:
                print(f'Successfully updated article {article_id}')
                return True
            else:
                print(f'Failed to update article {article_id}: {response.status_code} - {response.text}')
                return False
        else:
            # Create new article with valid section ID
            print(f"Article {article_id} not found, creating new in section ID {section_id}...")
            
            # Try creation with valid section ID from target system
            create_url = f'{zendesk_subdomain}/api/v2/help_center/{article_locale}/sections/{section_id}/articles.json'
            create_payload = {
                'article': article_payload,
                'notify_subscribers': False
            }
            
            response = requests.post(create_url, auth=auth, headers=headers, json=create_payload)
            
            if response.status_code in [200, 201]:
                print(f'Successfully created article {article_id}')
                return True
            else:
                print(f'Failed to create article: {response.status_code} - {response.text}')
                
                # Try Guide API endpoint
                create_url = f'{zendesk_subdomain}/api/v2/guide/sections/{section_id}/articles.json'
                response = requests.post(create_url, auth=auth, headers=headers, json=create_payload)
                
                if response.status_code in [200, 201]:
                    print(f'Successfully created article {article_id} via Guide API')
                    return True
                else:
                    print(f'Failed to create via Guide API: {response.status_code} - {response.text}')
                    print(f'Could not restore article {article_id}')
                    return False
    except Exception as e:
        print(f'Error processing article {article_id}: {str(e)}')
        return False