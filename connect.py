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


def send_connection_requests_on_page():
    """Find all Connect buttons on the current page and click them."""
    sent = 0

    connect_containers = driver.find_elements(
        By.CSS_SELECTOR, '[data-view-name="edge-creation-connect-action"]'
    )
    print(f"  Found {len(connect_containers)} Connect button(s) on this page.")

    for idx in range(len(connect_containers)):
        try:
            dismiss_any_modal()
            random_delay(0.5, 1)

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
                print("attempt", attempt)
                try:
                    connect_btn.click()
                    click_success = True
                    print("attempt try : ", attempt)
                    break
                except ElementClickInterceptedException:
                    print(f"    ⚠ Click intercepted (attempt {attempt + 1}/3), dismissing overlay …")
                    dismiss_any_modal()
                    random_delay(1, 2)
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

            # Option A: Click "Add a note" button only
            try:
                print("before add note")
                # add 2 sec delay

                add_note_button = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//span[text()='Add a note']"))
                )

                # add_note_btn = wait.until(EC.element_to_be_clickable(
                #     (By.XPATH, "//button")
                # ))

                # add_note_btn = driver.find_element(
                #     By.CSS_SELECTOR,
                #     'button'
                #     # 'button[aria-label="Add a note"]'
                # )

                print("--x--")
                print("after add note ",add_note_btn)
                print("--y--", add_note_btn.get_attribute("outerHTML"))
                random_delay(0.5, 1)
                try:
                    print("before add note click", add_note_btn.text)
                    add_note_btn.click()
                    print("after add note click")
                except ElementClickInterceptedException:
                    driver.execute_script("arguments[0].click();", add_note_btn)
                random_delay(1, 2)

                note_textarea = wait.until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, 'textarea[name="message"], textarea#custom-message')
                    )
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
                note_textarea.clear()
                note_textarea.send_keys(personal_note)
                random_delay(1, 2)

                send_btn = wait.until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR,
                         'button[aria-label="Send invitation"], '
                         'button[aria-label="Send now"]')
                    )
                )
                send_btn.click()
                modal_handled = True
                print(f"    ✓ Sent (with note)")
            except (TimeoutException, NoSuchElementException) as note_err:
                print(f"    ⚠ Add-a-note path failed: {type(note_err).__name__}")
                print("")
                print("--z-- ", note_err)

            # Option B: "Send without a note" button
            if not modal_handled:
                try:
                    send_btn = driver.find_element(
                        By.CSS_SELECTOR,
                        'button[aria-label="Send without a note"]',
                    )
                    if send_btn.is_displayed():
                        send_btn.click()
                        modal_handled = True
                        print(f"    ✓ Sent (without note)")
                except (NoSuchElementException, TimeoutException):
                    pass

            # Option C: Plain "Send" / "Send invitation" button inside a modal
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

            # Option D: Any primary button with text "Send"
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
