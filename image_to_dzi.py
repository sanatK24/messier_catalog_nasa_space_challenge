#!/usr/bin/env python3
import sys
import os
import math
from PIL import Image

def create_dzi(input_image_path, output_name, tile_size=256, tile_format='jpg', tile_overlap=1):
    """
    Convert an image to Deep Zoom Image (DZI) format.
    
    Args:
        input_image_path: Path to input image
        output_name: Base name for output (without extension)
        tile_size: Size of each tile (default 256)
        tile_format: Format for tiles (jpg or png)
        tile_overlap: Overlap between tiles (default 1)
    """
    print(f"Loading image: {input_image_path}")
    img = Image.open(input_image_path)
    
    # Convert to RGB if necessary
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    width, height = img.size
    print(f"Image size: {width}x{height}")
    
    # Calculate number of levels
    max_dimension = max(width, height)
    max_level = math.ceil(math.log2(max_dimension))
    
    print(f"Creating {max_level + 1} zoom levels...")
    
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
        
        print(f"  Level {level}: {level_width}x{level_height} ({cols}x{rows} tiles)")
        
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
                    tile.save(tile_path, 'JPEG', quality=90)
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
    
    print(f"\nDZI created successfully!")
    print(f"  DZI file: {dzi_path}")
    print(f"  Tiles directory: {tiles_dir}")
    print(f"  Total levels: {max_level + 1}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python image_to_dzi.py <input_image> <output_name> [tile_size]")
        print("Example: python image_to_dzi.py input.jpg output 256")
        sys.exit(1)
    
    input_image = sys.argv[1]
    output_name = sys.argv[2]
    tile_size = int(sys.argv[3]) if len(sys.argv) > 3 else 256
    
    if not os.path.exists(input_image):
        print(f"Error: Input image '{input_image}' not found")
        sys.exit(1)
    
    create_dzi(input_image, output_name, tile_size=tile_size)