import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

BASE_DIR = Path(__file__).parent
MASTER_PATH = BASE_DIR / "master_overrides.json"
DEFAULT_API_URL = "https://web-production-d5e24.up.railway.app/api/camps"


def normalize_county_value(raw_county):
    county = (raw_county or "").strip()
    if not county:
        return "Dublin"

    lowered = county.lower()
    if (
        lowered in {"unknown", "unknown county", "multi-county", "ireland (multi-location)"}
        or "multi-location" in lowered
        or "multi county" in lowered
        or lowered.startswith("ireland")
    ):
        return "Dublin"
    return county


def camp_to_override(camp):
    weeks = camp.get("campWeeks") or []
    camp_weeks_text = "|".join(weeks) if isinstance(weeks, list) and weeks else None
    return {
        "name": camp.get("name"),
        "type": camp.get("type"),
        "county": normalize_county_value(camp.get("county")),
        "locationDetail": camp.get("locationDetail"),
        "priceEur": camp.get("priceEur"),
        "hours": camp.get("hours"),
        "extendedHours": camp.get("extendedHours"),
        "campWeeksText": camp_weeks_text,
        "foodProvided": (
            "yes" if camp.get("foodProvided") is True else "no" if camp.get("foodProvided") is False else "unknown"
        ),
        "ageMin": camp.get("ageMin"),
        "ageMax": camp.get("ageMax"),
        "sourceUrl": camp.get("sourceUrl"),
        "notes": camp.get("notes") or "Captured from approved live API snapshot.",
    }


def main():
    api_url = DEFAULT_API_URL
    with urlopen(api_url) as response:
        camps = json.loads(response.read().decode("utf-8"))

    overrides = [camp_to_override(c) for c in camps if c.get("name")]
    overrides.sort(key=lambda item: item["name"].lower())

    payload = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "sourceApi": api_url,
        "camps": overrides,
        "rejectNames": [],
    }

    with open(MASTER_PATH, "w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)

    print(f"Wrote {len(overrides)} camps to {MASTER_PATH.name}")


if __name__ == "__main__":
    main()

