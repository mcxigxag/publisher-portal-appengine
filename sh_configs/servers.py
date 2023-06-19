from google.cloud import storage
import firebase_admin
from firebase_admin import firestore, auth

firebase_admin.initialize_app()

storage_client = storage.Client()
db = firestore.client()
