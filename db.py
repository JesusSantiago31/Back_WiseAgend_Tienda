from google.cloud import firestore
from config import SERVICE_ACCOUNT_INFO, SERVICE_ACCOUNT

if SERVICE_ACCOUNT_INFO:
    # Create credentials in memory from the JSON info and initialize client
    from google.oauth2 import service_account

    creds = service_account.Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO)
    db = firestore.Client(credentials=creds, project=SERVICE_ACCOUNT_INFO.get("project_id"))

elif SERVICE_ACCOUNT:
    # Fallback to local json file (not committed to git)
    db = firestore.Client.from_service_account_json(SERVICE_ACCOUNT)

else:
    # Fall back to Application Default Credentials (e.g., set up in Render via service integration)
    db = firestore.Client()
