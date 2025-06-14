import os
import math
import pandas as pd
from PIL import Image, ImageDraw, ImageFont

# === Configuration ===
# No hardcoded paths; caller will supply directories

# Thumbnail settings
THUMB_SIZE    = (4, 6)   # downsample dimensions
UPSCALE       = 20       # scale factor
COLS          = 5        # columns per mosaic
GAP           = 20       # gap between mosaics in final image
TITLE_HEIGHT  = 40       # space below each mosaic for title

# Default font for titles
font = ImageFont.load_default()


def create_mosaic(csv_path: str, posters_dir: str) -> Image.Image:
    """
    Build a horizontal mosaic for a single sorted-CSV.
    Returns a PIL Image of the tiled posters + title.
    """
    df = pd.read_csv(csv_path)
    poster_paths = []
    for name in df['Name']:
        slug = name.replace(' ', '_')
        matches = [f for f in os.listdir(posters_dir) if f.startswith(slug)]
        if matches:
            poster_paths.append(os.path.join(posters_dir, matches[0]))

    total = len(poster_paths)
    rows = math.ceil(total / COLS)
    tw = THUMB_SIZE[0] * UPSCALE
    th = THUMB_SIZE[1] * UPSCALE
    width = COLS * tw
    height = rows * th + TITLE_HEIGHT

    mosaic = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(mosaic)

    # Paste thumbnails
    for idx, path in enumerate(poster_paths):
        with Image.open(path) as img:
            thumb = img.resize(THUMB_SIZE, Image.LANCZOS)
            thumb = thumb.resize((tw, th), Image.NEAREST)
        c = idx % COLS
        r = idx // COLS
        mosaic.paste(thumb, (c * tw, r * th))

    # Draw title
    title = os.path.basename(csv_path)
    bbox = draw.textbbox((0,0), title, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    tx = (width - text_w) // 2
    ty = rows * th + (TITLE_HEIGHT - text_h) // 2
    draw.text((tx, ty), title, font=font, fill='black')

    return mosaic


def build_all_mosaics(sorted_dir: str, posters_dir: str) -> Image.Image:
    """
    Given a directory of sorted CSVs and the covers directory,
    build and stitch all mosaics side-by-side with gaps.
    """
    mosaics = []
    for fname in sorted(os.listdir(sorted_dir)):
        if not fname.lower().endswith('.csv'):
            continue
        path = os.path.join(sorted_dir, fname)
        mosaics.append(create_mosaic(path, posters_dir))

    # Compute final canvas dimensions
    total_w = sum(m.width for m in mosaics) + GAP * (len(mosaics) - 1)
    max_h = max(m.height for m in mosaics)
    final = Image.new('RGB', (total_w, max_h), 'white')

    x = 0
    for m in mosaics:
        final.paste(m, (x, 0))
        x += m.width + GAP

    return final

