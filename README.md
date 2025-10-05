# Messier Skymap — Hackathon Prototype

This is a 24–72 hour-friendly prototype that visualizes the 110 Messier objects on a zoomable skymap. It uses Leaflet for mapping and OpenSeadragon for deep-zoom DZI images (a subset of DZI tiles is included in `messier_dzi/`).

How to run (simple):

1. Open `index.html` in a browser that allows local file fetches (some browsers block fetch from file://). Recommended: run a local static server from the project root.

Example (Python 3):

```cmd
python -m http.server 8000
```

Then visit http://localhost:8000/index.html

Windows tip: from PowerShell or cmd.exe run the same python command above. If you don't have Python, use a lightweight static server like `npx http-server` (Node.js required):

```cmd
npx http-server -p 8000
```

What exists:
- `index.html` — main UI
- `css/styles.css` — dark, space-themed styles
- `js/app.js` — app logic: loads `messier_data.json` and `messier_dzi/manifest.json`, builds map and modal viewer
- `messier_data.json` — catalog with RA/DEC and metadata
- `messier_dzi/` — DZI files and thumbnails (subset)

Next steps / stretch ideas:
- Add filters (type: galaxy/nebula/cluster) and toggle between historical/modern imagery
- Add constellation overlays and clickable guides
- Improve RA/Dec projection and star background (use real star catalog tiles)
- Add annotations and shareable links
# DZI Image Converter

This tool converts images to Deep Zoom Image (DZI) format using pyvips and provides a web viewer using OpenSeadragon.

## Prerequisites

1. Python 3.6+
2. libvips library (required by pyvips)
3. pip (Python package manager)

## Installation

1. Install libvips:
   - **Windows**: Download from [libvips Windows binaries](https://github.com/libvips/libvips/releases)
   - **macOS**: `brew install vips`
   - **Ubuntu/Debian**: `sudo apt-get install libvips-dev`
   - **Fedora**: `sudo dnf install vips-devel`

2. Install the required Python package:
   ```bash
   pip install pyvips
   ```

## Usage

### Convert an image to DZI format:

```bash
python image_to_dzi.py input.jpg [output_folder]
```

If `output_folder` is not specified, it will use the input filename without extension.

### View the DZI image:

1. Start a local web server in the project directory:
   ```bash
   python -m http.server 8000
   ```

2. Open your web browser and navigate to:
   ```
   http://localhost:8000/viewer.html?dzi=your_image.dzi
   ```
   Replace `your_image.dzi` with the path to your DZI file relative to the project directory.

## Example

```bash
# Convert an image to DZI
python image_to_dzi.py sample.jpg

# This will create:
# - sample.dzi
# - sample_files/ (directory with image tiles)

# Then open in browser:
# http://localhost:8000/viewer.html?dzi=sample.dzi
```

## Features

- Fast image conversion using libvips
- Supports various image formats (JPEG, PNG, TIFF, etc.)
- Interactive web viewer with zoom and pan
- Responsive design that works on desktop and mobile

## License

MIT
