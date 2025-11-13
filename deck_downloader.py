import os
import re
import sys
import requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO

def mm_to_px(mm, dpi=300):
    return int(mm / 25.4 * dpi)

def fetch_deck(url, out_folder_images='images', out_file_list='decklist.txt', target_mm=(63,88), dpi=300):
    # Create output folder if not exists
    os.makedirs(out_folder_images, exist_ok=True)

    # Fetch the deck page
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    # ---- Step 1: Parse cards and quantities ----
    cards = []
    for tr in soup.select('table.decklist tr'):
    cols = tr.find_all('td')
        if len(cols) >= 2:
            qty = cols[0].get_text(strip=True)
            name = cols[1].get_text(strip=True)
            if qty.isdigit():
                cards.append((int(qty), name))

    if not cards:
        raise RuntimeError("Could not find any cards on this deck page. Check the site structure or selectors.")
        
    # ---- Step 2: Append decklist entries ----
    with open(out_file_list, 'a', encoding='utf-8') as f:
        f.write(f"\n--- Deck from: {url} ---\n")
        for qty, name in cards:
            f.write(f"{qty}× {name}\n")
            
    # ---- Step 3: Download images ----
    width_px = mm_to_px(target_mm[0], dpi)
    height_px = mm_to_px(target_mm[1], dpi)

    for qty, name in cards:
        safe_name = re.sub(r'[\\/*?:"<>|]', '_', name)
        filename = f"{safe_name}.png"
        filepath = os.path.join(out_folder_images, filename)

    # Skip if already downloaded
    if os.path.exists(filepath):
        print(f"Skipping {name} (already downloaded)")
        continue
        
    # Attempt to find image tag — may need adjustment
    img_tag = soup.find('img', alt=name)
    if img_tag and img_tag.get('src'):
        img_url = img_tag['src']
    else:
        print(f"Warning: Could not locate image for {name}")
        continue

    # Download and resize image
    try:
        img_resp = requests.get(img_url)
        img_resp.raise_for_status()
        img = Image.open(BytesIO(img_resp.content)).convert('RGBA')
        img = img.resize((width_px, height_px), Image.LANCZOS)
        img.save(filepath)
        print(f"Saved image: {filepath}")
    except Exception as e:
        print(f"Failed to save image for {name}: {e}")

    print(f"\nDeck '{url}' processed successfully.\n")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python deck_downloader.py <deck-url>")
        sys.exit(1)
        
    deck_url = sys.argv[1]
    fetch_deck(deck_url)
