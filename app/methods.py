import os
import pandas as pd
import numpy as np
from PIL import Image
import colorsys
from sklearn.cluster import KMeans
from skimage.color import rgb2lab, lab2rgb

# === Configuration ===
# No hardcoded paths; caller will supply input/output
RESIZE_MAX   = (200, 300)
BLACK_V      = 0.16
WHITE_V      = 0.72
WHITE_S      = 0.15
GRAY_S       = 0.05
HIST_BINS    = 36
SAMPLE_PIXELS = 20000

# === Helper functions ===

def classify_rgb(rgb):
    """
    Classify an RGB triple [0-1] to a sort key: (group, hue)
    group: 0=color, 1=white, 2=gray, 3=black, 4=no data
    """
    if rgb is None:
        return (4, 0)
    h, s, v = colorsys.rgb_to_hsv(*rgb)
    hue = h * 360
    if v > WHITE_V and s < WHITE_S:
        return (1, 0)
    if s < GRAY_S and BLACK_V <= v <= WHITE_V:
        return (2, 0)
    if v < BLACK_V:
        return (3, 0)
    return (0, hue)


def load_pixels(path):
    img = Image.open(path).convert('RGB')
    img.thumbnail(RESIZE_MAX, Image.LANCZOS)
    arr = np.array(img) / 255.0
    px = arr.reshape(-1, 3)
    if px.shape[0] > SAMPLE_PIXELS:
        idx = np.random.choice(px.shape[0], SAMPLE_PIXELS, replace=False)
        px = px[idx]
    return px

# === Sorting methods ===

def median_cut(path, palette_size=5):
    img = Image.open(path).convert('P', palette=Image.ADAPTIVE, colors=palette_size)
    palette = img.getpalette()[:palette_size * 3]
    counts = img.getcolors()
    dom_idx = max(counts, key=lambda c: c[0])[1]
    r, g, b = palette[dom_idx * 3:dom_idx * 3 + 3]
    return np.array([r, g, b]) / 255.0


def histogram_peak(path):
    px = load_pixels(path)
    hsv = np.array([colorsys.rgb_to_hsv(*p) for p in px])
    h = hsv[:, 0] * 360
    s = hsv[:, 1]
    v = hsv[:, 2]
    mask = (v >= BLACK_V) & ~((v > WHITE_V) & (s < WHITE_S))
    h = h[mask]
    if h.size == 0:
        return None
    counts, edges = np.histogram(h, bins=HIST_BINS, range=(0, 360))
    idx = np.argmax(counts)
    hue = (edges[idx] + edges[idx + 1]) / 2 / 360
    return np.array(colorsys.hsv_to_rgb(hue, 1, 1))


def lab_kmeans(path, k=3):
    px = load_pixels(path)
    lab = rgb2lab(px.reshape(-1, 3)).reshape(-1, 3)
    km = KMeans(n_clusters=k, random_state=0, n_init=10).fit(lab)
    counts = np.bincount(km.labels_)
    center = km.cluster_centers_[np.argmax(counts)]
    return lab2rgb(center.reshape(1, 1, 3)).reshape(3)


def color_naming(path):
    # reuse histogram_peak to get base hue RGB
    return histogram_peak(path)


def two_stage_kmeans(path, k1=2, k2=3):
    px = load_pixels(path)
    lab = rgb2lab(px.reshape(-1, 3)).reshape(-1, 3)
    km1 = KMeans(n_clusters=k1, random_state=0, n_init=10).fit(lab)
    bg_label = np.argmax(km1.cluster_centers_[:, 0])
    fg_lab = lab[km1.labels_ != bg_label]
    if fg_lab.size == 0:
        fg_lab = lab
    km2 = KMeans(n_clusters=k2, random_state=0, n_init=10).fit(fg_lab)
    counts = np.bincount(km2.labels_)
    center = km2.cluster_centers_[np.argmax(counts)]
    return lab2rgb(center.reshape(1, 1, 3)).reshape(3)

# Method registry
def get_methods():
    return {
        'median_cut': median_cut,
        'histogram_peak': histogram_peak,
        'lab_kmeans': lab_kmeans,
        'color_naming': color_naming,
        'two_stage_kmeans': two_stage_kmeans
    }

# === Run all methods ===

def run_all_methods(input_csv: str, output_dir: str) -> None:
    """
    Read `input_csv`, apply each sort method to the covers in the parallel `covers/` dir,
    and write sorted CSVs into `output_dir` using the same columns.
    """
    df = pd.read_csv(input_csv)
    methods = get_methods()
    os.makedirs(output_dir, exist_ok=True)

    for name, func in methods.items():
        results = []  # list of (row, key)
        for _, row in df.iterrows():
            slug = row['Name'].replace(' ', '_')
            # find poster file
            matches = [f for f in os.listdir('covers') if f.startswith(slug)]
            rgb = None
            if matches:
                try:
                    rgb = func(os.path.join('covers', matches[0]))
                except Exception:
                    rgb = None
            key = classify_rgb(rgb)
            results.append((row, key))

        # sort and save
        results.sort(key=lambda x: x[1])
        out_rows = [r[0] for r in results]
        out_df = pd.DataFrame(out_rows, columns=df.columns)
        out_path = os.path.join(output_dir, f'watched_{name}.csv')
        out_df.to_csv(out_path, index=False)