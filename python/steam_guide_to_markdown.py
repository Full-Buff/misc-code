#!/usr/bin/env python3
"""
Fixed Steam Guide Downloader with proper image processing
"""

import requests
from bs4 import BeautifulSoup
import argparse
import re
import os
import time
from pathlib import Path
from markdownify import markdownify as md
import yaml
from datetime import datetime
from urllib.parse import urlparse

class SteamGuideProcessor:
    def __init__(self, output_dir="./steam_guides", cdn_base_url=None, skip_ui_images=True):
        self.output_dir = Path(output_dir)
        self.cdn_base_url = cdn_base_url
        self.skip_ui_images = skip_ui_images
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # URLs patterns to skip when downloading UI images
        self.skip_patterns = [
            '/public/images/sharedfiles/4-star_large.png',
            '/public/images/sharedfiles/filterselect_blue.png',
            '/public/images/skin_1/footerLogo_valve.png',
            '/public/images/loyalty/reactions/',
            '/avatars.fastly.steamstatic.com/',
            # Add more specific patterns for Steam UI elements
        ]
        
        # Keep track of processed images for better mapping
        self.image_mapping = {}
    
    def sanitize_filename(self, filename):
        """Sanitize filename for filesystem compatibility"""
        filename = filename.replace(' ', '_')
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        filename = re.sub(r'_+', '_', filename).strip('_')
        return filename
    
    def should_skip_image(self, url):
        """Check if image should be skipped based on URL patterns"""
        if not self.skip_ui_images:
            return False
        
        for pattern in self.skip_patterns:
            if pattern in url:
                return True
        return False
    
    def download_page(self, url):
        """Download the Steam guide page"""
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract guide title early
            title_elem = soup.find('div', class_='workshopItemTitle')
            guide_title = title_elem.get_text().strip() if title_elem else "Untitled_Guide"
            
            return soup, guide_title
        
        except Exception as e:
            print(f"Error downloading page: {e}")
            return None, None
    
    def download_image(self, url, local_path, delay=0.5):
        """Download image with rate limiting"""
        try:
            time.sleep(delay)
            response = requests.get(url, headers=self.headers, stream=True)
            response.raise_for_status()
            
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
        except Exception as e:
            print(f"Error downloading image {url}: {e}")
            return False
    
    def process_images(self, soup, guide_name):
        """Download and process all images in the guide"""
        img_counter = 1
        images_dir = self.output_dir / guide_name / "images"
        
        # Process all images in the HTML
        for img in soup.find_all('img'):
            src = img.get('src')
            if not src:
                continue
            
            # Store original src for mapping
            original_src = src
            
            # Convert relative URLs to absolute
            if src.startswith('//'):
                src = 'https:' + src
            elif src.startswith('/'):
                src = 'https://steamcommunity.com' + src
            elif not src.startswith('http'):
                continue
            
            # Skip Steam UI images if enabled
            if self.should_skip_image(src):
                print(f"Skipping UI image: {src}")
                # Keep the original reference but don't download
                continue
            
            # Parse URL to extract clean path
            parsed_url = urlparse(src)
            
            # Get file extension from path (not from URL with query params)
            file_ext = os.path.splitext(parsed_url.path)[1]
            if not file_ext:
                file_ext = '.jpg'
            
            # Generate clean filename
            image_name = f"image_{img_counter:03d}{file_ext}"
            local_path = images_dir / image_name
            
            print(f"Downloading image {img_counter}: {src}")
            
            # Download image
            if self.download_image(src, local_path):
                # Store the mapping between original and new URLs
                self.image_mapping[original_src] = f"images/{image_name}"
                # Update src in soup
                if self.cdn_base_url:
                    img['src'] = f"{self.cdn_base_url}/{guide_name}/images/{image_name}"
                else:
                    img['src'] = f"images/{image_name}"
                img_counter += 1
            else:
                print(f"Failed to download image: {src}")
    
    def extract_metadata(self, soup, url):
        """Extract metadata from the guide"""
        metadata = {}
        
        # Title
        title_elem = soup.find('div', class_='workshopItemTitle')
        if title_elem:
            metadata['title'] = title_elem.get_text().strip()
        
        # Author
        author_elem = soup.select('.guideAuthors')
        if author_elem:
            metadata['author'] = author_elem[0].get_text().replace('By ', '').strip()
        
        # Description
        desc_elem = soup.select('.guideTopDescription')
        if desc_elem:
            metadata['description'] = desc_elem[0].get_text().strip()
        
        # Categories
        tag_elems = soup.select('.workshopTags a')
        if tag_elems:
            metadata['tags'] = [tag.get_text().strip() for tag in tag_elems]
        
        # Extract guide ID from URL
        guide_id_match = re.search(r'id=(\d+)', url)
        if guide_id_match:
            metadata['steam_guide_id'] = guide_id_match.group(1)
        
        metadata['source_url'] = url
        metadata['imported_date'] = datetime.now().isoformat()
        
        return metadata
    
    def clean_soup_for_conversion(self, soup):
        """Remove unnecessary elements before markdown conversion"""
        # Remove elements that shouldn't be in the guide content
        elements_to_remove = [
            {'id': 'global_header'},
            {'id': '-1'},
            {'class': 'responsive_header'},
            {'class': 'responsive_page_menu_ctn'},
            {'class': 'breadcrumbs'},
            {'class': 'apphub_HeaderTop'},
            {'class': 'apphub_sectionTabs'},
            {'class': 'rightContents'},
            {'class': 'sidebar'},
            {'class': 'footer'},
            {'id': 'footer'},
            {'class': 'workshopItemControls'},
            {'class': 'ratingSection'},
            {'class': 'workshopItemControlCtn'},
            {'id': 'ScrollingItemControls'},
        ]
        
        for element_spec in elements_to_remove:
            for element in soup.find_all('div', element_spec):
                element.decompose()
        
        return soup
    
    def convert_to_markdown(self, soup):
        """Convert HTML content to Markdown"""
        # Clean the soup before conversion
        soup = self.clean_soup_for_conversion(soup)
        
        # Find main content - prioritize the guide sections
        content_elem = soup.find('div', class_='guide subSections')
        if not content_elem:
            content_elem = soup.find('div', id='profileBlock')
        
        if content_elem:
            # Convert to markdown with better options
            markdown_content = md(
                str(content_elem), 
                heading_style="ATX",
                strip=['script', 'style'],
                convert_charrefs=True,
                escape_asterisks=False,
                escape_underscores=False
            )
            
            # Clean up markdown
            markdown_content = re.sub(r'\n\s*\n\s*\n', '\n\n', markdown_content)
            markdown_content = re.sub(r'<div[^>]*>|</div>', '', markdown_content)
            
            # Fix image references in markdown to use local paths
            for original_src, local_path in self.image_mapping.items():
                # Handle both direct links and markdown image syntax
                markdown_content = markdown_content.replace(original_src, local_path)
                
                # Also handle cases where the original src might be in markdown format
                escaped_original = re.escape(original_src)
                markdown_content = re.sub(
                    fr'!\[\]\({escaped_original}\)',
                    f'![](images/{os.path.basename(local_path)})',
                    markdown_content
                )
            
            # Remove empty links
            markdown_content = re.sub(r'\[]\([^)]*\)', '', markdown_content)
            
            return markdown_content
        return None
    
    def process_guide(self, url):
        """Process a single Steam guide"""
        print(f"Processing: {url}")
        
        # Download the page
        soup, guide_title = self.download_page(url)
        if not soup:
            return None
        
        # Sanitize guide name for filesystem
        guide_name = self.sanitize_filename(guide_title)
        guide_dir = self.output_dir / guide_name
        guide_dir.mkdir(parents=True, exist_ok=True)
        
        # Process images first (this modifies the soup)
        self.process_images(soup, guide_name)
        
        # Extract metadata
        metadata = self.extract_metadata(soup, url)
        
        # Convert to markdown
        markdown_content = self.convert_to_markdown(soup)
        if not markdown_content:
            print("Failed to convert content to markdown")
            return None
        
        # Create frontmatter
        frontmatter = '---\n' + yaml.dump(metadata, default_flow_style=False) + '---\n\n'
        
        # Combine frontmatter and content
        full_content = frontmatter + markdown_content
        
        # Save markdown file
        output_file = guide_dir / "index.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(full_content)
        
        print(f"Guide saved to: {output_file}")
        print(f"Images downloaded: {len(self.image_mapping)}")
        return output_file

def main():
    parser = argparse.ArgumentParser(description="Download and convert Steam guides to Markdown")
    parser.add_argument("url", help="Steam guide URL")
    parser.add_argument("--output", "-o", default="./steam_guides", help="Output directory")
    parser.add_argument("--cdn", help="CDN base URL for images")
    parser.add_argument("--include-ui", action="store_true", help="Include Steam UI images (default: skip them)")
    
    args = parser.parse_args()
    
    processor = SteamGuideProcessor(
        output_dir=args.output,
        cdn_base_url=args.cdn,
        skip_ui_images=not args.include_ui
    )
    
    result = processor.process_guide(args.url)
    
    if result:
        print(f"\nSuccess! Guide converted to: {result}")
    else:
        print("Failed to process guide")

if __name__ == "__main__":
    main()