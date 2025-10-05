#!/usr/bin/env python3
"""
stitch_messier_thumbs.py

Create an equirectangular skymap by placing Messier thumbnails at their RA/Dec coordinates.

Usage:
  python stitch_messier_thumbs.py --width 8192 --height 4096 --out output/messier_skymap.png

Requires: Pillow
  pip install pillow

Thumbnails are read from `messier_dzi/<thumbnail>` using `messier_dzi/manifest.json`.
"""

import os
import json
import argparse
from math import floor, ceil, log2, sin, cos, radians
from random import Random
from PIL import Image, ImageOps, ImageFilter, ImageDraw, ImageFont


def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def ra_dec_to_xy(ra_deg, dec_deg, width, height):
    """Map RA (0..360) and Dec (-90..+90) to pixel coordinates on equirectangular image.

    RA 0 -> left, RA increases to the right. Dec +90 (north) -> y=0 (top), Dec -90 -> y=height.
    """
    x = (ra_deg % 360.0) / 360.0 * width
    y = (90.0 - dec_deg) / 180.0 * height
    return int(x), int(y)


def stereographic_xy(ra_deg, dec_deg, width, height, center_ra=180.0, center_dec=0.0):
    """Project RA/Dec to stereographic x,y centered at (center_ra, center_dec).
    Returns pixel coordinates on canvas width x height. This is an approximate full-sky mapping
    for prototype purposes (note: stereographic cannot represent whole sky without clipping).
    """
    # convert to radians
    lam = radians(ra_deg)
    phi = radians(dec_deg)
    lam0 = radians(center_ra)
    phi0 = radians(center_dec)

    # spherical to stereographic projection
    cosc = sin(phi0)*sin(phi) + cos(phi0)*cos(phi)*cos(lam - lam0)
    # avoid division by zero
    k = 2.0 / max(1e-8, (1.0 + cosc))
    x = k * cos(phi) * sin(lam - lam0)
    y = k * (cos(phi0)*sin(phi) - sin(phi0)*cos(phi)*cos(lam - lam0))

    # Normalize x,y to [-1,1] using an estimated scale factor so that typical values fit canvas
    # Use a small multiplier to scale to image pixels; this is heuristic for prototype.
    scale = min(width, height) / 4.0
    px = int((width / 2.0) + x * scale)
    py = int((height / 2.0) - y * scale)
    return px, py


def size_from_magnitude(mag, base=160, min_size=20, max_size=400):
    """Heuristic: brighter objects (smaller mag) get larger thumbnails.
    This is simple and adjustable for a hackathon prototype.
    """
    try:
        m = float(mag)
    except Exception:
        m = 8.0
    # map mag in range [-1..12] to scale 1.6..0.15
    scale = max(0.12, min(1.6, (10.0 - m) / 8.0))
    size = int(base * scale)
    size = max(min_size, min(max_size, size))
    return size


def generate_starfield(width, height, star_count=4000, seed=0):
    """Generate a procedural starfield as a PIL Image.
    star_count: number of stars (points) to draw; seed ensures reproducibility.
    """
    rnd = Random(seed)
    bg = Image.new('RGB', (width, height), (2, 6, 12))
    draw = ImageDraw.Draw(bg)

    # Add a soft gradient
    for y in range(height):
        v = int(6 + 20 * (1 - abs((y - height/2) / (height/2))))
        draw.line([(0, y), (width, y)], fill=(v, v+8, v+12))

    # Draw stars with varying brightness and small halos
    for i in range(star_count):
        x = rnd.randrange(0, width)
        y = rnd.randrange(0, height)
        b = rnd.random()
        if b < 0.97:
            r = rnd.choice([0,1,1])
            color = (200, 220, 255) if rnd.random() > 0.7 else (220, 230, 255)
        else:
            r = rnd.choice([2,3,4])
            color = (255, 245, 220)
        draw.point((x,y), fill=color)
        if r>0:
            # small halo
            halo = Image.new('RGBA', (r*4+1, r*4+1), (0,0,0,0))
            hd = ImageDraw.Draw(halo)
            hd.ellipse((0,0,r*4,r*4), fill=(color[0],color[1],color[2],30))
            bg.paste(halo, (x - r*2, y - r*2), halo)

    # slight gaussian blur for realism
    bg = bg.filter(ImageFilter.GaussianBlur(radius=0.6))
    return bg


def main(args):
    root = os.path.abspath(os.path.dirname(__file__))
    data_path = os.path.join(root, 'messier_data.json')
    manifest_path = os.path.join(root, 'messier_dzi', 'manifest.json')

    if not os.path.exists(data_path):
        print('ERROR: messier_data.json not found in project root.')
        return
    if not os.path.exists(manifest_path):
        print('WARNING: manifest.json not found in messier_dzi/. Thumbnails may be missing.')

    messier = load_json(data_path)
    manifest = {}
    if os.path.exists(manifest_path):
        try:
            for item in load_json(manifest_path):
                manifest[item.get('id')] = item
        except Exception as e:
            print('Failed to parse manifest.json:', e)

    width = args.width
    height = args.height
    out_path = args.out

    # build starfield background (or use provided image if exists)
    star_bg_path = os.path.join(root, 'messier_images', 'stars-bg.jpg')
    if os.path.exists(star_bg_path):
        bg = Image.open(star_bg_path).convert('RGBA').resize((width, height), Image.LANCZOS)
    else:
        bg = generate_starfield(width, height, star_count=6000, seed=42).convert('RGBA')

    canvas = Image.new('RGBA', (width, height), (0, 0, 0, 255))
    canvas.alpha_composite(bg)

    placed = 0
    missing = []

    hotspots = []
    draw = ImageDraw.Draw(canvas)
    font = None
    try:
        font = ImageFont.truetype('arial.ttf', 14)
    except Exception:
        font = ImageFont.load_default()

    for o in messier:
        oid = o.get('id')
        ra = o.get('ra_decimal')
        dec = o.get('dec_decimal')
        mag = o.get('magnitude', None)

        if ra is None or dec is None:
            missing.append((oid, 'no coords'))
            continue

    # find thumbnail in manifest
        thumb_path = None
        entry = manifest.get(oid)
        # tolerant lookup: some manifest ids include suffixes like 'M51-02'
        if not entry:
            for k,v in manifest.items():
                if k == oid or k.startswith(oid + '-') or oid.startswith(k + '-') or oid in k:
                    entry = v
                    break
        if entry and entry.get('thumbnail'):
            candidate = os.path.join(root, 'messier_dzi', entry['thumbnail'])
            if os.path.exists(candidate):
                thumb_path = candidate
        # fallback: try common filename patterns
        if not thumb_path:
            for ext in ('.jpg', '.jpeg', '.png'):
                candidate = os.path.join(root, 'messier_dzi', f"{oid}{ext}")
                if os.path.exists(candidate):
                    thumb_path = candidate
                    break

        # fallback: try to use lowest-resolution DZI tile from the _files folder
        if not thumb_path:
            # try possible _files directories: either <oid>_files or the base name from the manifest entry (e.g. M51-02_files)
            possible_dirs = [f"{oid}_files"]
            if entry:
                base = None
                if entry.get('dzi'):
                    base = os.path.splitext(entry['dzi'])[0]
                elif entry.get('thumbnail'):
                    base = os.path.splitext(entry['thumbnail'])[0]
                if base and f"{base}_files" not in possible_dirs:
                    possible_dirs.append(f"{base}_files")

            for d in possible_dirs:
                files_dir = os.path.join(root, 'messier_dzi', d)
                if not os.path.isdir(files_dir):
                    continue
                # list numeric subdirectories (levels)
                levels = []
                for name in os.listdir(files_dir):
                    if name.isdigit():
                        levels.append(int(name))
                if levels:
                    min_level = str(min(levels))
                    candidate = os.path.join(files_dir, min_level, '0_0.jpg')
                    if os.path.exists(candidate):
                        thumb_path = candidate
                        break

        if not thumb_path:
            missing.append((oid, 'thumbnail not found'))
            continue

        try:
            im = Image.open(thumb_path).convert('RGBA')
        except Exception as e:
            missing.append((oid, f'error opening: {e}'))
            continue

        # size heuristic
        sz = size_from_magnitude(mag, base=args.base_size)
        # preserve aspect ratio
        im.thumbnail((sz, sz), Image.LANCZOS)

        # create feathered mask
        alpha = im.split()[-1]
        # if fully opaque, create mask from luminosity
        if alpha.getextrema() == (255, 255):
            mask = ImageOps.grayscale(im).point(lambda p: p)
        else:
            mask = alpha
        # apply blur to mask for feathering
        if args.feather_radius > 0:
            mask = mask.filter(ImageFilter.GaussianBlur(radius=args.feather_radius))

        # projection choice
        if args.projection == 'stereographic':
            x, y = stereographic_xy(float(ra), float(dec), width, height, center_ra=args.center_ra, center_dec=args.center_dec)
        else:
            x, y = ra_dec_to_xy(float(ra), float(dec), width, height)

        # paste centered
        px = int(x - im.width // 2)
        py = int(y - im.height // 2)

        # clamp paste region to canvas bounds
        if px > width or py > height or (px + im.width) < 0 or (py + im.height) < 0:
            # completely outside
            missing.append((oid, 'outside bounds'))
            continue

        # composite with feather mask
        canvas.alpha_composite(Image.new('RGBA', canvas.size, (0,0,0,0)))
        canvas.paste(im, (px, py), mask)

        # record hotspot bounding box and label position
        bbox = [px, py, px + im.width, py + im.height]
        center = [x, y]
        hotspots.append({
            'id': oid,
            'name': o.get('name'),
            'bbox_px': bbox,
            'center_px': center,
            'bbox_norm': [bbox[0]/width, bbox[1]/height, bbox[2]/width, bbox[3]/height]
        })

        # draw label (small, with outline)
        if args.draw_labels:
            label = oid
            tx = bbox[2] + 6
            ty = bbox[1]
            # outline
            draw.text((tx-1,ty-1), label, font=font, fill=(0,0,0))
            draw.text((tx+1,ty-1), label, font=font, fill=(0,0,0))
            draw.text((tx-1,ty+1), label, font=font, fill=(0,0,0))
            draw.text((tx+1,ty+1), label, font=font, fill=(0,0,0))
            draw.text((tx,ty), label, font=font, fill=(220, 235, 255))

        placed += 1

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    canvas.save(out_path)

    # save hotspots JSON
    hs_path = os.path.splitext(out_path)[0] + '_hotspots.json'
    with open(hs_path, 'w', encoding='utf-8') as f:
        json.dump(hotspots, f, indent=2)
    print(f'Hotspots written: {hs_path}')

    # Optionally generate tiles
    if args.generate_tiles:
        tile_size = 256
        # determine max zoom so that tile size ~256 at highest zoom
        max_zoom = args.max_zoom if args.max_zoom is not None else int(ceil(log2(max(1, width / tile_size))))
        tiles_dir = os.path.join(os.path.dirname(out_path), 'tiles')
        print(f'Generating tiles up to zoom {max_zoom} -> {tiles_dir} ...')
        for z in range(0, max_zoom+1):
            n = 2 ** z
            tile_w = width / n
            tile_h = height / n
            for x in range(n):
                for y in range(n):
                    left = int(round(x * tile_w))
                    upper = int(round(y * tile_h))
                    right = int(round((x+1) * tile_w))
                    lower = int(round((y+1) * tile_h))
                    tile = canvas.crop((left, upper, right, lower)).resize((tile_size, tile_size), Image.LANCZOS)
                    out_tile_dir = os.path.join(tiles_dir, str(z), str(x))
                    os.makedirs(out_tile_dir, exist_ok=True)
                    tile_path = os.path.join(out_tile_dir, f"{y}.png")
                    tile.save(tile_path)
        print('Tiles generated.')

    print(f'Output written: {out_path}')
    print(f'Placed thumbnails: {placed}')
    if missing:
        print(f'Missing or skipped: {len(missing)}')
        for m in missing:
            print(' -', m[0], ':', m[1])


if __name__ == '__main__':
    p = argparse.ArgumentParser(description='Stitch Messier thumbnails into an equirectangular skymap')
    p.add_argument('--width', type=int, default=8192, help='output width in pixels')
    p.add_argument('--height', type=int, default=4096, help='output height in pixels')
    p.add_argument('--out', type=str, default='output/messier_skymap.png', help='output image path')
    p.add_argument('--base-size', type=int, default=160, help='base thumbnail size (affects magnitude scaling)')
    p.add_argument('--feather-radius', type=float, default=4.0, help='radius for feathering thumbnails (px)')
    p.add_argument('--draw-labels', action='store_true', help='draw ID labels next to thumbnails')
    p.add_argument('--generate-tiles', action='store_true', help='generate XYZ tiles for the stitched image')
    p.add_argument('--max-zoom', type=int, default=None, help='max zoom level for tile generation (overrides auto)')
    p.add_argument('--projection', choices=['equirectangular','stereographic'], default='equirectangular', help='map projection to use')
    p.add_argument('--center-ra', type=float, default=180.0, help='center RA (deg) for stereographic projection')
    p.add_argument('--center-dec', type=float, default=0.0, help='center Dec (deg) for stereographic projection')
    args = p.parse_args()
    main(args)
