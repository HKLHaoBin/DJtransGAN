"""Desktop entry: start Mix Studio API and open the browser."""

from __future__ import annotations

import threading
import time
import urllib.error
import urllib.request
import webbrowser

import uvicorn

from server.paths import ensure_runtime_env, read_version

HOST = "127.0.0.1"
PORT = 8010
URL = f"http://{HOST}:{PORT}/"


def _wait_and_open_browser(timeout_s: float = 60.0) -> None:
    deadline = time.time() + timeout_s
    health = f"http://{HOST}:{PORT}/api/health"
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(health, timeout=2) as resp:
                if resp.status == 200:
                    webbrowser.open(URL)
                    return
        except (urllib.error.URLError, TimeoutError, OSError):
            time.sleep(0.5)
    # Open anyway so the user sees connection errors in the browser.
    webbrowser.open(URL)


def main() -> None:
    ensure_runtime_env()
    # Import after env bootstrap so paths resolve correctly when frozen.
    from server.main import app

    print(f"[Mix Studio] DJtransGAN Mix Studio v{read_version()}")
    print(f"[Mix Studio] Opening {URL}")
    threading.Thread(target=_wait_and_open_browser, name="browser-opener", daemon=True).start()
    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        log_level="info",
    )


if __name__ == "__main__":
    main()
