"""
Arlo integration using Arlo's REST API directly — no pyaarlo dependency.
Works in both Vercel serverless and local dev.

If your Arlo account has 2FA enabled, set ARLO_TFA_TYPE=imap and provide
ARLO_IMAP_* credentials so the server can read the code from your email.
To skip 2FA entirely: disable it on my.arlo.com → Account → Security.
"""

import os
import logging
import httpx

logger = logging.getLogger(__name__)

_AUTH_URL = "https://ocapi-app.arlo.com/api/auth"
_DEVICES_URL = "https://myapi.arlo.com/hmsweb/users/devices"
_MFA_START = "https://ocapi-app.arlo.com/api/startAuth"
_MFA_FINISH = "https://ocapi-app.arlo.com/api/finishAuth"

_BASE_HEADERS = {
    "Content-Type": "application/json",
    "Referer": "https://my.arlo.com/",
    "schemaVersion": "1",
    "DNT": "1",
}

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

_CAMERA_TYPES = {"camera", "arloq", "arloqs", "arloqtc", "doorbell"}


class ArloManager:
    def __init__(self):
        self._token: str | None = None
        self._raw_cameras: list[dict] = []
        self.status = "not_configured"
        self._mock = True

    async def initialize(self):
        # If a pre-authenticated token is set (e.g. from the setup script), use it directly.
        token = os.getenv("ARLO_TOKEN", "").strip()
        if token:
            await self._connect_with_token(token)
            return

        email = os.getenv("ARLO_EMAIL", "").strip()
        password = os.getenv("ARLO_PASSWORD", "").strip()

        if not email or not password or email == "your@email.com":
            self.status = "not_configured"
            return

        try:
            self.status = "connecting"
            async with httpx.AsyncClient(headers=_BASE_HEADERS, timeout=20) as client:
                token, err = await _login(client, email, password)

                if err == "needs_2fa":
                    token, err = await _handle_2fa(client, email)

                if err or not token:
                    self.status = err or "error"
                    logger.warning("Arlo auth failed: %s", err)
                    return

                self._token = token
                devices = await _fetch_devices(client, token)
                self._raw_cameras = [
                    d for d in devices
                    if d.get("deviceType", "").lower() in _CAMERA_TYPES
                ]
                self._mock = False
                self.status = "connected"
                logger.info("Arlo connected — %d camera(s)", len(self._raw_cameras))

        except Exception as exc:
            self.status = "error"
            logger.error("Arlo init failed: %s", exc)

    async def _connect_with_token(self, token: str):
        try:
            self.status = "connecting"
            async with httpx.AsyncClient(headers=_BASE_HEADERS, timeout=20) as client:
                devices = await _fetch_devices(client, token)
                self._token = token
                self._raw_cameras = [
                    d for d in devices
                    if d.get("deviceType", "").lower() in _CAMERA_TYPES
                ]
                self._mock = False
                self.status = "connected"
                logger.info("Arlo connected via token — %d camera(s)", len(self._raw_cameras))
        except Exception as exc:
            self.status = "error"
            logger.error("Arlo token auth failed: %s", exc)

    @property
    def cameras(self) -> list[dict]:
        if self._mock:
            return MOCK_CAMERAS
        return [_format_camera(d) for d in self._raw_cameras]

    @property
    def mode(self) -> dict:
        return {"base_stations": []}

    async def set_mode(self, base_id: str, mode: str) -> dict:
        return {"ok": True, "mock": self._mock}

    async def request_snapshot(self, camera_id: str) -> dict:
        if self._mock or not self._token:
            return {"ok": True, "mock": True, "url": None}
        cam = next((c for c in self._raw_cameras if c.get("deviceId") == camera_id), None)
        if not cam:
            return {"ok": False, "error": "camera not found"}
        props = cam.get("properties", {})
        return {"ok": True, "url": props.get("presignedLastImageUrl")}

    def cleanup(self):
        pass  # stateless — nothing to close


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _login(client: httpx.AsyncClient, email: str, password: str):
    resp = await client.post(
        _AUTH_URL,
        json={"email": email, "password": password, "language": "en", "EnvType": "prod"},
    )
    if resp.status_code != 200:
        return None, "error"
    body = resp.json().get("data", {})
    if body.get("authenticated"):
        return body.get("token"), None
    return None, "needs_2fa"


async def _handle_2fa(client: httpx.AsyncClient, email: str):
    """Attempt IMAP-based 2FA. Only runs if ARLO_TFA_TYPE=imap."""
    if os.getenv("ARLO_TFA_TYPE", "").lower() != "imap":
        logger.warning("Arlo 2FA required. Set ARLO_TFA_TYPE=imap or disable 2FA on your account.")
        return None, "needs_2fa"

    try:
        import imaplib, email as email_lib, re, time
        imap_host = os.getenv("ARLO_IMAP_HOST", "imap.gmail.com")
        imap_user = os.getenv("ARLO_IMAP_USER", "")
        imap_pass = os.getenv("ARLO_IMAP_PASSWORD", "")

        await client.get(_MFA_START)
        time.sleep(8)  # wait for Arlo to send the email

        code = _read_imap_code(imap_host, imap_user, imap_pass)
        if not code:
            return None, "needs_2fa"

        resp = await client.post(_MFA_FINISH, json={"code": code})
        body = resp.json().get("data", {})
        if body.get("authenticated"):
            return body.get("token"), None
        return None, "needs_2fa"
    except Exception as exc:
        logger.error("IMAP 2FA failed: %s", exc)
        return None, "needs_2fa"


def _read_imap_code(host: str, user: str, password: str) -> str | None:
    try:
        import imaplib, email as email_lib, re
        mail = imaplib.IMAP4_SSL(host)
        mail.login(user, password)
        mail.select("INBOX")
        _, data = mail.search(None, 'FROM "arlo" UNSEEN')
        ids = data[0].split()
        if not ids:
            return None
        _, msg_data = mail.fetch(ids[-1], "(RFC822)")
        msg = email_lib.message_from_bytes(msg_data[0][1])
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode()
                    break
        else:
            body = msg.get_payload(decode=True).decode()
        match = re.search(r"\b(\d{6})\b", body)
        return match.group(1) if match else None
    except Exception:
        return None


async def _fetch_devices(client: httpx.AsyncClient, token: str) -> list[dict]:
    resp = await client.get(_DEVICES_URL, headers={"auth_token": token})
    resp.raise_for_status()
    return resp.json().get("data", [])


def _format_camera(d: dict) -> dict:
    props = d.get("properties", {})
    return {
        "id": d.get("deviceId", ""),
        "name": d.get("deviceName", "Camera"),
        "battery": props.get("batteryLevel"),
        "signal": props.get("signalStrength"),
        "state": d.get("state", "idle"),
        "last_image": props.get("presignedLastImageUrl") or props.get("presignedFullFrameSnapshotUrl"),
        "model": d.get("modelId", ""),
    }


arlo_manager = ArloManager()
