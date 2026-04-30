import sqlite3
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "camps.db"


def upsert(connection, camp):
    now = datetime.utcnow().isoformat()
    existing = connection.execute("SELECT id FROM camps WHERE name = ?", (camp["name"],)).fetchone()
    if existing:
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
                existing[0],
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


def reject_extra_rows_same_name(connection, name, now_iso):
    """Keep lowest id; reject other approved rows with identical name."""
    rows = connection.execute(
        "SELECT id FROM camps WHERE name = ? AND status = 'approved' ORDER BY id ASC",
        (name,),
    ).fetchall()
    if len(rows) <= 1:
        return 0
    rejected = 0
    for row in rows[1:]:
        connection.execute(
            "UPDATE camps SET status = 'rejected', updated_at = ? WHERE id = ?",
            (now_iso, row[0]),
        )
        rejected += 1
    return rejected


def main():
    connection = sqlite3.connect(DB_PATH)
    now = datetime.utcnow().isoformat()

    # Remove intentionally hidden duplicate provider entry.
    connection.execute(
        "UPDATE camps SET status='rejected', updated_at=? WHERE name='SwimCamp Summer Swimming Camp (Castle Park School)'",
        (now,),
    )

    # Dedupe same-title rows (e.g. scrape + curated both inserted).
    reject_extra_rows_same_name(
        connection,
        "Bricks 4 Kidz South County Dublin - Firhouse",
        now,
    )

    # Scraped generic page-title rows that duplicate curated entries.
    noisy_scraped_titles = [
        "Summer Camps 2026",
        "Dublin Summer Camps | Whizzkids.ie",
        "Summer Camps(In Person) - KidsComp - Coding classes for kids",
        "Summer Camps | STEAM Camps | Camps for kids - Designer Minds",
        "Summer Day Camps for Kids Ireland - The School of Irish Archaeology",
        "Summer Camps Galway - Rusheen Bay Watersports",
        "Bricks 4 Kidz South County Dublin - Firhouse",
        "PSA Rugby Academies Summer Camps",
        "Summer Swim Camps | Kilkee Waterworld",
        "Summer Camps Dublin - Inside Out",
    ]
    for title in noisy_scraped_titles:
        connection.execute(
            "UPDATE camps SET status='rejected', updated_at=? WHERE name=?",
            (now, title),
        )

    # Ensure specific overrides added later in chat exist in production.
    camps = [
        {
            "name": "Underdog Games Junior Camp (Cabra)",
            "type": "Team games and multi-activity camp for younger children",
            "county": "Dublin",
            "locationDetail": "Christ the King Girls National School, Annaly Road, Cabra, Dublin 7, D07 DC56",
            "priceEur": None,
            "hours": "09:00-14:00",
            "extendedHours": "Drop-off from 08:45 and collection from 13:45",
            "campWeeksText": "2026-07-07|2026-07-13|2026-07-20",
            "foodProvided": "no",
            "ageMin": 3,
            "ageMax": 5,
            "sourceUrl": "https://www.theunderdoggames.ie/juniorcamps",
            "notes": "Updated from official junior camps page.",
        },
        {
            "name": "Underdog Games Senior Camp (St Kilian's)",
            "type": "Team games and multi-activity sports camp",
            "county": "Dublin",
            "locationDetail": "St. Kilian's German School, Roebuck Rd, Clonskeagh, Dublin 14, D14 P7F2",
            "priceEur": None,
            "hours": "09:00-14:00",
            "extendedHours": "Drop-off from 08:45 and collection from 13:45",
            "campWeeksText": "2026-07-27|2026-08-03|2026-08-10",
            "foodProvided": "no",
            "ageMin": 5,
            "ageMax": 12,
            "sourceUrl": "https://www.theunderdoggames.ie/seniorcampsdublin14",
            "notes": "Curated from official Underdog Games page with St Kilian's venue dates.",
        },
        {
            "name": "Sherpa Kids Rathfarnham Holiday HQ Summer Camp",
            "type": "Multi-activity holiday camp (sports, STEM, arts)",
            "county": "Ireland (multi-location)",
            "locationDetail": "Rathfarnham ETNS plus 50+ locations nationwide via Holiday HQ",
            "priceEur": None,
            "hours": "Day schedule varies by week",
            "extendedHours": "Extended hours up to 08:30-17:30 (site dependent)",
            "campWeeksText": None,
            "foodProvided": "unknown",
            "ageMin": 4,
            "ageMax": 13,
            "sourceUrl": "https://www.sherpakids.ie/school-holidays/holiday-hq-summer-camp-2026/",
            "notes": "Updated from official Holiday HQ page.",
        },
        {
            "name": "RoboticsAI Club Summer Camps",
            "type": "Robotics, AI and coding camp",
            "county": "Ireland (multi-location)",
            "locationDetail": "Multiple school locations across Dublin and nationwide via provider booking",
            "priceEur": None,
            "hours": "Session times vary by location/week",
            "extendedHours": "Not listed on public page",
            "campWeeksText": None,
            "foodProvided": "unknown",
            "ageMin": 4,
            "ageMax": 12,
            "sourceUrl": "https://embed.exoclass.com/en/embed/provider/736809ef-680e-4d35-b447-3b3ba478948a/group-management?sort=start_date&activity_type=camp",
            "notes": "Official provider page with direct camp registration link.",
        },
        {
            "name": "Lets Go Multi-Activity Summer Camps (Dublin & Nationwide)",
            "type": "Summer camp listing",
            "county": "Dublin",
            "locationDetail": "Multiple Dublin venues incl. Ballinteer, Ballsbridge, Blackrock, Booterstown, Castleknock, Firhouse, Raheny, Sandyford, Sutton, Swords, Terenure, Whitehall",
            "priceEur": 132,
            "hours": "09:30-15:30",
            "extendedHours": None,
            "campWeeksText": None,
            "foodProvided": "no",
            "ageMin": None,
            "ageMax": None,
            "sourceUrl": "https://www.letsgo.ie/camps/dublin/",
            "notes": "Updated from official Lets Go Dublin camps page; provider also runs nationwide camps.",
        },
        {
            "name": "Basketball Ireland National Camps (3x3 & 5v5)",
            "type": "Basketball camp (residential)",
            "county": "Kildare",
            "locationDetail": "Clongowes Wood College, Co. Kildare",
            "priceEur": 700,
            "hours": "Residential schedule varies by camp week",
            "extendedHours": None,
            "campWeeksText": "2026-06-29|2026-07-05",
            "foodProvided": "yes",
            "ageMin": 12,
            "ageMax": 17,
            "sourceUrl": "http://basketballireland.ie/nationalcamp",
            "notes": "Official Basketball Ireland national camps page.",
        },
        {
            "name": "Junior Songschool Summer Camp (NCH)",
            "type": "Music songwriting and performance camp",
            "county": "Dublin",
            "locationDetail": "National Concert Hall, The Studio, Dublin",
            "priceEur": 112.5,
            "hours": "10:00-14:00",
            "extendedHours": None,
            "campWeeksText": "2026-07-06",
            "foodProvided": "no",
            "ageMin": 8,
            "ageMax": 12,
            "sourceUrl": "https://www.nch.ie/all-events-listing/junior-song-school-summer-camp-jul26/",
            "notes": "Presented by NCH with CreateSchool.",
        },
        {
            "name": "Rockjam Summer Camps",
            "type": "Music band and performance camp",
            "county": "Ireland (multi-location)",
            "locationDetail": "Sandyford, Milltown, Monkstown, Blanchardstown (provider venues)",
            "priceEur": None,
            "hours": "Varies by venue/week",
            "extendedHours": None,
            "campWeeksText": None,
            "foodProvided": "unknown",
            "ageMin": 8,
            "ageMax": 17,
            "sourceUrl": "https://www.rockjam.ie/post/rockjam-summer-camps-2026-now-open-for-bookings",
            "notes": "Provider lists multiple Dublin locations.",
        },
        {
            "name": "Dublin Youth Choir Summer Sing (RIAM)",
            "type": "Music and choir camp",
            "county": "Dublin",
            "locationDetail": "Royal Irish Academy of Music, Westland Row, Dublin",
            "priceEur": 190,
            "hours": "10:00-16:00",
            "extendedHours": "Early supervised activities from 09:00",
            "campWeeksText": "2026-06-29",
            "foodProvided": "no",
            "ageMin": 9,
            "ageMax": 14,
            "sourceUrl": "https://www.riam.ie/short-courses/dublin-youth-choirs-summer-sing",
            "notes": "Includes optional early supervised drop-off window.",
        },
    ]

    for camp in camps:
        upsert(connection, camp)

    # Normalize castle park details discovered later.
    connection.execute(
        """
        UPDATE camps
        SET food_provided='yes',
            notes='Hot lunch and snack included per source page.',
            updated_at=?
        WHERE name='Castle Park Swim Academy Multi Activity Camp'
        """,
        (now,),
    )

    connection.commit()
    connection.close()
    print("Live overrides synced.")


if __name__ == "__main__":
    main()
