"""
QuestForge - Vercel Serverless Function Entrypoint
Exposes the FastAPI application as an ASGI handler for Vercel Serverless.
"""

import sys
import os
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent

for path in [str(PROJECT_ROOT), str(PROJECT_ROOT / "backend")]:
    if path not in sys.path:
        sys.path.insert(0, path)

# Enable Neon Postgres and safe serverless defaults
os.environ.setdefault("USE_NEON", "true")
os.environ.setdefault("SANDBOX_TYPE", "subprocess")
os.environ.setdefault("TESTING", "False")

try:
    from backend.app.main import app
except Exception as e:
    import traceback
    print(f"QuestForge Serverless Initialization Error: {e}", file=sys.stderr)
    traceback.print_exc()
    raise e
