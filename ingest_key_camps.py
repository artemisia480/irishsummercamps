import sqlite3
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "camps.db"

KEY_CAMPS = [
    {
        "name": "Bricks 4 Kidz Summer Camps (Ireland)",
        "type": "LEGO STEM camp",
        "county": "Dublin",
        "locationDetail": "Multiple locations across Ireland",
        "priceEur": None,
        "hours": "Varies by location/week",
        "foodProvided": "unknown",
        "ageMin": 5,
        "ageMax": 13,
        "sourceUrl": "https://bricks4kidz.ie/our-programs/camps/",
        "notes": "National LEGO/engineering camps. Check local branch pages for dates and booking.",
    },
    {
        "name": "KidsComp LEGO Robotics & Coding Summer Camp",
        "type": "LEGO robotics and coding camp",
        "county": "Dublin",
        "locationDetail": "Community centres across Dublin and Cork",
        "priceEur": 150,
        "hours": "10:00-13:00",
        "foodProvided": "no",
        "ageMin": 5,
        "ageMax": 10,
        "sourceUrl": "https://www.kidscomp.ie/product/summer-camps-in-person/",
        "notes": "Community-centre based camps in Dublin and Cork locations.",
    },
    {
        "name": "Designer Minds STEAM Summer Camps",
        "type": "STEAM, LEGO and robotics camp",
        "county": "Dublin",
        "locationDetail": "County/town venues selected on booking page",
        "priceEur": None,
        "hours": "Typically 09:00-13:00 (some 14:00-18:00)",
        "foodProvided": "unknown",
        "ageMin": 6,
        "ageMax": 12,
        "sourceUrl": "https://designerminds.ie/camps",
        "notes": "County/town-specific booking flow on source site.",
    },
    {
        "name": "Castle Park Swim Academy Multi Activity Camp",
        "type": "Multi-activity with daily swim, gymnastics, dance and sports",
        "county": "Dublin",
        "locationDetail": "Castle Park School Swim Academy, Dalkey",
        "priceEur": 180,
        "hours": "09:30-15:00",
        "foodProvided": "unknown",
        "ageMin": 4,
        "ageMax": 12,
        "sourceUrl": "https://castleparkschool.ie/swim-academy/camps/",
        "notes": "Dalkey camp with optional extended care.",
    },
    {
        "name": "SwimCamp Summer Swimming Camp (Castle Park School)",
        "type": "Swimming intensive camp",
        "county": "Dublin",
        "locationDetail": "Castle Park School Swimming Pool, Dalkey",
        "priceEur": None,
        "hours": "45-minute sessions (dates vary)",
        "foodProvided": "no",
        "ageMin": 4,
        "ageMax": 17,
        "sourceUrl": "https://www.swimcamp.ie/summer-swimming-camp-dublin",
        "notes": "Runs at Castle Park School pool in Dalkey.",
    },
    {
        "name": "Cork Acro Gymnastics Summer Camp",
        "type": "Gymnastics camp",
        "county": "Cork",
        "locationDetail": "Cork Acro Gymnastics Club, Cork",
        "priceEur": 95,
        "hours": "10:00-13:00 (some senior weeks longer)",
        "foodProvided": "no",
        "ageMin": 5,
        "ageMax": 17,
        "sourceUrl": "https://www.corkacro.com/summer-camps-2026.html",
        "notes": "Member and non-member pricing listed on source site.",
    },
    {
        "name": "Odette School of Ballet Summer Dance Camp",
        "type": "Dance camp (ballet, lyrical, hip hop, jazz)",
        "county": "Dublin",
        "locationDetail": "Baldoyle Racecourse Community Centre, Dublin 13",
        "priceEur": 120,
        "hours": "09:30-13:30",
        "foodProvided": "no",
        "ageMin": 4,
        "ageMax": 17,
        "sourceUrl": "https://www.theodetteschoolofballet.ie/summer-camp-2026.php",
        "notes": "Held in Baldoyle Racecourse Community Centre.",
    },
]


def upsert(connection, camp):
    now = datetime.utcnow().isoformat()
    existing = connection.execute(
        "SELECT id FROM camps WHERE name = ?",
        (camp["name"],),
    ).fetchone()

    if existing:
        connection.execute(
            """
            UPDATE camps
            SET type = ?, county = ?, location_detail = ?, price_eur = ?, hours = ?, food_provided = ?, age_min = ?, age_max = ?,
                source_url = ?, source_type = 'curated_key_camps', status = 'approved',
                notes = ?, last_checked_at = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                camp["type"],
                camp["county"],
                camp.get("locationDetail"),
                camp["priceEur"],
                camp["hours"],
                camp["foodProvided"],
                camp["ageMin"],
                camp["ageMax"],
                camp["sourceUrl"],
                camp["notes"],
                now,
                now,
                existing["id"],
            ),
        )
    else:
        connection.execute(
            """
            INSERT INTO camps
            (name, type, county, location_detail, price_eur, hours, food_provided, age_min, age_max, source_url, source_type, status,
             notes, last_checked_at, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'curated_key_camps', 'approved', ?, ?, ?, ?)
            """,
            (
                camp["name"],
                camp["type"],
                camp["county"],
                camp.get("locationDetail"),
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
    connection.row_factory = sqlite3.Row
    for camp in KEY_CAMPS:
        upsert(connection, camp)
    connection.commit()
    count = connection.execute("SELECT COUNT(*) AS count FROM camps").fetchone()["count"]
    connection.close()
    print(f"Upserted {len(KEY_CAMPS)} key camps. Total records: {count}")


if __name__ == "__main__":
    main()
