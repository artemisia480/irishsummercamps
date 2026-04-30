# Ireland Summer Camps (Live Database Starter)

This project now includes:

- public camp listings from a SQLite database
- filter UI (county, price, age, food, hours)
- public submission form for new camps
- moderation workflow (`pending_review` -> `approved`/`rejected`)
- legal-safe scraper scaffold that checks `robots.txt` before fetching

## 1) Install dependencies

```bash
python -m pip install -r requirements.txt
```

## 2) Run the web app

```bash
python app.py
```

Open: `http://127.0.0.1:5000`

On first run, `camps.db` is created and seeded from `camps.json`.

## Deploy on Railway (Option A)

1. Create a GitHub repo and push this project.
2. In Railway, create a new project and select **Deploy from GitHub repo**.
3. Railway will detect Python and install from `requirements.txt`.
4. The app starts with:
   - `Procfile`: `gunicorn --bind 0.0.0.0:$PORT app:app`
   - `railway.json` deploy settings
5. Add environment variable:
   - `ADMIN_TOKEN` = your-secure-token

Note: this setup uses SQLite (`camps.db`) for now, which is fine for your current scale.

## 3) Public submission form

Anyone can submit a camp from the website.
Submissions are saved as `pending_review` and are not publicly listed until approved.

## 4) Admin moderation endpoints

Set an admin token before running:

```bash
set ADMIN_TOKEN=your-secret-token
python app.py
```

Review pending:

```bash
curl -H "x-admin-token: your-secret-token" http://127.0.0.1:5000/api/admin/submissions
```

Approve:

```bash
curl -X POST -H "x-admin-token: your-secret-token" http://127.0.0.1:5000/api/admin/submissions/ID/approve
```

Reject:

```bash
curl -X POST -H "x-admin-token: your-secret-token" http://127.0.0.1:5000/api/admin/submissions/ID/reject
```

## 5) Scraper pipeline (legal-first)

Edit `sources.json` with real selectors for each camp site, then run:

```bash
python scraper.py
```

Scraped items are inserted/updated as `pending_review` to avoid publishing unchecked data.

## 6) Import real starter entries now

This project includes a curated import script using publicly available camp information:

```bash
python ingest_real_data.py
```

Imported records are marked `pending_review` so you can verify before publishing.

## 7) Discovery pipeline (broad legal search)

Run this to discover camp URLs across Irish counties, check `robots.txt`, and scrape only allowed pages:

```bash
python discovery_pipeline.py
```

What it does:

- discovers candidate camp URLs from multiple county search queries
- checks each URL against `robots.txt`
- skips blocked/unknown URLs
- scrapes only allowed URLs
- stores discovered metadata in `discovered_urls`
- inserts extracted camp candidates as `pending_review`

If search engines throttle your network, run the curated seed discovery pass:

```bash
python discover_from_seed_urls.py
```

This checks a broad starter set of Irish camp URLs and only ingests pages allowed by `robots.txt`.

## Legal notes

- Always respect source site terms and `robots.txt`
- Use a clear bot user-agent with contact details
- Keep source URL and last checked timestamp
- Provide correction/removal contact for organisers
