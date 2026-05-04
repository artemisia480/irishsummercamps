"""
Scrape TheKerryMam directory for Irish summer camps and add new ones to camps.db.
Covers Dublin summer camps pages, cross-references existing DB entries to avoid dupes.
"""
import re
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

DB_PATH = Path(__file__).parent / "camps.db"
HEADERS = {"User-Agent": "IrelandCampDirectoryBot/1.0 (+contact@example.com)"}

# Pages to scrape — Dublin summer camps (?in_loc=2235 is Dublin area)
BASE_URL = (
    "https://thekerrymam.ie/search-result/"
    "?in_cat=2566&in_loc=2235&directory_type=all"
    "&paged={page}"
    "&custom_field%5Bcustom-checkbox-2%5D%5B%5D=Summer%20Camps"
)

COUNTY_MAP = {
    "dublin 16": "Dublin", "dublin 15": "Dublin", "dublin 14": "Dublin",
    "dublin 12": "Dublin", "dublin 18": "Dublin", "dublin 24": "Dublin",
    "dublin 6": "Dublin", "ballinteer": "Dublin", "rathmines": "Dublin",
    "castleknock": "Dublin", "tallaght": "Dublin", "lucan": "Dublin",
    "malahide": "Dublin", "sutton": "Dublin", "dundrum": "Dublin",
    "baldoyle": "Dublin", "glenageary": "Dublin",
    "co. kerry": "Kerry", "kerry": "Kerry", "killarney": "Kerry",
    "tralee": "Kerry", "cork": "Cork", "galway": "Galway",
    "limerick": "Limerick", "wicklow": "Wicklow", "meath": "Meath",
    "kildare": "Kildare", "wexford": "Wexford", "louth": "Louth",
}

TYPE_MAP = {
    ("science", "stem"): "STEM",
    ("art", "craft", "paint", "drawing"): "Arts & Crafts",
    ("gymnastics", "gym", "cheerleading"): "Gymnastics",
    ("dance", "stage", "performing"): "Dance & Performing Arts",
    ("sport", "soccer", "football", "rugby", "swimming", "multi-sport", "basketball", "athletics"): "Sports",
    ("outdoor", "forest", "nature", "adventure"): "Outdoor & Nature",
    ("music", "singing"): "Music",
    ("coding", "robotics", "tech"): "STEM",
    ("language", "irish"): "Language",
    ("cooking", "baking"): "Cooking",
}


def guess_county(text: str) -> str:
    text_lower = text.lower()
    for keyword, county in COUNTY_MAP.items():
        if keyword in text_lower:
            return county
    return "Dublin"  # default for this query's location


def guess_type(text: str) -> str:
    text_lower = text.lower()
    for keywords, camp_type in TYPE_MAP.items():
        if any(kw in text_lower for kw in keywords):
            return camp_type
    return "Multi-activity"


def extract_age_range(text: str):
    age_min, age_max = None, None
    match = re.search(r"ages?\s*(\d+)\s*[-–to]+\s*(\d+)", text, re.IGNORECASE)
    if match:
        age_min, age_max = int(match.group(1)), int(match.group(2))
    else:
        match = re.search(r"(\d+)\s*[-–]\s*(\d+)\s*year", text, re.IGNORECASE)
        if match:
            age_min, age_max = int(match.group(1)), int(match.group(2))
        else:
            match = re.search(r"age[sd]?\s+(\d+)", text, re.IGNORECASE)
            if match:
                age_min = int(match.group(1))
    return age_min, age_max


def get_existing_names(conn):
    c = conn.cursor()
    c.execute("SELECT LOWER(name) FROM camps")
    return {row[0] for row in c.fetchall()}


def scrape_page(page: int):
    url = BASE_URL.format(page=page)
    print(f"  Fetching page {page}: {url}")
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
    except Exception as e:
        print(f"  ERROR fetching page {page}: {e}")
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    camps = []

    # Each camp listing is an article or div with a title link
    # TheKerryMam uses .item-list or article cards
    for card in soup.select("article.item, .item-content, .directory-item, article"):
        title_el = card.select_one("h2 a, h3 a, .item-title a, .listing-title a")
        if not title_el:
            continue
        name = title_el.get_text(strip=True)
        if not name:
            continue

        link = title_el.get("href", "")
        desc_el = card.select_one("p, .item-excerpt, .listing-excerpt")
        description = desc_el.get_text(strip=True) if desc_el else ""

        address_el = card.select_one(".item-address, address, .listing-address")
        address = address_el.get_text(strip=True) if address_el else ""

        full_text = f"{name} {description} {address}"
        county = guess_county(full_text)
        camp_type = guess_type(full_text)
        age_min, age_max = extract_age_range(description)

        camps.append({
            "name": name,
            "type": camp_type,
            "county": county,
            "location_detail": address or "",
            "source_url": link or url,
            "description": description,
            "age_min": age_min,
            "age_max": age_max,
        })

    return camps


def scrape_all(max_pages=10):
    conn = sqlite3.connect(DB_PATH)
    existing = get_existing_names(conn)
    now = datetime.utcnow().isoformat()
    added = 0
    skipped = 0

    for page in range(1, max_pages + 1):
        camps = scrape_page(page)
        if not camps:
            print(f"  No camps found on page {page}, stopping.")
            break

        for camp in camps:
            if camp["name"].lower() in existing:
                skipped += 1
                continue

            c = conn.cursor()
            c.execute(
                """INSERT INTO camps
                   (name, type, county, location_detail, source_url, status, notes,
                    age_min, age_max, food_provided, created_at, updated_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    camp["name"], camp["type"], camp["county"],
                    camp["location_detail"], camp["source_url"],
                    "pending_review", camp["description"],
                    camp["age_min"], camp["age_max"],
                    "unknown", now, now,
                ),
            )
            conn.commit()
            existing.add(camp["name"].lower())
            added += 1
            print(f"  + Added: {camp['name']} ({camp['county']}) [{camp['type']}]")

        time.sleep(1)  # polite delay

    conn.close()
    print(f"\nDone. Added {added} new camps, skipped {skipped} duplicates.")
    return added


if __name__ == "__main__":
    pages = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    print(f"Scraping TheKerryMam for Dublin summer camps (up to {pages} pages)...")
    scrape_all(max_pages=pages)
