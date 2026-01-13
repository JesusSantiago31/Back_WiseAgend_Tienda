import os
import logging
from google.cloud import firestore
from config import SERVICE_ACCOUNT_INFO, SERVICE_ACCOUNT

import firebase_admin
from firebase_admin import credentials as firebase_credentials

logger = logging.getLogger(__name__)

if SERVICE_ACCOUNT_INFO:
    from google.oauth2 import service_account

    creds = service_account.Credentials.from_service_account_info(
        SERVICE_ACCOUNT_INFO
    )

    db = firestore.Client(
        credentials=creds,
        project=SERVICE_ACCOUNT_INFO.get("project_id")
    )

    # 🔥 Firebase Admin (OBLIGATORIO EN RENDER)
    if not firebase_admin._apps:
        firebase_admin.initialize_app(
            firebase_credentials.Certificate(SERVICE_ACCOUNT_INFO)
        )

else:
    if SERVICE_ACCOUNT and os.path.exists(SERVICE_ACCOUNT):
        try:
            db = firestore.Client.from_service_account_json(SERVICE_ACCOUNT)

            if not firebase_admin._apps:
                firebase_admin.initialize_app(
                    firebase_credentials.Certificate(SERVICE_ACCOUNT)
                )

        except Exception:
            logger.exception(
                "Failed to initialize Firestore from service account file"
            )
            db = firestore.Client()
    else:
        logger.info(
            "No service account provided; Firebase Auth will NOT work."
        )
        db = firestore.Client()
