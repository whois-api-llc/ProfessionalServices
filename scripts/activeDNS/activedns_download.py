#!/usr/bin/env python3
"""
WHOISXMLAPI.COM
Version 1.1, August, 2025
DNS Data Feed Downloader
Monitors WhoisXML API directory and downloads new files automatically.
"""

import os
import time
import json
import logging
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse
import requests
from requests.auth import HTTPBasicAuth
from bs4 import BeautifulSoup

class DNSDownloader:
    def __init__(self, base_url, download_dir="downloads", state_file="download_state.json", check_interval=600, username=None, password=None):
        """
        Initialize the DNS downloader.
        
        Args:
            base_url: The URL to monitor for files
            download_dir: Directory to save downloaded files
            state_file: JSON file to track download state
            check_interval: Check interval in seconds (default: 600 = 10 minutes)
            username: HTTP Basic Auth username
            password: HTTP Basic Auth password
        """
        self.base_url = base_url
        self.download_dir = Path(download_dir)
        self.state_file = Path(state_file)
        self.check_interval = check_interval
        
        # Setup HTTP Basic Auth if credentials provided
        self.auth = None
        if username and password:
            self.auth = HTTPBasicAuth(username, password)
            self.logger = logging.getLogger(__name__)
            self.logger.info("HTTP Basic Authentication configured")
        
        # Create download directory if it doesn't exist
        self.download_dir.mkdir(exist_ok=True)
        
        # Load or initialize state
        self.downloaded_files = self.load_state()
        
        # Setup logging
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('dns_downloader.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def load_state(self):
        """Load the download state from JSON file."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                self.logger.warning(f"Could not load state file: {e}. Starting fresh.")
        return {}
        
    def save_state(self):
        """Save the download state to JSON file."""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.downloaded_files, f, indent=2, default=str)
        except IOError as e:
            self.logger.error(f"Could not save state file: {e}")
            
    def get_file_list(self):
        """
        Scrape the directory listing and return a list of file URLs and metadata.
        
        Returns:
            List of dictionaries containing file information
        """
        try:
            response = requests.get(self.base_url, auth=self.auth, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            files = []
            
            # Look for links that appear to be files (not directories)
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                
                # Skip parent directory links and directories
                if href in ['../', '../'] or href.startswith('?') or href.endswith('/'):
                    continue
                    
                # Get file info from the row
                file_info = {
                    'name': href,
                    'url': urljoin(self.base_url, href),
                    'size': None,
                    'modified': None
                }
                
                # Try to extract size and date from the parent row
                parent_row = link.find_parent('tr')
                if parent_row:
                    cells = parent_row.find_all('td')
                    if len(cells) >= 3:
                        # Typically: name, date, size, description
                        try:
                            file_info['modified'] = cells[1].get_text(strip=True)
                            size_text = cells[2].get_text(strip=True)
                            if size_text and size_text != '-':
                                file_info['size'] = size_text
                        except IndexError:
                            pass
                
                files.append(file_info)
                
            self.logger.info(f"Found {len(files)} files on the server")
            return files
            
        except requests.RequestException as e:
            self.logger.error(f"Error fetching file list: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error parsing file list: {e}")
            return []
            
    def download_file(self, file_info):
        """
        Download a single file.
        
        Args:
            file_info: Dictionary containing file information
            
        Returns:
            bool: True if successful, False otherwise
        """
        file_name = file_info['name']
        file_url = file_info['url']
        local_path = self.download_dir / file_name
        
        try:
            # Record start time
            start_time = time.time()
            
            self.logger.info(f"Starting download: {file_name}")
            
            # Check if file already exists locally (additional safety check)
            if local_path.exists():
                self.logger.info(f"File {file_name} already exists locally, skipping download")
                return True
                
            # Download with streaming to handle large files
            response = requests.get(file_url, auth=self.auth, stream=True, timeout=60)
            response.raise_for_status()
            
            # Get total file size from headers
            total_size = int(response.headers.get('content-length', 0))
            
            with open(local_path, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
            # Calculate download time
            end_time = time.time()
            download_time = end_time - start_time
            
            # Format download time
            if download_time < 60:
                time_str = f"{download_time:.1f} seconds"
            else:
                minutes = int(download_time // 60)
                seconds = download_time % 60
                time_str = f"{minutes}m {seconds:.1f}s"
            
            self.logger.info(f"Download completed: {file_name} ({downloaded:,} bytes in {time_str})")
            return True
            
        except requests.RequestException as e:
            self.logger.error(f"Error downloading {file_name}: {e}")
            # Clean up partial download
            if local_path.exists():
                local_path.unlink()
            return False
        except IOError as e:
            self.logger.error(f"Error saving {file_name}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error downloading {file_name}: {e}")
            return False
            
    def check_and_download(self):
        """Check for new files and download them."""
        self.logger.info("Checking for new files...")
        
        files = self.get_file_list()
        if not files:
            self.logger.warning("No files found or error occurred")
            return
            
        new_files = []
        for file_info in files:
            file_name = file_info['name']
            
            # Check if file has been downloaded before
            if file_name not in self.downloaded_files:
                new_files.append(file_info)
                
        if not new_files:
            self.logger.info("No new files to download")
            return
            
        self.logger.info(f"Found {len(new_files)} new files to download")
        
        # Download new files
        for file_info in new_files:
            file_name = file_info['name']
            
            if self.download_file(file_info):
                # Mark as downloaded with timestamp and metadata
                self.downloaded_files[file_name] = {
                    'downloaded_at': datetime.now().isoformat(),
                    'url': file_info['url'],
                    'size': file_info.get('size'),
                    'modified': file_info.get('modified'),
                    'status': 'completed'
                }
                self.save_state()
                self.logger.info(f"Marked {file_name} as downloaded")
            else:
                self.logger.error(f"Failed to download {file_name}")
                
    def run(self):
        """Main execution loop."""
        self.logger.info(f"Starting DNS downloader monitoring {self.base_url}")
        self.logger.info(f"Check interval: {self.check_interval} seconds")
        self.logger.info(f"Download directory: {self.download_dir.absolute()}")
        self.logger.info(f"State file: {self.state_file.absolute()}")
        
        try:
            while True:
                try:
                    self.check_and_download()
                except Exception as e:
                    self.logger.error(f"Error during check and download cycle: {e}")
                    
                self.logger.info(f"Waiting {self.check_interval} seconds until next check...")
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal, shutting down...")
        except Exception as e:
            self.logger.error(f"Unexpected error in main loop: {e}")
            
    def show_status(self):
        """Show current download status."""
        print(f"\nDownload Status:")
        print(f"Downloaded files: {len(self.downloaded_files)}")
        print(f"Download directory: {self.download_dir.absolute()}")
        print(f"State file: {self.state_file.absolute()}")
        
        if self.downloaded_files:
            print("\nRecent downloads:")
            sorted_files = sorted(
                self.downloaded_files.items(),
                key=lambda x: x[1].get('downloaded_at', ''),
                reverse=True
            )
            for file_name, info in sorted_files[:10]:  # Show last 10
                downloaded_at = info.get('downloaded_at', 'Unknown')
                size = info.get('size', 'Unknown size')
                print(f"  {file_name} - {downloaded_at} ({size})")
                

def main():
    """Main function to run the downloader."""
    import argparse
    
    # Get API key from environment variable
    api_key = os.getenv('WXAAPIKEY')
    if not api_key or api_key.strip() == '':
        print("Error: WXAAPIKEY environment variable is required and cannot be blank")
        print("Please set it with one of these methods:")
        print("  Windows Command Prompt: set WXAAPIKEY=your_api_key")
        print("  Windows PowerShell:     $env:WXAAPIKEY=\"your_api_key\"")
        print("  Or use Windows Settings to set it permanently")
        print("\nFor example:")
        print("  set WXAAPIKEY=at_abcdefghijklmnopqrstuvwzyx")
        return 1
    
    print(f"✓ WXAAPIKEY environment variable found and configured")
    
    # Construct default URL with API key
    default_url = f'https://download.whoisxmlapi.com/datafeeds/Active_DNS/?apiKey={api_key}'
    
    parser = argparse.ArgumentParser(description='DNS Data Feed Downloader')
    parser.add_argument('--url', 
                       default=default_url,
                       help='URL to monitor for files')
    parser.add_argument('--download-dir', default='downloads',
                       help='Directory to save downloaded files')
    parser.add_argument('--state-file', default='download_state.json',
                       help='File to track download state')
    parser.add_argument('--interval', type=int, default=600,
                       help='Check interval in seconds (default: 600)')
    parser.add_argument('--status', action='store_true',
                       help='Show current status and exit')
    parser.add_argument('--check-once', action='store_true',
                       help='Check once and exit (no continuous monitoring)')
    
    args = parser.parse_args()
    
    downloader = DNSDownloader(
        base_url=args.url,
        download_dir=args.download_dir,
        state_file=args.state_file,
        check_interval=args.interval,
        username=api_key,
        password=api_key
    )
    
    if args.status:
        downloader.show_status()
    elif args.check_once:
        downloader.check_and_download()
    else:
        downloader.run()


if __name__ == "__main__":
    main()
