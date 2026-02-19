import json
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    ElementClickInterceptedException,
    NoSuchElementException,
    StaleElementReferenceException,
)

# ── Configuration ──────────────────────────────────────────────────────
CREDENTIAL_FILE = "credential.json"
SEARCH_URL = (
    "https://www.linkedin.com/search/results/people/"
    "?keywords=talent%20acquisition%20Amazon&origin=SWITCH_SEARCH_VERTICAL"
)
MAX_PAGES = 5  # how many result pages to process (change as needed)
DELAY_BETWEEN_ACTIONS = (2, 4)  # random sleep range in seconds


def random_delay(low=None, high=None):
    low = low or DELAY_BETWEEN_ACTIONS[0]
    high = high or DELAY_BETWEEN_ACTIONS[1]
    time.sleep(random.uniform(low, high))


# ── Load credentials ───────────────────────────────────────────────────
with open(CREDENTIAL_FILE, "r") as f:
    creds = json.load(f)

EMAIL = creds["email"]
PASSWORD = creds["password"]

# ── Set up browser ─────────────────────────────────────────────────────
chrome_options = Options()
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option("useAutomationExtension", False)

driver = webdriver.Chrome(options=chrome_options)
driver.execute_cdp_cmd(
    "Page.addScriptToEvaluateOnNewDocument",
    {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"},
)
wait = WebDriverWait(driver, 15)


def login():
    """Log in to LinkedIn."""
    print("[*] Navigating to LinkedIn login …")
    driver.get("https://www.linkedin.com/login")
    random_delay(2, 4)

    email_field = wait.until(EC.presence_of_element_located((By.ID, "username")))
    email_field.clear()
    email_field.send_keys(EMAIL)

    password_field = driver.find_element(By.ID, "password")
    password_field.clear()
    password_field.send_keys(PASSWORD)

    random_delay(1, 2)
    driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()

    # Wait until the feed or some logged-in page loads
    try:
        wait.until(
            lambda d: "/feed" in d.current_url
            or "/search" in d.current_url
            or "/check" in d.current_url
            or "/checkpoint" in d.current_url
        )
    except TimeoutException:
        pass

    # If a security checkpoint appears, wait for the user to solve it
    if "checkpoint" in driver.current_url or "check" in driver.current_url:
        print("[!] Security checkpoint detected – please solve it manually.")
        input("    Press ENTER here once you are past the checkpoint …")

    print("[✓] Logged in successfully.")
    random_delay(2, 4)


def dismiss_any_modal():
    """Try to close any overlay / modal that may have appeared."""
    selectors = [
        'button[aria-label="Dismiss"]',
        'button[aria-label="Got it"]',
        'button[aria-label="Close"]',
        'button.artdeco-modal__dismiss',
        'button.msg-overlay-bubble-header__control--new-convo-btn',
    ]
    for sel in selectors:
        try:
            btn = driver.find_element(By.CSS_SELECTOR, sel)
            if btn.is_displayed():
                btn.click()
                random_delay(0.5, 1)
        except (NoSuchElementException, ElementClickInterceptedException):
            pass


def scroll_to_bottom():
    """Scroll down the page gradually to load all results."""
    last_height = driver.execute_script("return document.body.scrollHeight")
    for _ in range(5):
        driver.execute_script("window.scrollBy(0, 600);")
        random_delay(0.8, 1.5)
    # Scroll back to top so buttons are interactable
    driver.execute_script("window.scrollTo(0, 0);")
    random_delay(1, 2)


def send_connection_requests_on_page():
    """
    Find all Connect buttons on the current page and click them.
    Connect buttons live inside a container with
        data-view-name="edge-creation-connect-action"
    and are <a> tags whose aria-label starts with "Invite" and ends with
    "to connect".
    """
    sent = 0

    # Re-collect buttons each iteration because the DOM may change
    connect_containers = driver.find_elements(
        By.CSS_SELECTOR, '[data-view-name="edge-creation-connect-action"]'
    )
    print(f"  Found {len(connect_containers)} Connect button(s) on this page.")

    for idx in range(len(connect_containers)):
        try:
            # Re-find containers to avoid stale references
            containers = driver.find_elements(
                By.CSS_SELECTOR, '[data-view-name="edge-creation-connect-action"]'
            )
            if idx >= len(containers):
                break

            container = containers[idx]
            # The <a> tag inside the container
            connect_btn = container.find_element(By.CSS_SELECTOR, "a")
            person_name = connect_btn.get_attribute("aria-label") or "Unknown"
            print(f"  → Clicking: {person_name}")

            # Scroll the button into view
            driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});", connect_btn
            )
            random_delay(0.5, 1)

            connect_btn.click()
            random_delay(2, 3)

            # ── Handle the modal that appears after clicking Connect ────
            # LinkedIn may show a modal asking to "Send without a note" or
            # "Add a note".  We look for the "Send without a note" or plain
            # "Send" button.
            modal_handled = False

            # Option A: "Send without a note" button
            try:
                send_btn = wait.until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, 'button[aria-label="Send without a note"]')
                    )
                )
                send_btn.click()
                modal_handled = True
                print(f"    ✓ Sent (without note)")
            except TimeoutException:
                pass

            # Option B: Plain "Send" / "Send invitation" button inside a modal
            if not modal_handled:
                try:
                    send_btn = driver.find_element(
                        By.XPATH,
                        '//button[contains(@aria-label,"Send invitation") or '
                        'contains(@aria-label,"Send now")]',
                    )
                    if send_btn.is_displayed():
                        send_btn.click()
                        modal_handled = True
                        print(f"    ✓ Sent (invitation)")
                except NoSuchElementException:
                    pass

            # Option C: There might be a "Send" button with specific text
            if not modal_handled:
                try:
                    buttons = driver.find_elements(
                        By.CSS_SELECTOR, "button.artdeco-button--primary"
                    )
                    for btn in buttons:
                        if btn.text.strip().lower() in ("send", "send invitation"):
                            btn.click()
                            modal_handled = True
                            print(f"    ✓ Sent (primary button)")
                            break
                except Exception:
                    pass

            if not modal_handled:
                # Maybe the connection was sent directly without a modal
                print(f"    ⚠ No modal detected – request may have been sent directly.")

            random_delay(1, 2)
            dismiss_any_modal()
            sent += 1

        except (
            StaleElementReferenceException,
            ElementClickInterceptedException,
            TimeoutException,
            NoSuchElementException,
        ) as e:
            print(f"    ✗ Skipped ({type(e).__name__})")
            dismiss_any_modal()
            random_delay(1, 2)
            continue

    return sent


def go_to_next_page():
    """Click the 'Next' pagination button. Returns True if successful."""
    try:
        next_btn = driver.find_element(
            By.CSS_SELECTOR, 'button[aria-label="Next"]'
        )
        if next_btn.is_enabled():
            driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});", next_btn
            )
            random_delay(0.5, 1)
            next_btn.click()
            random_delay(3, 5)
            return True
    except NoSuchElementException:
        pass
    return False


# ── Main flow ──────────────────────────────────────────────────────────
def main():
    total_sent = 0
    try:
        login()

        print(f"[*] Opening search URL …")
        driver.get(SEARCH_URL)
        random_delay(3, 5)
        dismiss_any_modal()

        for page in range(1, MAX_PAGES + 1):
            print(f"\n[Page {page}] Processing …")
            scroll_to_bottom()
            sent = send_connection_requests_on_page()
            total_sent += sent
            print(f"[Page {page}] Sent {sent} request(s).  Total so far: {total_sent}")

            if not go_to_next_page():
                print("[*] No more pages.")
                break

    except KeyboardInterrupt:
        print("\n[!] Interrupted by user.")
    except Exception as e:
        print(f"\n[!] Unexpected error: {e}")
    finally:
        print(f"\n[✓] Done. Total connection requests sent: {total_sent}")
        input("Press ENTER to close the browser …")
        driver.quit()


if __name__ == "__main__":
    main()
