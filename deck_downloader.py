import os
import re
import sys
import requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO

def mm_to_px(mm, dpi=600):
    return int(mm / 25.4 * dpi)

def get_next_image_number(folder):
    # Find the next sequntial number based on existing image files.
    existing = [
        int(re.match(r"(\d{3})_", f).group(1))
        for f in os.listdir(folder)
        if re.match(r"\d{3}_", f)
    ]
    return max(existing) + 1 if existing else 1

def fetch_deck(url, out_folder_images='images', out_file_list='decklist.txt', target_mm=(63,88), dpi=600):
    # Create output folder if not exists
    os.makedirs(out_folder_images, exist_ok=True)

    # Fetch the deck page
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    # ---- Step 1: Parse cards and quantities ----
    cards = []
    for tr in soup.select('div.card-container.card-view'):
        img = div.find('img')
        if not img:
            continue

        # Card name
        name = img.get('alt', '').strip()
        if not name:
            continue

        # Card image URL
        img_url + img.get('data-src') or img.get('src')

        # Quantity
        qty = 1
        span = div.find('span')
        if span:
            text = span.get_text(strip=True).lower
            match = re.search(r'(\d+)', text)
            if match:
                qty = int(match.group(1))

        cards.append((qty, name, img_url))

    if not cards:
        raise RuntimeError("No cards found. Check the HTML structure or make sure deck is public.")

    # ---- Step 2: Prepare numbering ----
    next_num = get_next_image_number(out_folder_images)
    width_px = mm_to_px(target_mm[0], dpi)
    height_px = mm_to_px(target_mm[1]. dpi)
        
    # ---- Step 3: Append decklist entries ----
    with open(out_file_list, 'a', encoding='utf-8') as f:
        f.write(f"\n--- Deck from: {url} ---\n")
        for qty, name in cards:
            f.write(f"[{next_num:03d}] {qty}x {name}\n")
            next_num += 1
            
    # Reset next_num to match numbering in text file
    next_num = get_next_image_number(out_folder_images)

    # ---- Step 4: Download images ----
    for qty, name, img_url in cards:
        safe_name = re.sub(r'[\\/*?:"<>|]', '_', name)
        filename = f"{next_num:03d}_{safe_name}.png"
        filepath = os.path.join(out_folder_images, filename)

        # Skip if already downloaded
        if os.path.exists(filepath):
            print(f"Skipping {name} (already downloaded)")
            next_num += 1
            continue

        # Download and resize image
        try:
            img_resp = requests.get(img_url)
            img_resp.raise_for_status()
            img = Image.open(BytesIO(img_resp.content)).convert('RGBA')
            img = Image.open(BytesIO(img_resp.content)).convert('RGBA')
            img = img.resize((width_px, height_px), Image.LANCZOS)
            img.save(filepath)
            print(f"Saved image: {filepath}")
        except Exception as e:
            print(f"Failed to save image for {name}: {e}")

        next_num += 1
    
    print(f"\nDeck '{url}' processed successfully.\n")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python deck_downloader.py <deck-url>")
        sys.exit(1)
        
    deck_url = sys.argv[1]
    fetch_deck(deck_url)
