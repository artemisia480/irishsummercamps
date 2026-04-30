import sqlite3
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "camps.db"

REQUESTED_CAMPS = [
    {
        "name": "Dublin Zoo Summer Camp",
        "type": "Wildlife and conservation camp",
        "county": "Dublin",
        "locationDetail": "Dublin Zoo, Phoenix Park, Dublin 8",
        "priceEur": 168,
        "hours": "10:00-14:30",
        "extendedHours": None,
        "foodProvided": "unknown",
        "ageMin": 7,
        "ageMax": 12,
        "sourceUrl": "https://www.dublinzoo.ie/conservation-education/summer-camps/",
        "notes": "Pricing can differ for annual pass holders.",
    },
    {
        "name": "School of Irish Archaeology Summer Camps",
        "type": "Archaeology and history camp",
        "county": "Dublin",
        "locationDetail": "Multiple Dublin venues (Sandyford, Malahide, Dalkey, Drumcondra, etc.)",
        "priceEur": 160,
        "hours": "10:00-15:00",
        "extendedHours": None,
        "foodProvided": "no",
        "ageMin": 7,
        "ageMax": 12,
        "sourceUrl": "https://sia.ie/summer-day-camps-for-kids-ireland/",
        "notes": "Range includes one-day and three-day options from source.",
    },
    {
        "name": "Airfield Experience Summer Camp",
        "type": "Farm, food and sustainability camp",
        "county": "Dublin",
        "locationDetail": "Airfield Estate, Dundrum, Dublin 14",
        "priceEur": 300,
        "hours": "Day camp hours vary by session",
        "extendedHours": None,
        "foodProvided": "unknown",
        "ageMin": 7,
        "ageMax": 14,
        "sourceUrl": "https://www.airfield.ie/events/young-chef-camp/",
        "notes": "Annual members discount shown on source page.",
    },
    {
        "name": "Alive Outside Summer Camp Rathgar (The High School)",
        "type": "Outdoor adventure and multi-activity camp",
        "county": "Dublin",
        "locationDetail": "The High School, Rathgar, Dublin 6",
        "priceEur": 182,
        "hours": "09:00-15:00",
        "extendedHours": None,
        "foodProvided": "no",
        "ageMin": 7,
        "ageMax": 13,
        "sourceUrl": "https://www.aliveoutside.ie/activity-package/summer-camp-thehighschool/",
        "notes": "Source lists 4 camp weeks in July and August 2026.",
    },
    {
        "name": "Alive Outside Summer Camp Swords (Colaiste Choilm)",
        "type": "Outdoor adventure and multi-activity camp",
        "county": "Dublin",
        "locationDetail": "Colaiste Choilm, Swords, Dublin",
        "priceEur": None,
        "hours": "Check source page for session times",
        "extendedHours": None,
        "foodProvided": "unknown",
        "ageMin": 7,
        "ageMax": 13,
        "sourceUrl": "https://www.aliveoutside.ie/summer-camps-dublin-wicklow-2026-alive-outside-summer-camps/",
        "notes": "Swords location listed as a new 2026 venue.",
    },
    {
        "name": "Alive Outside Summer Camp Grangegorman (TUD)",
        "type": "Outdoor adventure and multi-activity camp",
        "county": "Dublin",
        "locationDetail": "TU Dublin Grangegorman, Dublin 7",
        "priceEur": None,
        "hours": "Check source page for session times",
        "extendedHours": None,
        "foodProvided": "unknown",
        "ageMin": 7,
        "ageMax": 13,
        "sourceUrl": "https://www.aliveoutside.ie/summer-camps-dublin-wicklow-2026-alive-outside-summer-camps/",
        "notes": "Grangegorman location listed as a new 2026 venue.",
    },
    {
        "name": "Alive Outside Summer Camp Bray (Killruddery)",
        "type": "Outdoor adventure and multi-activity camp",
        "county": "Wicklow",
        "locationDetail": "Killruddery Estate, Bray, Co. Wicklow",
        "priceEur": 177,
        "hours": "09:00-15:00",
        "extendedHours": None,
        "foodProvided": "no",
        "ageMin": 7,
        "ageMax": 13,
        "sourceUrl": "https://www.aliveoutside.ie/activity-package/summer-camp-killruddery/",
        "notes": "Source lists multiple summer weeks across late June to late August.",
    },
    {
        "name": "Life Skills Academy Excellence Camp (Blackrock College)",
        "type": "Life skills and multi-activity camp",
        "county": "Dublin",
        "locationDetail": "Blackrock College, Dublin",
        "priceEur": 325,
        "hours": "08:50-16:00",
        "extendedHours": "Early drop-off from 08:30 included",
        "foodProvided": "unknown",
        "ageMin": 6,
        "ageMax": 14,
        "sourceUrl": "https://lifeskillsacademy.ie/pages/summer-camps",
        "notes": "Official source lists summer week at Blackrock College.",
    },
]


def ensure_columns(connection):
    cols = {row[1] for row in connection.execute("PRAGMA table_info(camps)").fetchall()}
    if "location_detail" not in cols:
        connection.execute("ALTER TABLE camps ADD COLUMN location_detail TEXT")
    if "extended_hours_note" not in cols:
        connection.execute("ALTER TABLE camps ADD COLUMN extended_hours_note TEXT")
    connection.commit()


def upsert(connection, camp):
    now = datetime.utcnow().isoformat()
    existing = connection.execute("SELECT id FROM camps WHERE name = ?", (camp["name"],)).fetchone()
    if existing:
        connection.execute(
            """
            UPDATE camps
            SET type = ?, county = ?, location_detail = ?, price_eur = ?, hours = ?, extended_hours_note = ?,
                food_provided = ?, age_min = ?, age_max = ?, source_url = ?, source_type = 'curated_requested',
                status = 'approved', notes = ?, last_checked_at = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                camp["type"],
                camp["county"],
                camp["locationDetail"],
                camp["priceEur"],
                camp["hours"],
                camp["extendedHours"],
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
        (name, type, county, location_detail, price_eur, hours, extended_hours_note, food_provided, age_min, age_max, source_url,
         source_type, status, notes, last_checked_at, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'curated_requested', 'approved', ?, ?, ?, ?)
        """,
        (
            camp["name"],
            camp["type"],
            camp["county"],
            camp["locationDetail"],
            camp["priceEur"],
            camp["hours"],
            camp["extendedHours"],
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


def update_extended_hours_facts(connection):
    now = datetime.utcnow().isoformat()
    updates = [
        (
            "Castle Park Swim Academy Multi Activity Camp",
            "Extended care 08:15-09:30 and 15:00-17:00 for extra fee",
        ),
        (
            "Underdog Games Senior Camp (St Kilian's)",
            "Drop-off from 08:45 and collection from 13:45",
        ),
    ]
    for name, note in updates:
        connection.execute(
            "UPDATE camps SET extended_hours_note = ?, updated_at = ? WHERE name = ?",
            (note, now, name),
        )


def main():
    connection = sqlite3.connect(DB_PATH)
    ensure_columns(connection)
    for camp in REQUESTED_CAMPS:
        upsert(connection, camp)
    update_extended_hours_facts(connection)
    connection.commit()
    connection.close()
    print(f"Upserted {len(REQUESTED_CAMPS)} requested camps and updated extended-hours facts.")


if __name__ == "__main__":
    main()
