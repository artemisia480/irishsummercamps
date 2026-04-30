import json
import sqlite3
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "camps.db"
MASTER_PATH = BASE_DIR / "master_overrides.json"


def upsert(connection, camp):
    now = datetime.utcnow().isoformat()
    existing = connection.execute("SELECT id FROM camps WHERE name = ?", (camp["name"],)).fetchone()

    if existing:
        connection.execute(
            """
            UPDATE camps
            SET type = ?, county = ?, location_detail = ?, price_eur = ?, hours = ?, extended_hours_note = ?,
                camp_weeks_text = ?, food_provided = ?, age_min = ?, age_max = ?, source_url = ?,
                source_type = 'master_override', status = 'approved', notes = ?, last_checked_at = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                camp.get("type") or "Summer camp listing",
                camp.get("county") or "Unknown",
                camp.get("locationDetail"),
                camp.get("priceEur"),
                camp.get("hours") or "Check source",
                camp.get("extendedHours"),
                camp.get("campWeeksText"),
                camp.get("foodProvided") or "unknown",
                camp.get("ageMin"),
                camp.get("ageMax"),
                camp.get("sourceUrl"),
                camp.get("notes") or "Applied from master_overrides.json",
                now,
                now,
                existing[0],
            ),
        )
        return

    connection.execute(
        """
        INSERT INTO camps
        (name, type, county, location_detail, price_eur, hours, extended_hours_note, camp_weeks_text, food_provided,
         age_min, age_max, source_url, source_type, status, notes, last_checked_at, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'master_override', 'approved', ?, ?, ?, ?)
        """,
        (
            camp["name"],
            camp.get("type") or "Summer camp listing",
            camp.get("county") or "Unknown",
            camp.get("locationDetail"),
            camp.get("priceEur"),
            camp.get("hours") or "Check source",
            camp.get("extendedHours"),
            camp.get("campWeeksText"),
            camp.get("foodProvided") or "unknown",
            camp.get("ageMin"),
            camp.get("ageMax"),
            camp.get("sourceUrl"),
            camp.get("notes") or "Applied from master_overrides.json",
            now,
            now,
            now,
        ),
    )


def main():
    if not MASTER_PATH.exists():
        print("master_overrides.json not found. Skipping.")
        return

    with open(MASTER_PATH, "r", encoding="utf-8") as file:
        payload = json.load(file)

    camps = payload.get("camps", [])
    reject_names = payload.get("rejectNames", [])

    connection = sqlite3.connect(DB_PATH)
    now = datetime.utcnow().isoformat()

    for camp in camps:
        if not camp.get("name"):
            continue
        upsert(connection, camp)

    for name in reject_names:
        connection.execute(
            "UPDATE camps SET status = 'rejected', updated_at = ? WHERE name = ?",
            (now, name),
        )

    connection.commit()
    connection.close()
    print(f"Master overrides applied. camps={len(camps)} rejectNames={len(reject_names)}")


if __name__ == "__main__":
    main()

