import sqlite3
from pathlib import Path

from discovery_pipeline import (
    ensure_discovery_table,
    robots_status_for_url,
    scrape_allowed_url,
    upsert_camp_from_discovery,
    upsert_discovery,
)

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "camps.db"

SEED_URLS = [
    ("https://www.rusheenbay.com/summer-camps", "summer camp Galway"),
    ("https://www.corkacro.com/summer-camps-2026.html", "summer camp Cork"),
    ("https://www.whizzkids.ie/dublin", "summer camp Dublin coding"),
    ("https://www.whizzkids.ie/", "summer camp Ireland coding"),
    ("https://starcamp.ie/summer-camps/", "summer camp nationwide Ireland"),
    ("https://instituteofeducation.ie/course/summer-camp/", "summer camp Dublin coding"),
    ("https://www.oceansofdiscovery.ie/summer-camp-cork", "summer camp Cork watersports"),
    ("https://kravmagacork.ie/teen_summer_camp_2026/", "summer camp Cork teens"),
    ("https://scoilnanog.com/en/summer-camp-2026/", "summer camp Cork language"),
    (
        "https://junioreinsteinsscienceclub.com/events/summer-science-camp-for-kids-claregalway-educate-together-national-school-galway-6th-july-to-10th-july-2026/",
        "summer camp Galway science",
    ),
    (
        "https://junioreinsteinsscienceclub.com/events/summer-science-camp-for-kids-westside-resource-center-galway-20th-july-to-24th-july-2026/",
        "summer camp Galway science",
    ),
    ("https://www.kidscomp.ie/product/summer-camps-in-person/", "lego robotics camp Dublin Cork"),
    ("https://designerminds.ie/camps", "steam camp Ireland robotics lego"),
    ("https://bricks4kidz.ie/our-programs/camps/", "lego camp Ireland"),
    ("https://starcamp.ie/search-summer/", "community centre camp Ireland"),
    ("https://sia.ie/summer-day-camps-for-kids-ireland/", "school camp Ireland archaeology"),
    ("https://just4funkidscamp.com/find-a-summer-camp/", "community centre camp Cork Kerry Limerick"),
    ("https://www.hibfitness.ie/pool/kids-swim-camps/", "swimming camp Cork"),
    ("https://www.woodlands-hotel.ie/leisure-club/swim-camp/", "swimming camp Limerick"),
    ("https://psaacademies.com/product/2025-psa-rai-rugby-academies-ireland-july-aug/", "rugby camp Ireland"),
    ("https://www.delphiadventureresort.com/summer-camps-galway", "adventure camp Galway"),
    ("http://letsgo.gdwin.net/camp/galway---summer-camp/", "kids camp Galway"),
]


def main():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    ensure_discovery_table(connection)

    allowed = 0
    skipped = 0
    scraped = 0

    for url, query in SEED_URLS:
        status = robots_status_for_url(url)
        if status != "allowed":
            skipped += 1
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
    pending = connection.execute(
        "SELECT COUNT(*) AS count FROM camps WHERE status = 'pending_review'"
    ).fetchone()["count"]
    connection.close()

    print(f"Seed discovery complete. Allowed={allowed}, Skipped={skipped}, Scraped={scraped}")
    print(f"Pending review camps: {pending}")


if __name__ == "__main__":
    main()
