import json
import urllib.parse

CREDENTIAL_FILE = "linkedin/credential.json"
COMPANIES_FILE = "companies.txt"
CONNECTION_NOTE_FILE = "connection_note.txt"
MAX_PAGES = 5
MAX_REQUESTS_PER_COMPANY = 3
DELAY_BETWEEN_ACTIONS = (2, 4)

def log(message):
    """Print a message and flush immediately so it appears in real time."""
    print(message, flush=True)

def load_companies(filepath=COMPANIES_FILE):
    """Read company names from a text file, one per line.
    Supports optional comma-separated request count, e.g. 'Microsoft,25'.
    Returns a list of (company_name, max_requests) tuples.
    """
    companies = []
    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if "," in line:
                parts = line.split(",", 1)
                name = parts[0].strip()
                try:
                    count = int(parts[1].strip())
                except ValueError:
                    count = MAX_REQUESTS_PER_COMPANY
            else:
                name = line
                count = MAX_REQUESTS_PER_COMPANY
            companies.append((name, count))
    return companies

def build_search_url(company_name):
    """Build a LinkedIn people search URL for the given company."""
    encoded = urllib.parse.quote(company_name)
    return f"https://www.linkedin.com/search/results/people/?keywords=talent%20acquisition%20{encoded}&origin=GLOBAL_SEARCH_HEADER"

with open(CREDENTIAL_FILE, "r") as f:
    creds = json.load(f)
EMAIL = creds["email"]
PASSWORD = creds["password"]

with open(CONNECTION_NOTE_FILE, "r", encoding="utf-8") as f:
    CONNECTION_NOTE = f.read().strip()

if len(CONNECTION_NOTE) > 300:
    print("[!] Connection note exceeds 300 chars – LinkedIn may reject it. Truncating.")
    CONNECTION_NOTE = CONNECTION_NOTE[:300]
