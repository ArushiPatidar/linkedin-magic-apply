from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    ElementClickInterceptedException,
    NoSuchElementException,
    StaleElementReferenceException,
)
from browser import driver, wait
from config import CONNECTION_NOTE
from utils import random_delay, dismiss_any_modal
import time
from datetime import datetime


def send_connection_requests_on_page(remaining=None, max_req_to_people=10, log_callback=None):
    """Find all Connect buttons on the current page and click them.
    Returns (sent_count, log_entries) where log_entries is a list of dicts."""
    sent = 0
    log_entries = []

    connect_containers = driver.find_elements(
        By.CSS_SELECTOR, '[data-view-name="edge-creation-connect-action"]'
    )
    print(f"  Found {len(connect_containers)} Connect button(s) on this page.")

    for idx in range(min(len(connect_containers),max_req_to_people)):
        if remaining is not None and sent >= remaining:
            print(f"  Reached per-company limit, stopping.")
            break

        try:
            dismiss_any_modal()
            random_delay(0.3, 0.8)

            containers = driver.find_elements(
                By.CSS_SELECTOR, '[data-view-name="edge-creation-connect-action"]'
            )
            if idx >= len(containers):
                break

            container = containers[idx]
            connect_btn = container.find_element(By.CSS_SELECTOR, "a")
            person_name = connect_btn.get_attribute("aria-label") or "Unknown"
            print(f"  → Clicking: {person_name}")

            driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});", connect_btn
            )
            random_delay(0.5, 1)

            # Retry click up to 3 times if intercepted
            click_success = False
            for attempt in range(3):
                print("attempt : ", attempt)
                try:
                    connect_btn.click()
                    click_success = True
                    # print("attempt try : ", attempt)
                    break
                except ElementClickInterceptedException:
                    print(f"    ⚠ Click intercepted (attempt {attempt + 1}/3), dismissing overlay …")
                    dismiss_any_modal()
                    random_delay(0.5, 1)
                    try:
                        containers = driver.find_elements(
                            By.CSS_SELECTOR, '[data-view-name="edge-creation-connect-action"]'
                        )
                        if idx < len(containers):
                            container = containers[idx]
                            connect_btn = container.find_element(By.CSS_SELECTOR, "a")
                            driver.execute_script(
                                "arguments[0].scrollIntoView({block:'center'});", connect_btn
                            )
                            random_delay(0.5, 1)
                    except Exception:
                        break

            if not click_success:
                print(f"    ✗ Skipped (could not click after retries)")
                continue

            modal_handled = False
            note_sent = ""
            method = ""

            # Option A: Access modal via shadow DOM, click "Add a note", fill textarea, send
            try:
                driver.implicitly_wait(1)

                root_element = driver.find_element(By.XPATH, '//*[@id="root"]')
                shadow_containers = root_element.find_elements(
                    By.XPATH, './/div[@data-testid="interop-shadowdom"]'
                )

                if not shadow_containers:
                    raise NoSuchElementException("No shadow DOM container found")

                shadow_root = shadow_containers[0].shadow_root

                add_note_btn = shadow_root.find_element(
                    By.CSS_SELECTOR, "button[aria-label='Add a note']"
                )
                print(f"    Found 'Add a note' button")
                add_note_btn.click()
                random_delay(0.5, 1)

                textarea = shadow_root.find_element(
                    By.CSS_SELECTOR, "textarea[name='message']"
                )
                WebDriverWait(shadow_root, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "textarea[name='message']"))
                )

                first_name = (
                    person_name.replace("Invite ", "").split(" to connect")[0].split()[0]
                    if "Invite" in person_name
                    else ""
                )
                personal_note = (
                    CONNECTION_NOTE.replace("{name}", first_name)
                    if first_name
                    else CONNECTION_NOTE
                )
                textarea.clear()
                textarea.send_keys(personal_note)
                random_delay(0.5, 1)

                send_btn = shadow_root.find_element(
                    By.CSS_SELECTOR, "button[aria-label='Send invitation']"
                )
                send_btn.click()
                modal_handled = True
                note_sent = personal_note
                method = "with note"
                print(f"    ✓ Sent (with note)")
            except (TimeoutException, NoSuchElementException, StaleElementReferenceException) as note_err:
                print(f"    ⚠ Add-a-note path failed: {type(note_err).__name__}: {note_err}")

            # Option B: "Send without a note" via shadow DOM
            if not modal_handled:
                try:
                    root_element = driver.find_element(By.XPATH, '//*[@id="root"]')
                    shadow_containers = root_element.find_elements(
                        By.XPATH, './/div[@data-testid="interop-shadowdom"]'
                    )
                    if shadow_containers:
                        shadow_root = shadow_containers[0].shadow_root
                        send_btn = shadow_root.find_element(
                            By.CSS_SELECTOR, "button[aria-label='Send without a note']"
                        )
                        send_btn.click()
                        modal_handled = True
                        method = "without note"
                        print(f"    ✓ Sent (without note)")
                except (NoSuchElementException, TimeoutException):
                    pass

            # Option C: Plain "Send" / "Send invitation" via shadow DOM
            if not modal_handled:
                try:
                    root_element = driver.find_element(By.XPATH, '//*[@id="root"]')
                    shadow_containers = root_element.find_elements(
                        By.XPATH, './/div[@data-testid="interop-shadowdom"]'
                    )
                    if shadow_containers:
                        shadow_root = shadow_containers[0].shadow_root
                        send_btn = shadow_root.find_element(
                            By.CSS_SELECTOR,
                            "button[aria-label='Send invitation'], button[aria-label='Send now']"
                        )
                        send_btn.click()
                        modal_handled = True
                        method = "direct invitation"
                        print(f"    ✓ Sent (invitation)")
                except (NoSuchElementException, TimeoutException):
                    pass

            if not modal_handled:
                print(f"    ⚠ No modal detected – request may have been sent directly.")
                method = "unknown/direct"

            random_delay(0.5, 1)
            dismiss_any_modal()
            sent += 1

            entry = {
                "person_name": person_name,
                "method": method,
                "note": note_sent,
                "status": "sent" if modal_handled else "possibly sent",
                "timestamp": datetime.now().isoformat(),
                "page_url": driver.current_url,
            }
            log_entries.append(entry)
            if log_callback:
                log_callback(entry)

        except (
            StaleElementReferenceException,
            ElementClickInterceptedException,
            TimeoutException,
            NoSuchElementException,
        ) as e:
            print(f"    ✗ Skipped ({type(e).__name__})")
            dismiss_any_modal()
            random_delay(0.5, 1)
            continue

    return sent, log_entries


def go_to_next_page():
    """Click the 'Next' pagination button. Returns True if successful."""
    try:
        next_btn = driver.find_element(
            By.CSS_SELECTOR, 'button[data-testid="pagination-controls-next-button-visible"]'
        )
        if next_btn.is_enabled():
            driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});", next_btn
            )
            random_delay(0.5, 1)
            next_btn.click()
            random_delay(0.5, 1)
            return True
    except NoSuchElementException:
        pass
    return False
