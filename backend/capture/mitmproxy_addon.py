"""
Neotherm API capture addon for mitmproxy.

SETUP:
  1. pip install mitmproxy
  2. mitmproxy --mode transparent -s capture/mitmproxy_addon.py
     OR: mitmdump -s capture/mitmproxy_addon.py   (headless, logs to stdout)
  3. Configure your phone to use this machine as an HTTP proxy (port 8080)
  4. Install the mitmproxy CA cert on your phone (visit mitm.it)
  5. Open the Neotherm app and interact with it (change temperature, switch modes)
  6. This script prints all captured requests — identify the Neotherm API calls

All captured traffic is written to captured_traffic.jsonl for review.
"""

import json
import time
from datetime import datetime
from mitmproxy import http


CAPTURE_FILE = "captured_traffic.jsonl"
HIGHLIGHT_KEYWORDS = ["neotherm", "neoterm", "heating", "thermostat", "thermo"]


def _is_interesting(host: str) -> bool:
    host_lower = host.lower()
    return any(kw in host_lower for kw in HIGHLIGHT_KEYWORDS)


class NeothermCapture:
    def __init__(self):
        self._file = open(CAPTURE_FILE, "a")
        print(f"\n[HOME HUB] Neotherm capture active → {CAPTURE_FILE}")
        print("[HOME HUB] Proxy all phone traffic through this machine (port 8080)\n")

    def request(self, flow: http.HTTPFlow):
        entry = {
            "ts": datetime.utcnow().isoformat(),
            "direction": "request",
            "host": flow.request.host,
            "method": flow.request.method,
            "url": flow.request.pretty_url,
            "headers": dict(flow.request.headers),
            "body": _safe_body(flow.request.content),
        }
        self._write(entry)

        if _is_interesting(flow.request.host):
            self._highlight("REQUEST", entry)

    def response(self, flow: http.HTTPFlow):
        if flow.response is None:
            return
        entry = {
            "ts": datetime.utcnow().isoformat(),
            "direction": "response",
            "host": flow.request.host,
            "url": flow.request.pretty_url,
            "status": flow.response.status_code,
            "headers": dict(flow.response.headers),
            "body": _safe_body(flow.response.content),
        }
        self._write(entry)

        if _is_interesting(flow.request.host):
            self._highlight("RESPONSE", entry)

    def _write(self, entry: dict):
        self._file.write(json.dumps(entry) + "\n")
        self._file.flush()

    def _highlight(self, label: str, entry: dict):
        sep = "=" * 60
        print(f"\n{sep}")
        print(f"  *** NEOTHERM {label} DETECTED ***")
        print(f"  Host   : {entry['host']}")
        print(f"  URL    : {entry.get('url', '')}")
        if label == "REQUEST":
            print(f"  Method : {entry['method']}")
        else:
            print(f"  Status : {entry.get('status', '')}")
        body = entry.get("body")
        if body:
            print(f"  Body   : {json.dumps(body, indent=4)}")
        print(sep)


def _safe_body(content: bytes | None) -> dict | str | None:
    if not content:
        return None
    try:
        return json.loads(content)
    except Exception:
        text = content.decode("utf-8", errors="replace")
        return text[:2000] if len(text) > 2000 else text


addons = [NeothermCapture()]
