import re
import sys
import os
from playwright.sync_api import sync_playwright

DECKLIST = "decklist.txt"
IMAGE_FOLDER = "images"

def read_decklist(decklist_path):
    cards = []
    with open(decklist_path, "r", encoding="utf-8") as f:
        for line in f:
            match = re.match(r"\[(\d+)\]", line.strip())
            if match:
                num = int(match.group(1))
                cards.append(num)
    return cards

def upload_imgs(url):
    MPC_URL = url
    cards = read_decklist(DECKLIST)

    print(f"Found {len(cards)} entries in decklist.")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        print("Loading MPC editor...")
        page.goto(MPC_URL, wait_until="networkidle")

        page.wait_for_timeout(3000)

        # Uplaod loop
        for card_num in cards:
            file_to_upload = None
            for f in os.listdir(IMAGE_FOLDER):
                if f.startswith(f"{card_num:03d}_"):
                    file_to_upload = os.path.join(IMAGE_FOLDER, f)
                    break

            if not file_to_upload:
                print(f"ERROR: No image found for [{card_num}]")
                continue

            print(f"Uplaoding {file_to_upload} ...")

            # Wait for upload button
            page.wait_for_selector("input[type='file']", state="attached")
            # Upload file
            page.set_input_files("input[type='file']", file_to_upload)

            print("Waiting for MPC to process image...")
            page.wait_for_timeout(5000)
                        
            # Apply image to card slot
            # *Not implemented yet, still WIP*

        print("All images processed!")
        input("Press Enter to close browser...")
        browser.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python MPCuploader.py <MPC url>")
        sys.exit(1)
    upload_imgs(sys.argv[1])
