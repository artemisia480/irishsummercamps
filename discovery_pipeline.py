import re
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, quote_plus, unquote, urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "camps.db"
USER_AGENT = "IrelandCampDirectoryBot/1.0 (+contact@example.com)"

COUNTIES = [
    "Dublin",
    "Cork",
    "Galway",
    "Limerick",
    "Kilkenny",
    "Wicklow",
    "Meath",
    "Kildare",
]

SEARCH_PATTERNS = [
    "summer camp {county}",
    "kids summer camps {county} ireland",
    "sports camp {county} summer",
    "stem camp {county} ireland",
]


def ensure_discovery_table(connection):
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS discovered_urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE NOT NULL,
            domain TEXT NOT NULL,
            query TEXT NOT NULL,
            robots_status TEXT NOT NULL,
            scrape_status TEXT NOT NULL,
            title TEXT,
            discovered_at TEXT NOT NULL,
            last_checked_at TEXT NOT NULL
        )
        """
    )
    connection.commit()


def robots_status_for_url(url):
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    parser = RobotFileParser()
    parser.set_url(robots_url)
    try:
        parser.read()
    except Exception:
        return "unknown"
    return "allowed" if parser.can_fetch(USER_AGENT, url) else "blocked"


def parse_price(text):
    match = re.search(r"€\s?(\d{2,4})", text)
    return float(match.group(1)) if match else None


def parse_age_range(text):
    match = re.search(r"(\d{1,2})\s*[-–]\s*(\d{1,2})\s*(?:year|yrs|years)?", text, re.IGNORECASE)
    if not match:
        return None, None
    return int(match.group(1)), int(match.group(2))


def parse_hours(text):
    match = re.search(r"(\d{1,2}(?::\d{2})?\s?(?:am|pm)?\s*[-–]\s*\d{1,2}(?::\d{2})?\s?(?:am|pm)?)", text, re.IGNORECASE)
    return match.group(1) if match else "Check source page"


def parse_food(text):
    lower = text.lower()
    if "lunch included" in lower or "food provided" in lower or "meals included" in lower:
        return "yes"
    if "bring a snack" in lower or "bring lunch" in lower:
        return "no"
    return "unknown"


def scrape_allowed_url(url):
    response = requests.get(url, timeout=20, headers={"User-Agent": USER_AGENT})
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    title = soup.title.get_text(strip=True) if soup.title else "Summer Camp Listing"
    text = soup.get_text(" ", strip=True)
    return {
        "title": title,
        "priceEur": parse_price(text),
        "ageMin": parse_age_range(text)[0],
        "ageMax": parse_age_range(text)[1],
        "hours": parse_hours(text),
        "foodProvided": parse_food(text),
    }


def infer_county(query):
    for county in COUNTIES:
        if county.lower() in query.lower():
            return county
    return "Unknown"


def upsert_discovery(connection, url, query, robots_status, scrape_status, title):
    now = datetime.utcnow().isoformat()
    domain = urlparse(url).netloc
    connection.execute(
        """
        INSERT INTO discovered_urls (url, domain, query, robots_status, scrape_status, title, discovered_at, last_checked_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(url) DO UPDATE SET
            query = excluded.query,
            robots_status = excluded.robots_status,
            scrape_status = excluded.scrape_status,
            title = excluded.title,
            last_checked_at = excluded.last_checked_at
        """,
        (url, domain, query, robots_status, scrape_status, title, now, now),
    )


def upsert_camp_from_discovery(connection, url, query, details):
    now = datetime.utcnow().isoformat()
    name = details["title"][:120]
    county = infer_county(query)
    existing = connection.execute(
        "SELECT id FROM camps WHERE name = ? AND source_url = ?",
        (name, url),
    ).fetchone()

    if existing:
        connection.execute(
            """
            UPDATE camps
            SET county = ?, price_eur = ?, hours = ?, food_provided = ?, age_min = ?, age_max = ?,
                source_type = 'discovered_scrape', status = 'pending_review',
                notes = ?, last_checked_at = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                county,
                details["priceEur"],
                details["hours"],
                details["foodProvided"],
                details["ageMin"],
                details["ageMax"],
                "Auto-discovered and scraped from public page. Verify fields before publishing.",
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
        VALUES (?, 'Summer camp listing', ?, ?, ?, ?, ?, ?, ?, 'discovered_scrape', 'pending_review', ?, ?, ?, ?)
        """,
        (
            name,
            county,
            details["priceEur"],
            details["hours"],
            details["foodProvided"],
            details["ageMin"],
            details["ageMax"],
            url,
            "Auto-discovered and scraped from public page. Verify fields before publishing.",
            now,
            now,
            now,
        ),
    )


def discover_urls():
    urls_by_query = {}
    for county in COUNTIES:
        for pattern in SEARCH_PATTERNS:
            query = pattern.format(county=county)
            urls = search_duckduckgo_html(query)
            urls_by_query[query] = list(dict.fromkeys(urls))
            time.sleep(1.0)
    return urls_by_query


def clean_result_url(href):
    if not href:
        return None
    if href.startswith("//"):
        href = f"https:{href}"
    if "duckduckgo.com/l/?" in href and "uddg=" in href:
        qs = parse_qs(urlparse(href).query)
        target = qs.get("uddg", [None])[0]
        return unquote(target) if target else None
    if href.startswith("http://") or href.startswith("https://"):
        return href
    return None


def search_duckduckgo_html(query):
    url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=20)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    urls = []
    for link in soup.select("a.result__a"):
        cleaned = clean_result_url(link.get("href"))
        if not cleaned:
            continue
        if "duckduckgo.com" in cleaned:
            continue
        if "facebook.com" in cleaned or "instagram.com" in cleaned:
            continue
        urls.append(cleaned)
        if len(urls) >= 8:
            break
    return urls


def run():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    ensure_discovery_table(connection)

    discovered = discover_urls()
    total_urls = 0
    allowed = 0
    blocked = 0
    scraped = 0

    for query, urls in discovered.items():
        for url in urls:
            total_urls += 1
            status = robots_status_for_url(url)
            if status != "allowed":
                blocked += 1
                upsert_discovery(connection, url, query, status, "skipped", None)
                continue

            allowed += 1
            try:
                details = scrape_allowed_url(url)
                upsert_discovery(connection, url, query, status, "scraped", details["title"])
                upsert_camp_from_discovery(connection, url, query, details)
                scraped += 1
            except Exception:
                upsert_discovery(connection, url, query, status, "error", None)

    connection.commit()
    pending_count = connection.execute(
        "SELECT COUNT(*) AS count FROM camps WHERE status = 'pending_review'"
    ).fetchone()["count"]
    connection.close()

    print(f"Discovery complete: {total_urls} URLs checked")
    print(f"Allowed: {allowed} | Blocked/Unknown: {blocked} | Scraped: {scraped}")
    print(f"Pending review camps total: {pending_count}")


if __name__ == "__main__":
    run()
