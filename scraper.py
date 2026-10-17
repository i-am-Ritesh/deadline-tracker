import cloudscraper
from bs4 import BeautifulSoup
from datetime import datetime
import json
import re
import sys

URL = "https://rojgarresult.com/recruitments/"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

def fetch_jobs():
    scraper = cloudscraper.create_scraper()
    resp = scraper.get(URL, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.content, "html.parser")

    jobs = []
    seen = set()

    # We target the specific container for each job based on your HTML file
    for item in soup.select('.gb-loop-item'):
        
        # 1. Extract the Title and the real link
        title_elem = item.select_one('h2.gb-text-65bad0de a')
        if not title_elem:
            continue
        
        title = title_elem.get_text(strip=True)
        href = title_elem.get('href', '')
        
        # 2. Extract the Date
        date_elem = item.select_one('p.gb-text-423b0b64')
        if not date_elem:
            continue
            
        date_text = date_elem.get_text(strip=True)
        
        # 3. Parse the Date (looking for DD/MM/YYYY)
        match = re.search(r'(\d{2})/(\d{2})/(\d{4})', date_text)
        if not match:
            # Skip jobs that say "District Wise" or "Not Declared"
            continue
            
        try:
            deadline = datetime.strptime(match.group(0), "%d/%m/%Y")
        except ValueError:
            continue
            
        # 4. Filter out old jobs (only show jobs closing today or in the future)
        # If a job closed yesterday (-1), we still hide it.
        days_left = (deadline - datetime.now()).days
        if days_left < 0:
            continue

        key = (title, deadline.isoformat())
        if key in seen:
            continue
        seen.add(key)

        jobs.append({
            "title": title,
            "deadline": deadline.isoformat(),
            "link": href,
            "days_left": days_left,
        })

    jobs.sort(key=lambda x: x["deadline"])
    return jobs

if __name__ == "__main__":
    try:
        data = fetch_jobs()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    if not data:
        print("No jobs found — keeping old jobs.json.")
        sys.exit(0)

    with open("jobs.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved {len(data)} jobs, sorted by deadline.")