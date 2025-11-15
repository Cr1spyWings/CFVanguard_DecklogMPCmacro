import os
import re
import sys
import requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
from playwright.sync_api import sync_playwright

def mm_to_px(mm, dpi=300):
    return int(mm / 25.4 * dpi)

def get_next_image_number(folder):
    # Find the next sequntial number based on existing image files.
    existing = []
    for f in os.listdir(folder):
        m = re.match(r"(\d{3})_", f)
        if m:
            existing.append(int(m.group(1)))
    return max(existing) + 1 if existing else 1

def fetch_deck_playwright(url, out_folder_images='images', out_file_list='decklist.txt', target_mm=(215.9,293.69), dpi=300):
    # Create output folder if not exists
    os.makedirs(out_folder_images, exist_ok=True)
    width_px = mm_to_px(target_mm[0], dpi)
    height_px = mm_to_px(target_mm[1], dpi)

    # Gets browser page 
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until='networkidle', timeout = 30000)
        for y in range(0, 7000, 500):
            page.evaluate(f"window.scrollTo(0, {y})")
            page.wait_for_timeout(250)
        page.evaluate("""
            document.querySelectorAll('img[data-src]').forEach(img => {
                if (!img.src || img.src.length < 5) {
                    img.src = img.dataset.src;
                }
            }); """)
        html = page.content()
        browser.close()

    soup = BeautifulSoup(html, 'html.parser')
    
    # ---- Step 1: Parse cards and quantities ----
    cards = []
    card_divs = soup.select('div.card-container.card-view')
    for div in card_divs:
        img = div.find('img', class_='card-view-item')
        if not img:
            continue

        # Card name
        name = img.get('alt', '').strip()
        if not name:
            continue

        # Card image URL
        img_url = img.get('src') or ""
        if len(img_url) < 5 or not img_url.startswith("http"):
            print("Skipping invalid image URL:", img_url)
            continue
        
        # Quantity
        qty_el = div.select_one('span.num')
        qty = int(qty_el.get_text(strip=True)) if qty_el else 1

        cards.append((qty, name, img_url))

    if not cards:
        raise RuntimeError("No cards found after rendering. Inspect the page or adjust selectors.")

    # ---- Step 2: Appending to end of output file ----
    next_num = get_next_image_number(out_folder_images)
        
    with open(out_file_list, 'a', encoding='utf-8') as f:
        f.write(f"\n--- Deck from: {url} ---\n")
        for qty, name, _ in cards:
            f.write(f"[{next_num:03d}] {qty}x {name}\n")
            next_num += 1
            
    # Reset next_num to match numbering in text file
    next_num = get_next_image_number(out_folder_images)

    session = requests.Session()

    # ---- Step 4: Download images ----
    for qty, name, img_url in cards:
        safe_name = re.sub(r'[\\/*?:"<>|]', '_', name)

        for i in range(qty):
            filename = f"{next_num:03d}_{safe_name}.png"
            filepath = os.path.join(out_folder_images, filename)

            if os.path.exists(filepath):
                print(f"Skipping {name} (already downloaded)")
                continue

            try:
                print(f"Downloading: {filename}")
                response = requests.get(img_url, timeout = 10)
                img = Image.open(BytesIO(response.content))

                # Resize image
                img = img.convert('RGBA')
                img = img.resize((width_px, height_px), Image.LANCZOS)
                img.save(filepath)
                print(f"Saved image: {filepath}")
            except Exception as e:
                print(f"FAILED to download {img_url} -> {e}")

        next_num += 1
    
    print(f"\nDeck '{url}' processed successfully.\n")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python deck_downloader.py <deck-url>")
        sys.exit(1)
        
    fetch_deck_playwright(sys.argv[1])
