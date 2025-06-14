#!/usr/bin/env python3
import os
import pandas as pd
import numpy as np
from PIL import Image
import colorsys

# Configuration
CSV_FILE = "watched.csv"
POSTERS_DIR = "covers"
OUTPUT_CSV = "watched_movies_sorted_by_color.csv"
RESIZE_WIDTH = 230
RESIZE_HEIGHT = 345

# Thresholds
BLACK_V_THRESH  = 0.16
WHITE_V_THRESH  = 0.72
WHITE_S_THRESH  = 0.15
GRAY_S_THRESH   = 0.05

# Read the original CSV, expecting columns: Date, Name, Year, Letterboxd URI
df = pd.read_csv(CSV_FILE)

def compute_sort_key(image_path):
    """
    Compute an average color sort key by resizing to a uniform size,
    averaging RGB, converting to HSV, and classifying into:
      group 0 = colored posters, sorted by hue
      group 1 = white posters
      group 2 = gray posters (very low saturation)
      group 3 = black posters
    Returns a tuple (group, hue) for sorting.
    """
    # Load and resize for smoothing
    with Image.open(image_path) as img:
        img = img.resize((RESIZE_WIDTH, RESIZE_HEIGHT), Image.LANCZOS)
        arr = np.array(img) / 255.0  # normalize

    # Drop alpha channel if present
    if arr.ndim == 3 and arr.shape[2] == 4:
        arr = arr[..., :3]

    # Compute average RGB
    r, g, b = arr.reshape(-1, 3).mean(axis=0)

    # Convert to HSV
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    hue_deg = h * 360

    # 1) White: very bright + low saturation
    if v > WHITE_V_THRESH and s < WHITE_S_THRESH:
        return (1, 0)
    # 2) Gray: very low saturation, mid brightness
    if s < GRAY_S_THRESH and BLACK_V_THRESH <= v <= WHITE_V_THRESH:
        return (2, 0)
    # 3) Black: very dark
    if v < BLACK_V_THRESH:
        return (3, 0)
    # 0) Colored posters: group 0 sorted by hue
    return (0, hue_deg)

# Build list of (sort_key, row)
entries = []
for _, row in df.iterrows():
    name = row['Name']
    # Poster filename uses underscores for spaces
    slug = name.replace(' ', '_')
    # Find matching poster file
    matches = [f for f in os.listdir(POSTERS_DIR)
               if f.startswith(slug + '_') or f.startswith(slug + '.')]
    if not matches:
        continue
    poster_file = os.path.join(POSTERS_DIR, matches[0])

    key = compute_sort_key(poster_file)
    entries.append((key, row))

# Sort by group then hue
entries.sort(key=lambda x: (x[0][0], x[0][1]))

# Rebuild and save
sorted_rows = [e[1] for e in entries]
sorted_df = pd.DataFrame(sorted_rows, columns=df.columns)
sorted_df.to_csv(OUTPUT_CSV, index=False)
