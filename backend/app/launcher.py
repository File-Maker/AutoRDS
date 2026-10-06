from __future__ import annotations

import os
import threading
import time
import urllib.request
import webbrowser

import uvicorn


def open_when_ready() -> None:
    for _ in range(120):
        try:
            with urllib.request.urlopen("http://127.0.0.1:8134/api/health", timeout=1) as response:
                if response.status == 200:
                    webbrowser.open("http://127.0.0.1:8134")
                    return
        except OSError:
            time.sleep(0.25)


def main() -> None:
    if not os.getenv("AUTORDS_NO_BROWSER"):
        threading.Thread(target=open_when_ready, daemon=True).start()
    uvicorn.run("app.main:app", host="127.0.0.1", port=8134, log_level="info")


if __name__ == "__main__":
    main()
