import asyncio
import os
import logging
from typing import Any

logger = logging.getLogger(__name__)

MOCK_CAMERAS = [
    {
        "id": "mock-cam-1",
        "name": "Front Door",
        "battery": 87,
        "signal": 4,
        "state": "idle",
        "last_image": None,
        "model": "VMC4050P",
    },
    {
        "id": "mock-cam-2",
        "name": "Backyard",
        "battery": 62,
        "signal": 3,
        "state": "idle",
        "last_image": None,
        "model": "VMC4050P",
    },
]


class ArloManager:
    def __init__(self):
        self._ar = None
        self.status = "not_configured"
        self._mock = True

    async def initialize(self):
        email = os.getenv("ARLO_EMAIL")
        password = os.getenv("ARLO_PASSWORD")
        tfa_type = os.getenv("ARLO_TFA_TYPE", "push")

        if not email or not password or email == "your@email.com":
            self.status = "not_configured"
            return

        try:
            self.status = "connecting"
            loop = asyncio.get_event_loop()

            kwargs: dict[str, Any] = {
                "username": email,
                "password": password,
                "tfa_type": tfa_type,
                "storage_dir": "/tmp/pyaarlo",
            }

            if tfa_type == "imap":
                kwargs["tfa_host"] = os.getenv("ARLO_IMAP_HOST", "imap.gmail.com")
                kwargs["tfa_username"] = os.getenv("ARLO_IMAP_USER", email)
                kwargs["tfa_password"] = os.getenv("ARLO_IMAP_PASSWORD", "")

            import pyaarlo

            ar = await loop.run_in_executor(
                None, lambda: pyaarlo.PyArlo(**kwargs)
            )
            connected = await loop.run_in_executor(
                None, lambda: ar.wait_for_connected(timeout=30)
            )

            if connected:
                self._ar = ar
                self._mock = False
                self.status = "connected"
                logger.info("Arlo connected — %d camera(s) found", len(ar.cameras))
            else:
                self.status = "timeout"
                logger.warning("Arlo connection timed out — falling back to mock data")

        except Exception as exc:
            self.status = "error"
            logger.error("Arlo init failed: %s", exc)

    @property
    def cameras(self) -> list[dict]:
        if self._mock or self._ar is None:
            return MOCK_CAMERAS

        result = []
        for cam in self._ar.cameras:
            result.append(
                {
                    "id": cam.device_id,
                    "name": cam.name,
                    "battery": cam.battery_level,
                    "signal": cam.signal_strength,
                    "state": cam.state,
                    "last_image": cam.last_image,
                    "model": cam.model_id,
                }
            )
        return result

    @property
    def mode(self) -> dict:
        if self._mock or self._ar is None:
            return {"mode": "mock", "base_stations": []}

        bases = []
        for base in self._ar.base_stations:
            bases.append({"id": base.device_id, "name": base.name, "mode": base.mode})
        return {"base_stations": bases}

    async def set_mode(self, base_id: str, mode: str) -> dict:
        if self._mock or self._ar is None:
            return {"ok": True, "mock": True}

        if mode not in ("armed", "disarmed", "schedule"):
            return {"ok": False, "error": "invalid mode"}

        loop = asyncio.get_event_loop()
        for base in self._ar.base_stations:
            if base.device_id == base_id:
                await loop.run_in_executor(None, lambda: base.set_base_station_mode(mode))
                return {"ok": True}
        return {"ok": False, "error": "base station not found"}

    async def request_snapshot(self, camera_id: str) -> dict:
        if self._mock or self._ar is None:
            return {"ok": True, "mock": True, "url": None}

        loop = asyncio.get_event_loop()
        for cam in self._ar.cameras:
            if cam.device_id == camera_id:
                await loop.run_in_executor(None, cam.request_snapshot)
                return {"ok": True, "url": cam.last_image}
        return {"ok": False, "error": "camera not found"}

    def cleanup(self):
        if self._ar is not None:
            try:
                self._ar.stop()
            except Exception:
                pass


arlo_manager = ArloManager()
