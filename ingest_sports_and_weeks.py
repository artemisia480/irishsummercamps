import sqlite3
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "camps.db"

SPORT_CAMPS = [
    {
        "name": "UCD AFC Soccer Summer Camp",
        "type": "Football (soccer) camp",
        "county": "Dublin",
        "locationDetail": "UCD AFC, Belfield, Dublin 4",
        "priceEur": 80,
        "hours": "10:00-15:00",
        "extendedHours": None,
        "campWeeksText": "2026-06-29|2026-07-06|2026-07-13|2026-07-20|2026-07-27|2026-08-03|2026-08-10|2026-08-17",
        "foodProvided": "no",
        "ageMin": 5,
        "ageMax": 14,
        "sourceUrl": "https://havefunkids.ie/event/summer-camp/811355-ucd-afcsummer-camp-2025/",
        "notes": "Weekly soccer camp dates listed on provider page.",
    },
    {
        "name": "Cul Camps (GAA)",
        "type": "GAA camp",
        "county": "Ireland (multi-location)",
        "locationDetail": "Club venues nationwide via booking portal",
        "priceEur": None,
        "hours": "Typically daytime camp hours",
        "extendedHours": None,
        "campWeeksText": "2026-06-29|2026-07-06|2026-07-13|2026-07-20|2026-07-27|2026-08-03|2026-08-10|2026-08-17",
        "foodProvided": "no",
        "ageMin": 6,
        "ageMax": 13,
        "sourceUrl": "https://www.kelloggsculcamps.gaa.ie/",
        "notes": "National GAA camps provider page.",
    },
]


def ensure_columns(connection):
    cols = {row[1] for row in connection.execute("PRAGMA table_info(camps)").fetchall()}
    if "location_detail" not in cols:
        connection.execute("ALTER TABLE camps ADD COLUMN location_detail TEXT")
    if "extended_hours_note" not in cols:
        connection.execute("ALTER TABLE camps ADD COLUMN extended_hours_note TEXT")
    if "camp_weeks_text" not in cols:
        connection.execute("ALTER TABLE camps ADD COLUMN camp_weeks_text TEXT")
    connection.commit()


def upsert(connection, camp):
    now = datetime.utcnow().isoformat()
    row = connection.execute("SELECT id FROM camps WHERE name = ?", (camp["name"],)).fetchone()
    if row:
        connection.execute(
            """
            UPDATE camps
            SET type=?, county=?, location_detail=?, price_eur=?, hours=?, extended_hours_note=?, camp_weeks_text=?,
                food_provided=?, age_min=?, age_max=?, source_url=?, source_type='curated_requested', status='approved',
                notes=?, last_checked_at=?, updated_at=?
            WHERE id=?
            """,
            (
                camp["type"],
                camp["county"],
                camp["locationDetail"],
                camp["priceEur"],
                camp["hours"],
                camp["extendedHours"],
                camp["campWeeksText"],
                camp["foodProvided"],
                camp["ageMin"],
                camp["ageMax"],
                camp["sourceUrl"],
                camp["notes"],
                now,
                now,
                row[0],
            ),
        )
    else:
        connection.execute(
            """
            INSERT INTO camps
            (name,type,county,location_detail,price_eur,hours,extended_hours_note,camp_weeks_text,food_provided,age_min,age_max,source_url,
             source_type,status,notes,last_checked_at,created_at,updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?, 'curated_requested','approved',?,?,?,?)
            """,
            (
                camp["name"],
                camp["type"],
                camp["county"],
                camp["locationDetail"],
                camp["priceEur"],
                camp["hours"],
                camp["extendedHours"],
                camp["campWeeksText"],
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


def set_weeks_for_existing(connection):
    now = datetime.utcnow().isoformat()
    updates = [
        ("Castle Park Swim Academy Multi Activity Camp", "2026-06-29|2026-07-06|2026-07-13|2026-07-20|2026-07-27|2026-08-03|2026-08-10"),
        ("Underdog Games Senior Camp (St Kilian's)", "2026-07-27|2026-08-03|2026-08-10"),
        ("Underdog Games Junior Camp (Cabra)", "2026-07-07|2026-07-13|2026-07-20"),
        ("We Love Science Summer Camp (Donnybrook Parish Centre)", "2026-07-06"),
        ("Dublin Zoo Summer Camp", "2026-07-21|2026-07-28|2026-08-04|2026-08-11"),
    ]
    for name, weeks in updates:
        connection.execute(
            "UPDATE camps SET camp_weeks_text=?, updated_at=? WHERE name=?",
            (weeks, now, name),
        )


def main():
    connection = sqlite3.connect(DB_PATH)
    ensure_columns(connection)
    for camp in SPORT_CAMPS:
        upsert(connection, camp)
    set_weeks_for_existing(connection)
    connection.commit()
    connection.close()
    print("Sports camps and week schedules updated.")


if __name__ == "__main__":
    main()
