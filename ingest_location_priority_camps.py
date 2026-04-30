import sqlite3
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "camps.db"

LOCATION_PRIORITY_CAMPS = [
    {
        "name": "UCD Sport Multisport Summer Camp",
        "type": "Multi-sport camp",
        "county": "Dublin",
        "locationDetail": "UCD Sports Centre, Belfield, Dublin 4",
        "priceEur": None,
        "hours": "09:00-14:00 (after-camp to 16:00)",
        "foodProvided": "unknown",
        "ageMin": 5,
        "ageMax": 14,
        "sourceUrl": "https://www.ucd.ie/sportfacilities/summercamps/",
        "notes": "Official UCD Sport camps page with schedule and booking link.",
    },
    {
        "name": "Whizzkids Dublin Coding Camp (UCD/DCU)",
        "type": "Coding, robotics and digital skills camp",
        "county": "Dublin",
        "locationDetail": "Daedalus Building (UCD) and DCU campus, Dublin",
        "priceEur": 140,
        "hours": "09:30-13:00 or 09:30-15:00",
        "foodProvided": "no",
        "ageMin": 8,
        "ageMax": 15,
        "sourceUrl": "https://www.whizzkids.ie/dublin",
        "notes": "Pricing varies by half-day/full-day option.",
    },
    {
        "name": "Trinity Walton Club STEM Camps",
        "type": "STEM and science camp",
        "county": "Dublin",
        "locationDetail": "Trinity College Dublin, College Green, Dublin 2",
        "priceEur": None,
        "hours": "10:00-14:00 or 10:00-15:00",
        "foodProvided": "unknown",
        "ageMin": 13,
        "ageMax": 18,
        "sourceUrl": "https://www.tcd.ie/waltonclub/STEM-camps.php",
        "notes": "Summer programme for second-level students.",
    },
    {
        "name": "UCD Computer Science Summer School",
        "type": "Science and coding camp",
        "county": "Dublin",
        "locationDetail": "O'Brien Centre for Science, UCD Belfield, Dublin 4",
        "priceEur": 35,
        "hours": "09:30-15:30",
        "foodProvided": "yes",
        "ageMin": 16,
        "ageMax": 18,
        "sourceUrl": "https://ucdsummerschool.ie/june-4-day-3/computer-science/",
        "notes": "Senior cycle focused summer school; includes lunch per source page.",
    },
    {
        "name": "Zero Latency Kids VR Camp Dublin",
        "type": "VR and STEM camp",
        "county": "Dublin",
        "locationDetail": "Zero Latency VR Dublin venue (see booking page)",
        "priceEur": 160,
        "hours": "09:00-13:30",
        "foodProvided": "unknown",
        "ageMin": 8,
        "ageMax": 14,
        "sourceUrl": "https://zerolatencyvr.ie/easter-summer-camp/",
        "notes": "Recent camp listings show EUR 160 per week with 09:00-13:30 sessions; confirm current-season pricing on booking page.",
    },
]


def ensure_location_column(connection):
    cols = {row[1] for row in connection.execute("PRAGMA table_info(camps)").fetchall()}
    if "location_detail" not in cols:
        connection.execute("ALTER TABLE camps ADD COLUMN location_detail TEXT")
        connection.commit()


def upsert(connection, camp):
    now = datetime.utcnow().isoformat()
    existing = connection.execute("SELECT id FROM camps WHERE name = ?", (camp["name"],)).fetchone()
    if existing:
        connection.execute(
            """
            UPDATE camps
            SET type = ?, county = ?, location_detail = ?, price_eur = ?, hours = ?, food_provided = ?,
                age_min = ?, age_max = ?, source_url = ?, source_type = 'curated_location_priority',
                status = 'approved', notes = ?, last_checked_at = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                camp["type"],
                camp["county"],
                camp["locationDetail"],
                camp["priceEur"],
                camp["hours"],
                camp["foodProvided"],
                camp["ageMin"],
                camp["ageMax"],
                camp["sourceUrl"],
                camp["notes"],
                now,
                now,
                existing[0],
            ),
        )
        return

    connection.execute(
        """
        INSERT INTO camps
        (name, type, county, location_detail, price_eur, hours, food_provided, age_min, age_max, source_url,
         source_type, status, notes, last_checked_at, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'curated_location_priority', 'approved', ?, ?, ?, ?)
        """,
        (
            camp["name"],
            camp["type"],
            camp["county"],
            camp["locationDetail"],
            camp["priceEur"],
            camp["hours"],
            camp["foodProvided"],
            camp["ageMin"],
            camp["ageMax"],
            camp["sourceUrl"],
            camp["notes"],
            now,
            now,
            now,
        ),
    )


def main():
    connection = sqlite3.connect(DB_PATH)
    ensure_location_column(connection)
    for camp in LOCATION_PRIORITY_CAMPS:
        upsert(connection, camp)
    connection.commit()
    print(f"Upserted {len(LOCATION_PRIORITY_CAMPS)} location-priority camps.")
    connection.close()


if __name__ == "__main__":
    main()
