#!/usr/bin/env python3
"""
Download all images from a webpage and save them to a ZIP file
Uses Selenium with Chrome to handle dynamic content
"""
import os
import sys
import time
import zipfile
import requests
from io import BytesIO
from urllib.parse import urljoin, urlparse
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def setup_chrome_driver(headless=True):
    """Setup Chrome driver with options"""
    chrome_options = Options()
    
    if headless:
        chrome_options.add_argument('--headless')
    
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    # Use Chrome from system PATH
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def get_all_image_urls(driver, url):
    """Extract all image URLs from the webpage"""
    print(f"Loading webpage: {url}")
    driver.get(url)
    
    # Wait for page to load
    time.sleep(3)
    
    # Scroll to load lazy images
    print("Scrolling to load all images...")
    last_height = driver.execute_script("return document.body.scrollHeight")
    
    for _ in range(5):  # Scroll 5 times
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
    
    # Find all image elements
    images = driver.find_elements(By.TAG_NAME, "img")
    
    image_urls = set()
    for img in images:
        src = img.get_attribute('src')
        if src and not src.startswith('data:'):
            # Convert relative URLs to absolute
            absolute_url = urljoin(url, src)
            image_urls.add(absolute_url)
    
    print(f"Found {len(image_urls)} unique images")
    return list(image_urls)

def download_image(url, session):
    """Download a single image"""
    try:
        response = session.get(url, timeout=30)
        response.raise_for_status()
        return response.content
    except Exception as e:
        print(f"  ✗ Failed to download {url}: {e}")
        return None

def sanitize_filename(url):
    """Create a safe filename from URL"""
    parsed = urlparse(url)
    filename = os.path.basename(parsed.path)
    
    # If no filename, generate one
    if not filename or '.' not in filename:
        filename = f"image_{abs(hash(url))}.jpg"
    
    # Remove invalid characters
    filename = "".join(c for c in filename if c.isalnum() or c in "._-")
    return filename

def download_images_to_zip(url, output_zip="webpage_images.zip"):
    """Main function to download all images and create ZIP"""
    print("=" * 70)
    print("Webpage Image Downloader")
    print("=" * 70)
    
    driver = None
    try:
        # Setup Chrome driver
        print("Starting Chrome browser...")
        driver = setup_chrome_driver(headless=True)
        
        # Get all image URLs
        image_urls = get_all_image_urls(driver, url)
        
        if not image_urls:
            print("No images found on the webpage!")
            return
        
        # Download images
        print(f"\nDownloading {len(image_urls)} images...")
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        downloaded_count = 0
        
        # Create ZIP file
        with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for idx, img_url in enumerate(image_urls, 1):
                print(f"[{idx}/{len(image_urls)}] Downloading {img_url[:60]}...", end=" ")
                
                image_data = download_image(img_url, session)
                
                if image_data:
                    # Generate filename
                    filename = sanitize_filename(img_url)
                    
                    # Ensure unique filename
                    base, ext = os.path.splitext(filename)
                    counter = 1
                    while filename in zipf.namelist():
                        filename = f"{base}_{counter}{ext}"
                        counter += 1
                    
                    # Add to ZIP
                    zipf.writestr(filename, image_data)
                    print(f"✓ ({len(image_data) // 1024} KB)")
                    downloaded_count += 1
                else:
                    print("✗ Failed")
                
                time.sleep(0.3)  # Be polite
        
        # Summary
        print("\n" + "=" * 70)
        print("Download Complete!")
        print("=" * 70)
        print(f"Successfully downloaded: {downloaded_count}/{len(image_urls)} images")
        print(f"ZIP file created: {os.path.abspath(output_zip)}")
        print(f"ZIP file size: {os.path.getsize(output_zip) / (1024*1024):.2f} MB")
        print("=" * 70)
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if driver:
            driver.quit()
            print("\nBrowser closed.")

def main():
    if len(sys.argv) < 2:
        print("Usage: python download_webpage_images.py <url> [output.zip]")
        print("\nExample:")
        print("  python download_webpage_images.py https://example.com/gallery")
        print("  python download_webpage_images.py https://example.com/gallery my_images.zip")
        sys.exit(1)
    
    url = sys.argv[1]
    output_zip = sys.argv[2] if len(sys.argv) > 2 else "webpage_images.zip"
    
    download_images_to_zip(url, output_zip)

if __name__ == "__main__":
    main()
