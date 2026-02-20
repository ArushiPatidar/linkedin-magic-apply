import json
import urllib.parse

CREDENTIAL_FILE = "credential.json"
COMPANIES_FILE = "companies.txt"
CONNECTION_NOTE_FILE = "connection_note.txt"
MAX_PAGES = 5
MAX_REQUESTS_PER_COMPANY = 4
DELAY_BETWEEN_ACTIONS = (2, 4)

def log(message):
    """Print a message and flush immediately so it appears in real time."""
    print(message, flush=True)

def load_companies(filepath="companies.txt"):
    """Read company names from a text file, one per line."""
    with open(filepath, "r") as f:
        return [line.strip() for line in f if line.strip()]

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
