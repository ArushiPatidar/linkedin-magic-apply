from config import MAX_PAGES, SEARCH_URL
from browser import driver
from auth import login
from utils import random_delay, dismiss_any_modal, scroll_to_bottom
from connect import send_connection_requests_on_page, go_to_next_page


def main():
    total_sent = 0
    try:
        login()

        print(f"[*] Opening search URL …")
        driver.get(SEARCH_URL)
        random_delay(1, 2)
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
