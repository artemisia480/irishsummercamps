#!/usr/bin/env python3
"""
Camp Data Enhancement Script

This script:
1. Reads all camps from the database
2. For camps with source_url, scrapes the website
3. Uses Claude AI to extract missing data (price, ages, description, activities)
4. Updates the database with enhanced information

Usage:
    python enhance_camps.py

Requirements:
    pip install anthropic requests beautifulsoup4 --break-system-packages

Environment Variables:
    ANTHROPIC_API_KEY - Your Anthropic API key (required)
"""

import os
import sqlite3
import json
import time
from pathlib import Path
from datetime import datetime

try:
    import anthropic
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("ERROR: Missing required packages.")
    print("Run: pip install anthropic requests beautifulsoup4 --break-system-packages")
    exit(1)

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "camps.db"

# Check for API key
API_KEY = os.environ.get("ANTHROPIC_API_KEY")
if not API_KEY:
    print("ERROR: ANTHROPIC_API_KEY environment variable not set")
    print("Get your key from: https://console.anthropic.com/")
    print("Then run: export ANTHROPIC_API_KEY='your-key-here'")
    exit(1)

client = anthropic.Anthropic(api_key=API_KEY)


def get_db():
    """Get database connection"""
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def scrape_website(url, timeout=10):
    """Scrape website content"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; IrishSummerCampsBot/1.0; +https://irishsummercamps.ie/contact)'
        }
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text
        text = soup.get_text()
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        # Limit to 8000 chars to avoid token limits
        return text[:8000]
    
    except Exception as e:
        print(f"  ❌ Failed to scrape: {str(e)}")
        return None


def extract_camp_data(camp_name, website_text):
    """Use Claude to extract structured data from website text"""
    
    prompt = f"""You are analyzing a summer camp website to extract missing information.

Camp name: {camp_name}

Website content:
{website_text}

Extract the following information if present (respond with null if not found):
1. Price in euros (just the number, e.g., 295)
2. Minimum age (just the number, e.g., 8)
3. Maximum age (just the number, e.g., 14)
4. Brief description (2-3 sentences max, compelling and parent-friendly)
5. Main activities (comma-separated list, e.g., "Swimming, Football, Arts & Crafts")

Respond ONLY with valid JSON in this exact format:
{{
  "price_eur": 295,
  "age_min": 8,
  "age_max": 14,
  "description": "A fun-filled adventure camp...",
  "activities": "Swimming, Football, Arts & Crafts"
}}

If any field is not found, use null. Be conservative - only extract data you're confident about."""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = message.content[0].text.strip()
        
        # Remove markdown code fences if present
        if response_text.startswith("```"):
            response_text = response_text.split("\n", 1)[1]
            response_text = response_text.rsplit("```", 1)[0]
        
        data = json.loads(response_text)
        return data
    
    except Exception as e:
        print(f"  ❌ AI extraction failed: {str(e)}")
        return None


def update_camp(connection, camp_id, extracted_data):
    """Update camp with extracted data"""
    updates = []
    values = []
    
    if extracted_data.get("price_eur") is not None:
        updates.append("price_eur = ?")
        values.append(extracted_data["price_eur"])
    
    if extracted_data.get("age_min") is not None:
        updates.append("age_min = ?")
        values.append(extracted_data["age_min"])
    
    if extracted_data.get("age_max") is not None:
        updates.append("age_max = ?")
        values.append(extracted_data["age_max"])
    
    # Store description and activities in notes field (we can add dedicated columns later)
    notes_parts = []
    if extracted_data.get("description"):
        notes_parts.append(f"Description: {extracted_data['description']}")
    if extracted_data.get("activities"):
        notes_parts.append(f"Activities: {extracted_data['activities']}")
    
    if notes_parts:
        updates.append("notes = ?")
        values.append("\n\n".join(notes_parts))
    
    if updates:
        updates.append("updated_at = ?")
        values.append(datetime.utcnow().isoformat())
        values.append(camp_id)
        
        query = f"UPDATE camps SET {', '.join(updates)} WHERE id = ?"
        connection.execute(query, values)
        connection.commit()
        return True
    
    return False


def enhance_camps():
    """Main function to enhance all camps"""
    connection = get_db()
    
    # Get camps with URLs but missing data
    camps = connection.execute("""
        SELECT id, name, source_url, price_eur, age_min, age_max, notes
        FROM camps 
        WHERE status = 'approved' 
        AND source_url IS NOT NULL 
        AND source_url != ''
        ORDER BY id
    """).fetchall()
    
    print(f"Found {len(camps)} camps with URLs")
    print("=" * 60)
    
    enhanced_count = 0
    skipped_count = 0
    
    for camp in camps:
        camp_id = camp['id']
        camp_name = camp['name']
        source_url = camp['source_url']
        
        # Check what's missing
        missing = []
        if camp['price_eur'] is None:
            missing.append("price")
        if camp['age_min'] is None or camp['age_max'] is None:
            missing.append("ages")
        if not camp['notes']:
            missing.append("description")
        
        if not missing:
            print(f"✓ {camp_name} - already complete")
            skipped_count += 1
            continue
        
        print(f"\n🔍 {camp_name}")
        print(f"   URL: {source_url}")
        print(f"   Missing: {', '.join(missing)}")
        
        # Scrape website
        print("   Scraping website...")
        website_text = scrape_website(source_url)
        
        if not website_text:
            skipped_count += 1
            continue
        
        # Extract data with AI
        print("   Extracting data with AI...")
        extracted = extract_camp_data(camp_name, website_text)
        
        if not extracted:
            skipped_count += 1
            continue
        
        # Update database
        if update_camp(connection, camp_id, extracted):
            print(f"   ✅ Enhanced!")
            if extracted.get("price_eur"):
                print(f"      Price: €{extracted['price_eur']}")
            if extracted.get("age_min") and extracted.get("age_max"):
                print(f"      Ages: {extracted['age_min']}-{extracted['age_max']}")
            enhanced_count += 1
        else:
            print(f"   ⚠️ No new data extracted")
            skipped_count += 1
        
        # Rate limiting - be nice to camp websites
        time.sleep(2)
    
    connection.close()
    
    print("\n" + "=" * 60)
    print(f"✅ Complete!")
    print(f"   Enhanced: {enhanced_count} camps")
    print(f"   Skipped: {skipped_count} camps")
    print("=" * 60)


if __name__ == "__main__":
    print("🏕️  Irish Summer Camps - Data Enhancement Tool")
    print("=" * 60)
    enhance_camps()