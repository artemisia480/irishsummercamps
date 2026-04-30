import sqlite3
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "camps.db"


REAL_CAMPS = [
    {
        "name": "Rusheen Bay Watersports Summer Camp",
        "type": "Watersports camp (windsurfing, kayaking, paddleboarding)",
        "county": "Galway",
        "priceEur": 200,
        "hours": "09:30-13:00 or 13:30-17:00",
        "foodProvided": "no",
        "ageMin": 8,
        "ageMax": 14,
        "sourceUrl": "https://www.rusheenbay.com/summer-camps",
        "notes": "Manual extraction from public page. 2nd/3rd sibling rate listed as EUR 180.",
    },
    {
        "name": "Rusheen Bay Teenage Adventure Camp",
        "type": "Teen watersports adventure camp",
        "county": "Galway",
        "priceEur": 200,
        "hours": "Check source page for exact session times",
        "foodProvided": "no",
        "ageMin": 12,
        "ageMax": 17,
        "sourceUrl": "https://www.rusheenbay.com/summer-camps",
        "notes": "Manual extraction from public page. Operator states camps run in late June.",
    },
    {
        "name": "Cork Acro Gymnastics Summer Camp",
        "type": "Gymnastics camp (junior/intermediate/advanced/senior weeks)",
        "county": "Cork",
        "priceEur": 95,
        "hours": "10:00-13:00 (some senior weeks listed longer)",
        "foodProvided": "no",
        "ageMin": 5,
        "ageMax": 17,
        "sourceUrl": "https://www.corkacro.com/summer-camps-2026.html",
        "notes": "Manual extraction from public page. EUR 90 for members, EUR 95 for non-members.",
    },
]


def upsert(connection, camp):
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
                source_url = ?, source_type = 'manual_public_web', status = 'pending_review',
                notes = ?, last_checked_at = ?, updated_at = ?
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
            (name, type, county, price_eur, hours, food_provided, age_min, age_max, source_url, source_type, status,
             notes, last_checked_at, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'manual_public_web', 'pending_review', ?, ?, ?, ?)
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
                camp["notes"],
                now,
                now,
                now,
            ),
        )


def main():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    for camp in REAL_CAMPS:
        upsert(connection, camp)
    connection.commit()
    pending = connection.execute(
        "SELECT COUNT(*) AS count FROM camps WHERE status = 'pending_review'"
    ).fetchone()["count"]
    connection.close()
    print(f"Imported {len(REAL_CAMPS)} real entries. Pending review total: {pending}")


if __name__ == "__main__":
    main()
