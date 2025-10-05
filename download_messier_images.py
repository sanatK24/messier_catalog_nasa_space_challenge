#!/usr/bin/env python3
"""
Download all 110 Messier object images from AstroPixels website
"""
import os
import sys
import time
import requests
from urllib.parse import urljoin
from pathlib import Path

# Base URL for the images
BASE_URL = "http://www.astropixels.com/"

# Messier object image paths based on the HTML structure
MESSIER_IMAGES = {
    # Supernova Remnants
    "M1": "supernovae/M1-01.jpg",
    
    # Globular Clusters
    "M2": "globularclusters/M2-01.jpg",
    "M3": "globularclusters/M3-01.jpg",
    "M4": "globularclusters/M4-01.jpg",
    "M5": "globularclusters/M5-01.jpg",
    "M9": "globularclusters/M9-01.jpg",
    "M10": "globularclusters/M10-01.jpg",
    "M12": "globularclusters/M12-01.jpg",
    "M13": "globularclusters/M13-01.jpg",
    "M14": "globularclusters/M14-01.jpg",
    "M15": "globularclusters/M15-01.jpg",
    "M19": "globularclusters/M19-01.jpg",
    "M22": "globularclusters/M22-01.jpg",
    "M28": "globularclusters/M28-01.jpg",
    "M30": "globularclusters/M30-01.jpg",
    "M53": "globularclusters/M53-01.jpg",
    "M54": "globularclusters/M54-01.jpg",
    "M55": "globularclusters/M55-01.jpg",
    "M56": "globularclusters/M56-01.jpg",
    "M62": "globularclusters/M62-01.jpg",
    "M68": "globularclusters/M68-01.jpg",
    "M69": "globularclusters/M69-01.jpg",
    "M70": "globularclusters/M70-01.jpg",
    "M71": "globularclusters/M71-01.jpg",
    "M72": "globularclusters/M72-01.jpg",
    "M75": "globularclusters/M75-01.jpg",
    "M79": "globularclusters/M79-01.jpg",
    "M80": "globularclusters/M80-01.jpg",
    "M92": "globularclusters/M92-01.jpg",
    "M107": "globularclusters/M107-01.jpg",
    
    # Open Clusters
    "M6": "openclusters/M6-01.jpg",
    "M7": "openclusters/M7-01.jpg",
    "M11": "openclusters/M11-01.jpg",
    "M18": "openclusters/M18-01.jpg",
    "M21": "openclusters/M21-01.jpg",
    "M23": "openclusters/M23-01.jpg",
    "M25": "openclusters/M25-01.jpg",
    "M26": "openclusters/M26-01.jpg",
    "M29": "openclusters/M29-01.jpg",
    "M34": "openclusters/M34-01.jpg",
    "M35": "openclusters/M35-01.jpg",
    "M36": "openclusters/M36-01.jpg",
    "M37": "openclusters/M37-01.jpg",
    "M38": "openclusters/M38-01.jpg",
    "M39": "openclusters/M39-01.jpg",
    "M41": "openclusters/M41-01.jpg",
    "M44": "openclusters/M44-01.jpg",
    "M45": "openclusters/M45-01.jpg",
    "M46": "openclusters/M46-01.jpg",
    "M47": "openclusters/M47-01.jpg",
    "M48": "openclusters/M48-01.jpg",
    "M50": "openclusters/M50-01.jpg",
    "M52": "openclusters/M52-01.jpg",
    "M67": "openclusters/M67-01.jpg",
    "M93": "openclusters/M93-01.jpg",
    "M103": "openclusters/M103-01.jpg",
    
    # Diffuse Nebulae
    "M8": "diffusenebulae/M8-01.jpg",
    "M16": "diffusenebulae/M16-01.jpg",
    "M17": "diffusenebulae/M17-01.jpg",
    "M20": "diffusenebulae/M20-01.jpg",
    "M42": "diffusenebulae/M42-01.jpg",
    "M43": "diffusenebulae/M43-01.jpg",
    "M78": "diffusenebulae/M78-01.jpg",
    
    # Planetary Nebulae
    "M27": "planetarynebulae/M27-01.jpg",
    "M57": "planetarynebulae/M57-01.jpg",
    "M76": "planetarynebulae/M76-01.jpg",
    "M97": "planetarynebulae/M97-01.jpg",
    
    # Galaxies
    "M31": "galaxies/M31-01.jpg",
    "M32": "galaxies/M32-01.jpg",
    "M33": "galaxies/M33-01.jpg",
    "M49": "galaxies/M49-01.jpg",
    "M51": "galaxies/M51-02.jpg",
    "M58": "galaxies/M58-01.jpg",
    "M59": "galaxies/M59-01.jpg",
    "M60": "galaxies/M60-01.jpg",
    "M61": "galaxies/M61-01.jpg",
    "M63": "galaxies/M63-01.jpg",
    "M64": "galaxies/M64-01.jpg",
    "M65": "galaxies/M65-01.jpg",
    "M66": "galaxies/M66-01.jpg",
    "M74": "galaxies/M74-01.jpg",
    "M77": "galaxies/M77-01.jpg",
    "M81": "galaxies/M81-01.jpg",
    "M82": "galaxies/M82-01.jpg",
    "M83": "galaxies/M83-01.jpg",
    "M84": "galaxies/M84-01.jpg",
    "M85": "galaxies/M85-01.jpg",
    "M86": "galaxies/M86-01.jpg",
    "M87": "galaxies/M87-01.jpg",
    "M88": "galaxies/M88-01.jpg",
    "M89": "galaxies/M89-01.jpg",
    "M90": "galaxies/M90-01.jpg",
    "M91": "galaxies/M91-01.jpg",
    "M94": "galaxies/M94-01.jpg",
    "M95": "galaxies/M95-01.jpg",
    "M96": "galaxies/M96-01.jpg",
    "M98": "galaxies/M98-01.jpg",
    "M99": "galaxies/M99-01.jpg",
    "M100": "galaxies/M100-01.jpg",
    "M101": "galaxies/M101-01.jpg",
    "M102": "galaxies/M102-01.jpg",
    "M104": "galaxies/M104-01.jpg",
    "M105": "galaxies/M105-01.jpg",
    "M106": "galaxies/M106-01.jpg",
    "M108": "galaxies/M108-01.jpg",
    "M109": "galaxies/M109-01.jpg",
    "M110": "galaxies/M110-01.jpg",
    
    # Special Objects
    "M24": "milkyway/closeup/M24-01.jpg",
    "M40": "stars/M40-01.jpg",
    "M73": "stars/M73-01.jpg",
}

def download_image(messier_id, image_path, output_dir, session):
    """Download a single Messier object image"""
    url = urljoin(BASE_URL, image_path)
    output_file = os.path.join(output_dir, f"{messier_id}.jpg")
    
    # Skip if already downloaded
    if os.path.exists(output_file):
        print(f"✓ {messier_id} already exists, skipping...")
        return True
    
    try:
        print(f"Downloading {messier_id} from {url}...", end=" ")
        response = session.get(url, timeout=30)
        response.raise_for_status()
        
        # Save the image
        with open(output_file, 'wb') as f:
            f.write(response.content)
        
        print(f"✓ Success ({len(response.content) // 1024} KB)")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"✗ Failed: {e}")
        return False

def main():
    # Create output directory
    output_dir = "messier_images"
    os.makedirs(output_dir, exist_ok=True)
    
    print("=" * 60)
    print("Messier Catalog Image Downloader")
    print("=" * 60)
    print(f"Output directory: {output_dir}")
    print(f"Total objects to download: {len(MESSIER_IMAGES)}")
    print("=" * 60)
    print()
    
    # Create a session for connection pooling
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    
    # Download all images
    success_count = 0
    failed_objects = []
    
    for messier_id, image_path in sorted(MESSIER_IMAGES.items(), key=lambda x: int(x[0][1:])):
        if download_image(messier_id, image_path, output_dir, session):
            success_count += 1
        else:
            failed_objects.append(messier_id)
        
        # Be polite to the server
        time.sleep(0.5)
    
    # Summary
    print()
    print("=" * 60)
    print("Download Summary")
    print("=" * 60)
    print(f"Successfully downloaded: {success_count}/{len(MESSIER_IMAGES)}")
    
    if failed_objects:
        print(f"Failed downloads: {', '.join(failed_objects)}")
    else:
        print("All images downloaded successfully! 🎉")
    
    print(f"\nImages saved to: {os.path.abspath(output_dir)}")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDownload interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError: {e}")
        sys.exit(1)
