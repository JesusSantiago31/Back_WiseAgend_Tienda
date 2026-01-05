import os
import json

API_TOKEN = os.environ.get("API_TOKEN", "MI_TOKEN_SEGURO_123")

# If you set SERVICE_ACCOUNT_JSON in Render (or locally), it should contain the whole
# service account JSON as a single environment variable (escaped/newlines preserved).
SERVICE_ACCOUNT_JSON = os.environ.get("SERVICE_ACCOUNT_JSON")

SERVICE_ACCOUNT_INFO = None
if SERVICE_ACCOUNT_JSON:
    try:
        SERVICE_ACCOUNT_INFO = json.loads(SERVICE_ACCOUNT_JSON)
    except Exception:
        # If parsing fails, leave as None and other methods will be used
        SERVICE_ACCOUNT_INFO = None

# Fallback to checking for a local key file (kept out of git).
# Prefer explicit env var `SERVICE_ACCOUNT_PATH` in short-lived environments like Render.
SERVICE_ACCOUNT = os.environ.get("SERVICE_ACCOUNT_PATH")
if SERVICE_ACCOUNT is None:
    try:
        if not SERVICE_ACCOUNT_INFO and os.path.exists("serviceAccountKey.json"):
            SERVICE_ACCOUNT = "serviceAccountKey.json"
    except Exception:
        # Some hosting environments may restrict filesystem checks; don't error out.
        SERVICE_ACCOUNT = None
