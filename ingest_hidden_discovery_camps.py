import sqlite3
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "camps.db"

DISCOVERED_CAMPS = [
    {
        "name": "Oysterhaven Start Sailing Camp (Level 1)",
        "type": "Sailing and watersports camp",
        "county": "Cork",
        "locationDetail": "Oysterhaven Centre, Kinsale, Co. Cork",
        "priceEur": 340,
        "hours": "09:30-15:30",
        "foodProvided": "no",
        "ageMin": 11,
        "ageMax": 17,
        "sourceUrl": "https://www.oysterhaven.com/activity/start-sailing--level-1-11yrs/?d=20%2F07%2F2026",
        "notes": "Discovered via broad category sweep.",
    },
    {
        "name": "Oysterhaven Dolphins Camp",
        "type": "Junior sailing and adventure camp",
        "county": "Cork",
        "locationDetail": "Oysterhaven Centre, Kinsale, Co. Cork",
        "priceEur": 295,
        "hours": "10:00-16:00",
        "foodProvided": "no",
        "ageMin": 7,
        "ageMax": 7,
        "sourceUrl": "https://www.oysterhaven.com/activity/dolphins-7-yrs/?d=29%2F06%2F2026",
        "notes": "Weekly camp format with age-specific sessions.",
    },
    {
        "name": "Carrickmines Pony Camp",
        "type": "Horse riding camp",
        "county": "Dublin",
        "locationDetail": "Carrickmines Equestrian Centre, Dublin",
        "priceEur": 310,
        "hours": "10:00-15:00",
        "foodProvided": "no",
        "ageMin": 6,
        "ageMax": 17,
        "sourceUrl": "https://www.carrickminesequestrian.ie/lesson-sign-up/p/summer-pony-camp",
        "notes": "Booking confirmed once payment is received.",
    },
    {
        "name": "Donegal Equestrian Pony Camps",
        "type": "Horse riding and stable skills camp",
        "county": "Donegal",
        "locationDetail": "Donegal Equestrian Centre, Bundoran, Co. Donegal",
        "priceEur": 270,
        "hours": "09:30-12:30 or 13:30-16:30",
        "foodProvided": "no",
        "ageMin": 7,
        "ageMax": 17,
        "sourceUrl": "https://donegalequestriancentre.com/pony-camps/",
        "notes": "Small-group camps with beginner and advanced tracks.",
    },
    {
        "name": "Curtain Call Summer Camp (Santry)",
        "type": "Performing arts, drama, singing and dance camp",
        "county": "Dublin",
        "locationDetail": "Santry Community Resource Centre, Dublin 9",
        "priceEur": 120,
        "hours": "10:00-14:00",
        "foodProvided": "no",
        "ageMin": 5,
        "ageMax": 16,
        "sourceUrl": "https://www.curtaincallstageschool.ie/summer-camps",
        "notes": "Annual summer camp with musical theatre focus.",
    },
    {
        "name": "Cecilian Theatre Arts Sunshine Summer Camp",
        "type": "Drama and dance camp",
        "county": "Dublin",
        "locationDetail": "Scoil Bhride Buachaili, Blanchardstown, Dublin 15",
        "priceEur": 120,
        "hours": "09:30-13:30",
        "foodProvided": "no",
        "ageMin": 4,
        "ageMax": 11,
        "sourceUrl": "https://ceciliantheatrearts.ie/sunshine-summer-camp/",
        "notes": "Sibling discount listed on source page.",
    },
    {
        "name": "Brigit's Garden Nature Summer Camps",
        "type": "Nature, bushcraft and outdoor skills camp",
        "county": "Galway",
        "locationDetail": "Brigit's Garden, Roscahill, Co. Galway",
        "priceEur": None,
        "hours": "10:00-13:30",
        "foodProvided": "no",
        "ageMin": 5,
        "ageMax": 12,
        "sourceUrl": "https://brigitsgarden.ie/class/summer-camps/",
        "notes": "Forest-school inspired outdoor camps.",
    },
    {
        "name": "Larch Hill Adventure Camp",
        "type": "Outdoor adventure camp",
        "county": "Dublin",
        "locationDetail": "Larch Hill, Dublin (Scouting Ireland)",
        "priceEur": 200,
        "hours": "09:00-16:00",
        "foodProvided": "unknown",
        "ageMin": 6,
        "ageMax": 14,
        "sourceUrl": "https://www.scouts.ie/post/larch-hill-adventure-camp---summer-2026",
        "notes": "Early bird pricing available on source page.",
    },
    {
        "name": "Canoe Centre Summer Adventure Camp",
        "type": "Rafting, paddling and bushcraft camp",
        "county": "Dublin",
        "locationDetail": "Canoe Centre, Dublin",
        "priceEur": 249,
        "hours": "10:00-15:00",
        "foodProvided": "no",
        "ageMin": 11,
        "ageMax": 16,
        "sourceUrl": "https://rafting.ie/product/camps/",
        "notes": "5-day adventure camp with water and land activities.",
    },
    {
        "name": "TechKidz Summer Camps",
        "type": "Technology, coding and engineering camp",
        "county": "Dublin",
        "locationDetail": "Multiple venues nationwide (Dublin/Cork/Galway etc.)",
        "priceEur": None,
        "hours": "Varies by venue",
        "foodProvided": "unknown",
        "ageMin": 7,
        "ageMax": 14,
        "sourceUrl": "https://www.techkidz.ie/summer-camps/",
        "notes": "Nationwide STEM/tech camps with venue selector.",
    },
    {
        "name": "Crystal Maze Summer Camp",
        "type": "Adventure and challenge camp",
        "county": "Meath",
        "locationDetail": "The Crystal Maze, Kilmainhamwood, Co. Meath",
        "priceEur": 125,
        "hours": "Check source session times",
        "foodProvided": "unknown",
        "ageMin": 6,
        "ageMax": 14,
        "sourceUrl": "https://www.crystalmaze.ie/service-page/crystal-maze-summer-camp-2026",
        "notes": "Includes transfer options from multiple towns.",
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
                age_min = ?, age_max = ?, source_url = ?, source_type = 'hidden_discovery_curated',
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
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'hidden_discovery_curated', 'approved', ?, ?, ?, ?)
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
    for camp in DISCOVERED_CAMPS:
        upsert(connection, camp)
    connection.commit()
    print(f"Upserted {len(DISCOVERED_CAMPS)} hidden/niche discovered camps.")
    connection.close()


if __name__ == "__main__":
    main()
