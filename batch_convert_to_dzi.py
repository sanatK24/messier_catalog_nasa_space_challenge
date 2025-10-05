#!/usr/bin/env python3
"""
Batch convert all Messier images to DZI format for interactive zooming
"""
import os
import sys
import math
import json
from pathlib import Path
from PIL import Image

def create_dzi(input_image_path, output_name, tile_size=256, tile_format='jpg', tile_overlap=1):
    """Convert an image to Deep Zoom Image (DZI) format."""
    print(f"  Processing: {os.path.basename(input_image_path)}")
    
    try:
        img = Image.open(input_image_path)
        
        # Convert to RGB if necessary
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        width, height = img.size
        
        # Calculate number of levels
        max_dimension = max(width, height)
        max_level = math.ceil(math.log2(max_dimension))
        
        # Create output directory structure
        tiles_dir = f"{output_name}_files"
        os.makedirs(tiles_dir, exist_ok=True)
        
        # Generate tiles for each level
        for level in range(max_level + 1):
            level_dir = os.path.join(tiles_dir, str(level))
            os.makedirs(level_dir, exist_ok=True)
            
            # Calculate dimensions for this level
            scale = 2 ** (max_level - level)
            level_width = math.ceil(width / scale)
            level_height = math.ceil(height / scale)
            
            # Resize image for this level
            level_img = img.resize((level_width, level_height), Image.LANCZOS)
            
            # Calculate number of tiles
            cols = math.ceil(level_width / tile_size)
            rows = math.ceil(level_height / tile_size)
            
            # Create tiles
            for row in range(rows):
                for col in range(cols):
                    # Calculate tile boundaries
                    x = col * tile_size
                    y = row * tile_size
                    
                    # Add overlap
                    x1 = max(0, x - tile_overlap)
                    y1 = max(0, y - tile_overlap)
                    x2 = min(level_width, x + tile_size + tile_overlap)
                    y2 = min(level_height, y + tile_size + tile_overlap)
                    
                    # Crop and save tile
                    tile = level_img.crop((x1, y1, x2, y2))
                    tile_path = os.path.join(level_dir, f"{col}_{row}.{tile_format}")
                    
                    if tile_format == 'jpg':
                        tile.save(tile_path, 'JPEG', quality=85)
                    else:
                        tile.save(tile_path, 'PNG')
        
        # Create DZI XML descriptor
        dzi_content = f'''<?xml version="1.0" encoding="utf-8"?>
<Image TileSize="{tile_size}" Overlap="{tile_overlap}" Format="{tile_format}" xmlns="http://schemas.microsoft.com/deepzoom/2008">
    <Size Width="{width}" Height="{height}"/>
</Image>'''
        
        dzi_path = f"{output_name}.dzi"
        with open(dzi_path, 'w') as f:
            f.write(dzi_content)
        
        return True
        
    except Exception as e:
        print(f"    Error: {e}")
        return False

def batch_convert_messier_images(input_dir="messier_images", output_dir="messier_dzi"):
    """Convert all Messier images to DZI format"""
    
    print("=" * 70)
    print("Batch DZI Converter for Messier Catalog")
    print("=" * 70)
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Get all image files
    image_files = []
    for ext in ['*.jpg', '*.jpeg', '*.png']:
        image_files.extend(Path(input_dir).glob(ext))
    
    if not image_files:
        print(f"No images found in {input_dir}")
        return
    
    print(f"Found {len(image_files)} images to convert")
    print("=" * 70)
    
    success_count = 0
    dzi_manifest = []
    
    for idx, image_path in enumerate(sorted(image_files), 1):
        messier_id = image_path.stem.upper().replace('-01N', '').replace('N', '')
        output_name = os.path.join(output_dir, messier_id)
        
        print(f"[{idx}/{len(image_files)}] {messier_id}")
        
        if create_dzi(str(image_path), output_name, tile_size=256):
            success_count += 1
            dzi_manifest.append({
                "id": messier_id,
                "dzi": f"{messier_id}.dzi",
                "thumbnail": str(image_path.name)
            })
    
    # Save manifest
    manifest_path = os.path.join(output_dir, "manifest.json")
    with open(manifest_path, 'w') as f:
        json.dump(dzi_manifest, f, indent=2)
    
    print("\n" + "=" * 70)
    print("Conversion Complete!")
    print("=" * 70)
    print(f"Successfully converted: {success_count}/{len(image_files)} images")
    print(f"DZI files saved to: {os.path.abspath(output_dir)}")
    print(f"Manifest saved to: {os.path.abspath(manifest_path)}")
    print("=" * 70)

if __name__ == "__main__":
    batch_convert_messier_images()
