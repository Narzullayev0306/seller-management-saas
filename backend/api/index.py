"""Vercel serverless entrypoint.

Exposes the FastAPI ASGI app to Vercel's Python runtime while keeping the
existing ``app`` package layout untouched.
"""

import os
import sys

_BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

from app.main import app  # noqa: E402
