"""
Vercel serverless entry point.
Imports the FastAPI app from backend/ and exposes it as `app` for the Python runtime.
Note: pyaarlo's persistent WebSocket connection is not supported in serverless mode.
The Arlo integration falls back to mock data automatically when credentials are absent.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend"))

from main import app  # noqa: F401  (Vercel picks up `app`)
