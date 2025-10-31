import os
import json
from collections.abc import Mapping
import firebase_admin
from firebase_admin import credentials, firestore
try:
    import streamlit as st  # Available in Streamlit Cloud
except Exception:  # Local scripts/tests may not have streamlit loaded here
    st = None

# Initialize Firebase (Cloud-friendly: secrets/env/file fallbacks)
if not firebase_admin._apps:
    init_error = None
    try:
        cred_dict = None

        # 1) Streamlit secrets (supports either a JSON string or a dict)
        if st is not None:
            secrets_val = None
            try:
                secrets_val = st.secrets.get("FIREBASE_CREDENTIALS")
            except Exception:
                secrets_val = None
            if secrets_val:
                if isinstance(secrets_val, str):
                    cred_dict = json.loads(secrets_val)
                elif isinstance(secrets_val, Mapping):
                    cred_dict = dict(secrets_val)

        # 2) Environment variable (JSON string)
        if cred_dict is None:
            env_val = os.getenv("FIREBASE_CREDENTIALS")
            if env_val:
                cred_dict = json.loads(env_val)

        # 3) Local credentials file fallback
        if cred_dict is None and os.path.exists("firebase_credentials.json"):
            cred = credentials.Certificate("firebase_credentials.json")
            firebase_admin.initialize_app(cred)
        elif cred_dict is not None:
            cred = credentials.Certificate(cred_dict)
            project_id = cred_dict.get("project_id") or cred_dict.get("projectId")
            options = {"projectId": project_id} if project_id else None
            firebase_admin.initialize_app(cred, options)
        else:
            # 4) Last resort: try default credentials if available
            # If project id is available in env, Firebase will pick it up; otherwise user must set GOOGLE_CLOUD_PROJECT
            firebase_admin.initialize_app()
    except Exception as e:
        init_error = e
        # Re-raise with a clearer message (Streamlit will redact in UI, but logs keep details)
        raise ValueError("Failed to initialize Firebase app. Ensure FIREBASE_CREDENTIALS are set correctly in Streamlit secrets or environment, or include firebase_credentials.json.") from e

db = firestore.client()