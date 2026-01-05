import os
import logging
from google.cloud import firestore
from config import SERVICE_ACCOUNT_INFO, SERVICE_ACCOUNT

logger = logging.getLogger(__name__)

if SERVICE_ACCOUNT_INFO:
    # Create credentials in memory from the JSON info and initialize client
    from google.oauth2 import service_account

    creds = service_account.Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO)
    db = firestore.Client(credentials=creds, project=SERVICE_ACCOUNT_INFO.get("project_id"))

else:
    # If SERVICE_ACCOUNT is set and points to an existing file, try loading it safely
    if SERVICE_ACCOUNT and os.path.exists(SERVICE_ACCOUNT):
        try:
            db = firestore.Client.from_service_account_json(SERVICE_ACCOUNT)
        except Exception:
            logger.exception("Failed to initialize Firestore from service account file; falling back to ADC")
            db = firestore.Client()
    else:
        # No file available; use Application Default Credentials
        logger.info("No service account file provided or file missing; using Application Default Credentials.")
        db = firestore.Client()
