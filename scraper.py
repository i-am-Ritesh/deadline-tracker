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
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.google.com/",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "cross-site",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}

DATE_PATTERNS = [
    (r"\d{2}/\d{2}/\d{4}", "%d/%m/%Y"),
    (r"\d{2}-\d{2}-\d{4}", "%d-%m-%Y"),
    (r"\d{2}\.\d{2}\.\d{4}", "%d.%m.%Y"),
]

def parse_date(text):
    for pattern, fmt in DATE_PATTERNS:
        m = re.search(pattern, text)
        if m:
            try:
                return datetime.strptime(m.group(0), fmt)
            except ValueError:
                continue
    return None

def fetch_jobs():
    # Use cloudscraper to bypass the firewall blocking GitHub's servers
    scraper = cloudscraper.create_scraper()
    
    try:
        resp = scraper.get(URL, headers=HEADERS, timeout=20)
        resp.raise_for_status()
    except Exception as e:
        print(f"HTTP Error: {e}", file=sys.stderr)
        raise

    soup = BeautifulSoup(resp.content, "html.parser")

    jobs = []
    seen = set()

    # Find every element containing "Last Date"
    for marker in soup.find_all(string=re.compile(r"Last\s*Date", re.I)):
        parent = marker.parent
        container = parent
        link = None

        # Walk up a few levels to find an <a> tag nearby
        for _ in range(6):
            if container is None:
                break
            link = container.find("a", href=True)
            if link:
                break
            container = container.parent

        if not link:
            continue

        title = link.get_text(strip=True)
        if not title or len(title) < 6:
            continue

        text = parent.get_text(" ", strip=True)
        deadline = parse_date(text)
        if not deadline:
            continue

        href = link["href"]
        if href.startswith("/"):
            href = "https://rojgarresult.com" + href

        key = (title, deadline.isoformat())
        if key in seen:
            continue
        seen.add(key)

        days_left = (deadline - datetime.now()).days
        if days_left < -30:  # skip very old entries
            continue

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
        print("No jobs found — selectors may need updating. Keeping old jobs.json.")
        sys.exit(0)

    with open("jobs.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved {len(data)} jobs, sorted by deadline.")