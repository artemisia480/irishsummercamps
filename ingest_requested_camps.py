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
        "name": "Deuce Point Multisport Summer Camp (Dublin)",
        "type": "Multisport camp (tennis, table tennis and games)",
        "county": "Dublin",
        "locationDetail": "Harold's Cross National School, Castleknock College, and other Dublin venues by season",
        "priceEur": 80,
        "hours": "09:30-14:30",
        "extendedHours": None,
        "foodProvided": "unknown",
        "ageMin": 5,
        "ageMax": 11,
        "sourceUrl": "https://deucepoint.ie/",
        "notes": "Official Deuce Point site lists 2026 summer camps (Harold's Cross and other venues); price can vary by location/week.",
    },
    {
        "name": "Artzone Summer Art Camps (Dublin)",
        "type": "Art and design camp",
        "county": "Dublin",
        "locationDetail": "Dundrum, Rathfarnham, Lucan, Malahide and Glenageary venues",
        "priceEur": None,
        "hours": "10:00-13:00 or 14:00-17:00",
        "extendedHours": None,
        "foodProvided": "unknown",
        "ageMin": 5,
        "ageMax": 16,
        "sourceUrl": "https://www.artzone.ie/camps/art-summer-camps-children-dublin/",
        "notes": "Qualified art-teacher-led summer camps with multiple Dublin venues and age bands.",
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
        "name": "Stretch-n-Grow Summer Camp (Dublin)",
        "type": "Early years fitness and multisport camp",
        "county": "Dublin",
        "locationDetail": "Ballinteer, Dundrum, Firhouse, Sandymount and Sandyford (Rosemont School)",
        "priceEur": 110,
        "hours": "10:00-13:00",
        "extendedHours": None,
        "foodProvided": "unknown",
        "ageMin": 3,
        "ageMax": 6,
        "sourceUrl": "https://stretchngrow.ie/camps/",
        "notes": "Action-packed 3-hour camps; locations and schedules vary by holiday period.",
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
    {
        "name": "Leinster Tennis Performance Summer Camps (DCU & Bushy Park)",
        "type": "Performance tennis camp",
        "county": "Dublin",
        "locationDetail": "National Tennis Centre (DCU) and Bushy Park, Dublin",
        "priceEur": 220,
        "hours": "Typically 10:00-13:00 or 13:00-16:00 (camp dependent)",
        "extendedHours": None,
        "foodProvided": "unknown",
        "ageMin": 8,
        "ageMax": 15,
        "sourceUrl": "https://www.leinstertennis.ie/page/39471/Summer-Camps-2025",
        "notes": "Official Leinster Tennis page; some blocks are priced at EUR 200 or EUR 120.",
    },
    {
        "name": "West Wood Leopardstown Junior Tennis Camp",
        "type": "Junior tennis camp",
        "county": "Dublin",
        "locationDetail": "West Wood Tennis Centre, Leopardstown Racecourse, Foxrock, Dublin 18",
        "priceEur": 190,
        "hours": "09:00-12:00",
        "extendedHours": None,
        "foodProvided": "unknown",
        "ageMin": 6,
        "ageMax": 10,
        "sourceUrl": "https://westwood.ie/tennis-in-dublin/junior-tennis-camps/summer-tennis-camp-2025-at-leopardstown",
        "notes": "Early-bird and multi-week discounts available.",
    },
    {
        "name": "Ashbrook Tennis Club Junior Summer Camp",
        "type": "Junior tennis camp",
        "county": "Dublin",
        "locationDetail": "Ashbrook Tennis Club, Dublin",
        "priceEur": 170,
        "hours": "09:00-12:00 or 13:00-16:00",
        "extendedHours": None,
        "foodProvided": "unknown",
        "ageMin": 6,
        "ageMax": None,
        "sourceUrl": "https://www.ashbrooktennisclub.ie/summercamp2024",
        "notes": "Member and non-member rates differ; reduced rates for bank-holiday week.",
    },
    {
        "name": "Enniskerry Tennis Club Summer Camps",
        "type": "Junior tennis camp",
        "county": "Wicklow",
        "locationDetail": "Enniskerry Tennis Club, Enniskerry, Co. Wicklow (A98 DW96)",
        "priceEur": 125,
        "hours": "10:00-13:00",
        "extendedHours": None,
        "foodProvided": "unknown",
        "ageMin": 6,
        "ageMax": 13,
        "sourceUrl": "https://jsta.ie/Enniskerry_Summer_Tennis_Camp.html",
        "notes": "Multiple weekly camps across July and August.",
    },
    {
        "name": "Growing Roots Forest Summer Camp (Red Rock)",
        "type": "Forest school and outdoor nature camp",
        "county": "Dublin",
        "locationDetail": "Red Rock, Sutton, Co. Dublin",
        "priceEur": 150,
        "hours": "09:00-14:00",
        "extendedHours": None,
        "foodProvided": "unknown",
        "ageMin": 4,
        "ageMax": 12,
        "sourceUrl": "https://www.edarabia.com/best-summer-camps-dublin/",
        "notes": "Sourced from Edarabia directory listing for Growing Roots at Red Rock; verify dates with provider.",
    },
    {
        "name": "Skillz Camp at St Raphaela's School",
        "type": "Hockey and football skills camp",
        "county": "Dublin",
        "locationDetail": "St Raphaela's School, Stillorgan, Dublin",
        "priceEur": 130,
        "hours": "Varies by week; check booking page",
        "extendedHours": None,
        "foodProvided": "unknown",
        "ageMin": 8,
        "ageMax": 17,
        "sourceUrl": "https://skillzcamps.com/",
        "notes": "Official Skillz site and related camp listings reference St Raphaela's location.",
    },
    {
        "name": "Just 4 Fun Kids Camp (Multi-location)",
        "type": "Multi-activity camp",
        "county": "Multi-county",
        "locationDetail": "Multiple locations (check provider map for current venues)",
        "priceEur": None,
        "hours": "Varies by venue and week",
        "extendedHours": None,
        "foodProvided": "unknown",
        "ageMin": 4,
        "ageMax": 12,
        "sourceUrl": "https://just4funkidscamp.com/find-a-summer-camp/",
        "notes": "Provider runs camps across multiple counties; check listing page for exact local dates.",
    },
    {
        "name": "Horizons Montessori Summer Camp (Terenure)",
        "type": "Multi-activity summer camp",
        "county": "Dublin",
        "locationDetail": "Terenure College, Terenure, Dublin 6W",
        "priceEur": 240,
        "hours": "Half day 09:00-14:00; full day 08:30-18:00",
        "extendedHours": None,
        "foodProvided": "yes",
        "ageMin": 5,
        "ageMax": 10,
        "sourceUrl": "https://horizonsmontessori.ie/terenure-college-dublin-6-w/summer-camps/",
        "notes": "Full-day campers receive hot dinner and snack (Little Dinners); packed lunch also required for daytime break per FAQ. Summer 2026 paused for renovations—confirm return dates on site.",
    },
    {
        "name": "Horizons Summer Camp (Mullingar)",
        "type": "Multi-sport and activity day camp",
        "county": "Westmeath",
        "locationDetail": "Loreto College, Mullingar, Co. Westmeath",
        "priceEur": 190,
        "hours": "09:30-16:00",
        "extendedHours": None,
        "foodProvided": "unknown",
        "ageMin": 8,
        "ageMax": 14,
        "sourceUrl": "https://horizonssummercamp.com/",
        "notes": "2026 camp week Mon 29 Jun–Fri 3 Jul on official site. Fee includes activities, tours, buses, insurance; confirm meals with organiser.",
    },
    {
        "name": "We Love Science Summer Camp (Donnybrook Parish Centre)",
        "type": "Science and STEM summer camp",
        "county": "Dublin",
        "locationDetail": "Donnybrook Parish Centre, Donnybrook, Dublin 4",
        "priceEur": None,
        "hours": "Check source for daily timetable",
        "extendedHours": None,
        "foodProvided": "unknown",
        "ageMin": None,
        "ageMax": None,
        "sourceUrl": "https://summercamps.carrd.co/",
        "notes": "Provider booking/info page shared in chat. Camp week currently tracked as 2026-07-06 in sports-and-weeks updater.",
    },
    {
        "name": "PlayAct Drama Camps (Dublin)",
        "type": "Drama and theatre camp",
        "county": "Dublin",
        "locationDetail": "Inchicore, Terenure, Sandymount and Dun Laoghaire, Dublin",
        "priceEur": None,
        "hours": "Camp times vary by season and location",
        "extendedHours": None,
        "foodProvided": "unknown",
        "ageMin": 4,
        "ageMax": 16,
        "sourceUrl": "https://playact.ie/drama-camps/",
        "notes": "PlayAct lists drama camps for ages 4-16 with multiple Dublin locations; check booking page for current dates/times.",
    },
    {
        "name": "Irish National Sailing & Powerboat School Summer Camp",
        "type": "Sailing and watersports camp",
        "county": "Dublin",
        "locationDetail": "West Pier, Dun Laoghaire, Co. Dublin",
        "priceEur": 285,
        "hours": "09:00-17:00",
        "extendedHours": "Drop-off from 08:30",
        "foodProvided": "unknown",
        "ageMin": 7,
        "ageMax": 17,
        "sourceUrl": "https://courses.inss.ie/product/summer-courses-7-17-lp/",
        "notes": "INSS summer sailing camps run Monday-Friday; 5-day EUR 285 and 4-day bank-holiday weeks EUR 230.",
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
