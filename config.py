import json

CREDENTIAL_FILE = "credential.json"
COMPANIES_FILE = "companies.txt"
SEARCH_URL = (
    "https://www.linkedin.com/search/results/people/"
    "?keywords=talent%20acquisition%20Amazon&origin=SWITCH_SEARCH_VERTICAL"
)
MAX_PAGES = 5
DELAY_BETWEEN_ACTIONS = (2, 4)

with open(CREDENTIAL_FILE, "r") as f:
    creds = json.load(f)
EMAIL = creds["email"]
PASSWORD = creds["password"]

with open(COMPANIES_FILE, "r", encoding="utf-8") as f:
    CONNECTION_NOTE = f.read().strip()

if len(CONNECTION_NOTE) > 300:
    print("[!] Connection note exceeds 300 chars – LinkedIn may reject it. Truncating.")
    CONNECTION_NOTE = CONNECTION_NOTE[:300]
