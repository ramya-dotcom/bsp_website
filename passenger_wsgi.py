import os
import sys

# Absolute path to the application root (folder containing main.py and .env)
APP_ROOT = os.path.dirname(os.path.abspath(__file__))

# Ensure app root is importable
if APP_ROOT not in sys.path:
    sys.path.insert(0, APP_ROOT)

# Optional: force Passenger to use the app's virtualenv interpreter (uncomment and set correct version)
# INTERP = "/home/mfnssihw/virtualenv/user_verification/3.11/bin/python"
# if sys.executable != INTERP:
#     os.execl(INTERP, INTERP, *sys.argv)

# Load environment early (if relying on .env)
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=os.path.join(APP_ROOT, ".env"), override=False)
except Exception:
    pass  # Safe to continue; env vars may be set via cPanel UI

# Wrap FastAPI (ASGI) app for Passenger (WSGI) using a2wsgi
from a2wsgi import ASGIMiddleware

# Import the FastAPI app from main.py (must be in the same folder as this file)
from main import app  # FastAPI instance

# WSGI callable for Passenger
application = ASGIMiddleware(app)
