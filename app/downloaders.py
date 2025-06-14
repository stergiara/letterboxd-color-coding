# app/downloaders.py
import os, time, json, re, logging
import pandas as pd
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Optional


USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
DELAY = 1  # second pause
logging.basicConfig(level=logging.INFO)

# HTTP session
session = requests.Session()
session.headers.update({"User-Agent": USER_AGENT})
retries = Retry(total=3, backoff_factor=1, status_forcelist=[429,500,502,503,504])
session.mount("https://", HTTPAdapter(max_retries=retries))


def get_poster_url_from_jsonld(uri: str) -> Optional[str]:
    resp = session.get(uri, timeout=10); resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')
    js = soup.find('script', type='application/ld+json')
    if not js or not js.string:
        return None
    text = js.string.strip()
    m = re.search(r'\{.*\}', text, re.S)
    if not m:
        return None
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    image = data.get('image')
    return image if isinstance(image, str) else None


def sanitize_filename(name: str) -> str:
    safe = re.sub(r'[\\/:*?"<>|]', '', name).strip().replace(' ', '_')
    return safe


def download_image(url: str, dest: str) -> None:
    if os.path.exists(dest):
        return
    resp = session.get(url, stream=True, timeout=10); resp.raise_for_status()
    with open(dest, 'wb') as f:
        for chunk in resp.iter_content(8192):
            f.write(chunk)


def download_posters(csv_path: str, output_dir: str) -> list[str]:
    """
    Reads csv_path (expects columns 'Name' and 'Letterboxd URI'),
    downloads each poster into output_dir, and returns list of filenames.
    """
    os.makedirs(output_dir, exist_ok=True)
    df = pd.read_csv(csv_path)
    saved = []

    for _, row in df.iterrows():
        name, uri = row.get('Name'), row.get('Letterboxd URI')
        if not pd.notna(name) or not pd.notna(uri):
            continue
        url = get_poster_url_from_jsonld(uri)
        if not url:
            logging.info(f"No poster for {name}")
            continue

        base = sanitize_filename(name)
        ext  = os.path.splitext(urlparse(url).path)[1]
        out  = os.path.join(output_dir, f"{base}{ext}")

        try:
            download_image(url, out)
            saved.append(out)
            time.sleep(DELAY)
        except Exception as e:
            logging.error(f"Error {name}: {e}")

    return saved
