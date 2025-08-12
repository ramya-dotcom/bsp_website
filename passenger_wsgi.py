import os
import sys

APP_ROOT = os.path.dirname(os.path.abspath(__file__))

if APP_ROOT not in sys.path:
    sys.path.insert(0, APP_ROOT)

# Optional: pin virtualenv interpreter if needed
# INTERP = "/home/mfnssihw/virtualenv/user_verification/3.11/bin/python"
# if sys.executable != INTERP:
#     os.execl(INTERP, INTERP, *sys.argv)

try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=os.path.join(APP_ROOT, ".env"), override=False)
    print("APP_ROOT:", APP_ROOT, flush=True)
    print("LS:", os.listdir(APP_ROOT), flush=True)
except Exception as e:
    print("dotenv load error:", e, flush=True)

from a2wsgi import ASGIMiddleware
from main import app

application = ASGIMiddleware(app)