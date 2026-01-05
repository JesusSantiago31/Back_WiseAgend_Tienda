from google.cloud import firestore
from config import SERVICE_ACCOUNT

db = firestore.Client.from_service_account_json(SERVICE_ACCOUNT)
