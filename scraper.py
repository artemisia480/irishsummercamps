import json
import sqlite3
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "camps.db"
SOURCES_PATH = BASE_DIR / "sources.json"
USER_AGENT = "IrelandCampDirectoryBot/1.0 (+contact@example.com)"


def load_sources():
    if not SOURCES_PATH.exists():
        return []
    with open(SOURCES_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def is_allowed_by_robots(url):
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    parser = RobotFileParser()
    parser.set_url(robots_url)
    try:
        parser.read()
    except Exception:
        return False
    return parser.can_fetch(USER_AGENT, url)


def extract_text(soup, selector):
    element = soup.select_one(selector)
    return element.get_text(strip=True) if element else None


def upsert_camp(connection, camp):
    now = datetime.utcnow().isoformat()
    existing = connection.execute(
        "SELECT id FROM camps WHERE name = ? AND county = ?",
        (camp["name"], camp["county"]),
    ).fetchone()

    if existing:
        connection.execute(
            """
            UPDATE camps
            SET type = ?, price_eur = ?, hours = ?, food_provided = ?, age_min = ?, age_max = ?,
                source_url = ?, source_type = 'scraped', status = 'pending_review', notes = ?, last_checked_at = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                camp["type"],
                camp["priceEur"],
                camp["hours"],
                camp["foodProvided"],
                camp["ageMin"],
                camp["ageMax"],
                camp["sourceUrl"],
                camp.get("notes"),
                now,
                now,
                existing["id"],
            ),
        )
        return

    connection.execute(
        """
        INSERT INTO camps
        (name, type, county, price_eur, hours, food_provided, age_min, age_max, source_url, source_type, status,
         notes, last_checked_at, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'scraped', 'pending_review', ?, ?, ?, ?)
        """,
        (
            camp["name"],
            camp["type"],
            camp["county"],
            camp["priceEur"],
            camp["hours"],
            camp["foodProvided"],
            camp["ageMin"],
            camp["ageMax"],
            camp["sourceUrl"],
            camp.get("notes"),
            now,
            now,
            now,
        ),
    )


def scrape_source(source):
    url = source["url"]
    if not is_allowed_by_robots(url):
        print(f"Skipped by robots.txt: {url}")
        return []

    response = requests.get(url, timeout=20, headers={"User-Agent": USER_AGENT})
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    items = []
    for card in soup.select(source["campCardSelector"]):
        camp = {
            "name": extract_text(card, source["fields"]["name"]),
            "type": extract_text(card, source["fields"]["type"]) or "Summer camp",
            "county": source["county"],
            "priceEur": None,
            "hours": extract_text(card, source["fields"]["hours"]) or "Check website",
            "foodProvided": source.get("defaultFoodProvided", "unknown"),
            "ageMin": source.get("defaultAgeMin"),
            "ageMax": source.get("defaultAgeMax"),
            "sourceUrl": url,
            "notes": "Auto-scraped. Needs verification before publishing.",
        }
        if camp["name"]:
            items.append(camp)
    return items


def run():
    sources = load_sources()
    if not sources:
        print("No sources found. Add entries to sources.json.")
        return

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    total = 0
    for source in sources:
        try:
            camps = scrape_source(source)
            for camp in camps:
                upsert_camp(connection, camp)
            total += len(camps)
            print(f"Processed {len(camps)} camps from {source['url']}")
        except Exception as error:
            print(f"Error scraping {source['url']}: {error}")

    connection.commit()
    connection.close()
    print(f"Done. {total} camps scraped and marked for review.")


if __name__ == "__main__":
    run()
