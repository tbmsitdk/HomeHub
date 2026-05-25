"""
Neotherm floor heating integration.

Neotherm does not publish a public API. This module uses realistic mock data
while you capture the real API using mitmproxy (see capture/mitmproxy_addon.py).

Once you have captured the endpoints, replace the MOCK_* constants and the
methods below with real HTTP calls (using httpx).
"""

import os
import asyncio
import httpx
import logging
from typing import Any

logger = logging.getLogger(__name__)

# ── Replace these once you've captured real traffic ──────────────────────────
NEOTHERM_BASE_URL = os.getenv("NEOTHERM_BASE_URL", "")
NEOTHERM_API_KEY = os.getenv("NEOTHERM_API_KEY", "")
# ─────────────────────────────────────────────────────────────────────────────

MOCK_ZONES: list[dict[str, Any]] = [
    {
        "id": "zone-living",
        "name": "Living Room",
        "current_temp": 22.3,
        "target_temp": 22.0,
        "heating": False,
        "mode": "schedule",
        "floor_temp": 24.1,
    },
    {
        "id": "zone-bedroom",
        "name": "Bedroom",
        "current_temp": 20.1,
        "target_temp": 20.0,
        "heating": False,
        "mode": "schedule",
        "floor_temp": 21.4,
    },
    {
        "id": "zone-bathroom",
        "name": "Bathroom",
        "current_temp": 23.2,
        "target_temp": 24.0,
        "heating": True,
        "mode": "manual",
        "floor_temp": 28.5,
    },
    {
        "id": "zone-hallway",
        "name": "Hallway",
        "current_temp": 19.8,
        "target_temp": 20.0,
        "heating": True,
        "mode": "eco",
        "floor_temp": 22.0,
    },
]


class NeothermManager:
    def __init__(self):
        self._mock = True
        self.status = "mock"
        self._zones: list[dict[str, Any]] = [z.copy() for z in MOCK_ZONES]

    async def initialize(self):
        if not NEOTHERM_BASE_URL or not NEOTHERM_API_KEY:
            self.status = "mock"
            logger.info("Neotherm: no credentials — running with mock data")
            return

        try:
            async with httpx.AsyncClient() as client:
                # TODO: replace with the real auth/login endpoint once captured
                resp = await client.get(
                    f"{NEOTHERM_BASE_URL}/zones",
                    headers={"Authorization": f"Bearer {NEOTHERM_API_KEY}"},
                    timeout=10,
                )
                resp.raise_for_status()
                self._zones = resp.json()
                self._mock = False
                self.status = "connected"
        except Exception as exc:
            logger.error("Neotherm init failed: %s — using mock data", exc)
            self.status = "mock"

    @property
    def zones(self) -> list[dict]:
        return self._zones

    async def set_temperature(self, zone_id: str, target: float) -> dict:
        zone = next((z for z in self._zones if z["id"] == zone_id), None)
        if zone is None:
            return {"ok": False, "error": "zone not found"}

        if self._mock:
            zone["target_temp"] = target
            zone["heating"] = target > zone["current_temp"]
            return {"ok": True, "mock": True}

        try:
            async with httpx.AsyncClient() as client:
                # TODO: replace with real set-temperature endpoint once captured
                resp = await client.post(
                    f"{NEOTHERM_BASE_URL}/zones/{zone_id}/temperature",
                    json={"target": target},
                    headers={"Authorization": f"Bearer {NEOTHERM_API_KEY}"},
                    timeout=10,
                )
                resp.raise_for_status()
                zone["target_temp"] = target
                return {"ok": True}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    async def set_mode(self, zone_id: str, mode: str) -> dict:
        if mode not in ("manual", "schedule", "eco", "off"):
            return {"ok": False, "error": "invalid mode"}

        zone = next((z for z in self._zones if z["id"] == zone_id), None)
        if zone is None:
            return {"ok": False, "error": "zone not found"}

        if self._mock:
            zone["mode"] = mode
            return {"ok": True, "mock": True}

        try:
            async with httpx.AsyncClient() as client:
                # TODO: replace with real mode endpoint once captured
                resp = await client.post(
                    f"{NEOTHERM_BASE_URL}/zones/{zone_id}/mode",
                    json={"mode": mode},
                    headers={"Authorization": f"Bearer {NEOTHERM_API_KEY}"},
                    timeout=10,
                )
                resp.raise_for_status()
                zone["mode"] = mode
                return {"ok": True}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}


neotherm_manager = NeothermManager()
