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
    scraper = cloudscraper.create_scraper()
    resp = scraper.get(URL, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.content, "html.parser")

    jobs = []
    seen = set()

    # Find every element containing "Last Date"
    for marker in soup.find_all(string=re.compile(r"Last\s*Date", re.I)):
        parent = marker.parent
        
        # Walk up to find a container (table row, list item, or div)
        container = parent
        for _ in range(5):
            if container.name in ['tr', 'li', 'article']:
                break
            if container.name == 'div' and len(container.get_text(strip=True)) > 30:
                break
            container = container.parent
            if not container:
                break

        if not container:
            continue

        block_text = container.get_text(" ", strip=True)
        deadline = parse_date(block_text)
        
        # Only keep jobs that are closing in the future or closed max 2 days ago
        if not deadline:
            continue
        days_left = (deadline - datetime.now()).days
        if days_left < -2:
            continue

        # Find the actual title (look for headings or bold text first)
        title_elem = container.find(['h2', 'h3', 'h4', 'b', 'strong'])
        
        # If no heading, look for a link that IS NOT "Click Here"
        if not title_elem:
            for a in container.find_all('a'):
                text = a.get_text(strip=True).lower()
                if text and "click" not in text and "apply" not in text and "read" not in text and len(text) > 8:
                    title_elem = a
                    break

        title = title_elem.get_text(strip=True) if title_elem else "Job Notification"

        # Find the link to apply
        link_elem = container.find('a', href=True)
        href = link_elem['href'] if link_elem else ""
        if href.startswith("/"):
            href = "https://rojgarresult.com" + href

        # Avoid duplicates
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