#!/usr/bin/env python3
"""Mark 3 alarm — one Telegram message to the owner's existing bot channel.

    python3 live/alert.py "text"

Reads TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID from $MARK3_TG_ENV (default
/root/.config/tg/env — the same file /opt/ecom-intel's cron alerts use, so
this lands in the channel Daman already watches). Never raises: an alarm that
crashes the loop is worse than no alarm. Prints one line either way.
"""
import os, sys, urllib.parse, urllib.request

ENV = os.environ.get("MARK3_TG_ENV", "/root/.config/tg/env")


def send(text: str) -> bool:
    tok = chat = None
    try:
        for line in open(ENV):
            line = line.strip()
            if line.startswith("TELEGRAM_BOT_TOKEN="):
                tok = line.split("=", 1)[1].strip()
            elif line.startswith("TELEGRAM_CHAT_ID="):
                chat = line.split("=", 1)[1].strip()
        if not (tok and chat):
            raise RuntimeError("tg env incomplete")
        urllib.request.urlopen(
            f"https://api.telegram.org/bot{tok}/sendMessage",
            data=urllib.parse.urlencode({"chat_id": chat, "text": text}).encode(),
            timeout=30)
        print("alert: sent")
        return True
    except Exception as e:                    # noqa: BLE001 — alert-only
        print(f"alert: NOT sent ({e})")
        return False


if __name__ == "__main__":
    sys.exit(0 if send(" ".join(sys.argv[1:]) or "(empty alert)") else 1)
