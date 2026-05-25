import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from devices.arlo import arlo_manager
from devices.neotherm import neotherm_manager

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await arlo_manager.initialize()
    await neotherm_manager.initialize()
    yield
    arlo_manager.cleanup()


app = FastAPI(title="Home Hub", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Overview ──────────────────────────────────────────────────────────────────

@app.get("/api/devices")
async def get_devices():
    return {
        "arlo": {
            "status": arlo_manager.status,
            "camera_count": len(arlo_manager.cameras),
        },
        "neotherm": {
            "status": neotherm_manager.status,
            "zone_count": len(neotherm_manager.zones),
        },
    }


# ── Arlo ──────────────────────────────────────────────────────────────────────

@app.get("/api/arlo/cameras")
async def get_cameras():
    return arlo_manager.cameras


@app.get("/api/arlo/mode")
async def get_mode():
    return arlo_manager.mode


class ModeRequest(BaseModel):
    mode: str


@app.post("/api/arlo/base/{base_id}/mode")
async def set_mode(base_id: str, body: ModeRequest):
    result = await arlo_manager.set_mode(base_id, body.mode)
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@app.post("/api/arlo/cameras/{camera_id}/snapshot")
async def request_snapshot(camera_id: str):
    return await arlo_manager.request_snapshot(camera_id)


# ── Neotherm ──────────────────────────────────────────────────────────────────

@app.get("/api/neotherm/zones")
async def get_zones():
    return neotherm_manager.zones


class TempRequest(BaseModel):
    target: float


@app.post("/api/neotherm/zones/{zone_id}/temperature")
async def set_temperature(zone_id: str, body: TempRequest):
    if not (5.0 <= body.target <= 35.0):
        raise HTTPException(status_code=400, detail="Temperature must be between 5 and 35°C")
    result = await neotherm_manager.set_temperature(zone_id, body.target)
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


class ModeBody(BaseModel):
    mode: str


@app.post("/api/neotherm/zones/{zone_id}/mode")
async def set_zone_mode(zone_id: str, body: ModeBody):
    result = await neotherm_manager.set_mode(zone_id, body.mode)
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result
