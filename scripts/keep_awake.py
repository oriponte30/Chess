"""Opens the app in a real (headless) browser so Streamlit Community Cloud counts it as a visit, and wakes it if it has gone to sleep.
A plain HTTP request is not enough: the platform only counts a visit once the page opens its live connection.

    APP_URL=https://your-app.streamlit.app python scripts/keep_awake.py

Run by .github/workflows/keepalive.yml every few hours. Exits with an error when the app does not come up, so the workflow shows red."""
from __future__ import annotations

import os
import sys
import time

from playwright.sync_api import TimeoutError as PWTimeout, sync_playwright

WAKE_BUTTONS = ("Yes, get this app back up", "get this app back up", "Wake up")


def main() -> int:
    url = (os.environ.get("APP_URL") or "").strip()
    if not url:
        print("APP_URL is not set. Add your app's address as a repository variable named APP_URL (Settings > Secrets and variables > Actions > Variables).")
        return 2
    with sync_playwright() as p:
        chrome = os.environ.get("CHROME_PATH")                              # optional: use an installed Chrome instead of the bundled one
        browser = p.chromium.launch(executable_path=chrome, args=["--no-sandbox"]) if chrome else p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        for attempt in range(1, 4):
            print(f"[{attempt}] opening {url}")
            page.goto(url, wait_until="domcontentloaded", timeout=90_000)
            page.wait_for_timeout(4_000)
            woke = False
            for text in WAKE_BUTTONS:                                   # the app was asleep: press the button on the sleep page
                btn = page.get_by_role("button", name=text)
                if btn.count():
                    print("  the app was asleep, waking it up")
                    btn.first.click()
                    woke = True
                    break
            # the app itself may sit inside an iframe (Community Cloud) or be the page (anything else)
            deadline = time.time() + (240 if woke else 90)
            ok = False
            while time.time() < deadline:
                frames = [page] + [f for f in page.frames if f != page.main_frame]
                for f in frames:
                    try:
                        if f.locator('[data-testid="stApp"]').count() and f.locator('[data-testid="stSidebar"], [data-testid="stMain"]').count():
                            ok = True
                            break
                    except Exception:                                   # noqa: BLE001  (frame navigating)
                        pass
                if ok:
                    break
                page.wait_for_timeout(2_000)
            if ok:
                page.wait_for_timeout(20_000)                          # stay a moment so the live connection is registered
                print("  the app is up")
                browser.close()
                return 0
            print("  the app did not load in time")
        browser.close()
    return 1


if __name__ == "__main__":
    sys.exit(main())
