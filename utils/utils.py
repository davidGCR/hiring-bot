from google.cloud import storage
import os
import streamlit as st
from vertexai.generative_models import  Part
from constants import *
from prompts import HELP_INSTRUCTIONS
import uuid
import time
from datetime import datetime
import pytz
from google.cloud import pubsub_v1
import re
import json
from utils.file_manager import FileObjectSet
from google.cloud import firestore
import logging
from dotenv import load_dotenv
from google.cloud import logging as gcloud_logging
import requests
from constants import API_URLS
import google.oauth2.id_token
import google.auth.transport.requests   

load_dotenv()
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
LOGGER_NAME = os.getenv("LOGGER_NAME")

logging.basicConfig(level=logging.INFO)

db = firestore.Client()
client = gcloud_logging.Client()
logger = client.logger(LOGGER_NAME)
peru_timezone = pytz.timezone('America/Lima')

def get_current_time():
    return datetime.now(peru_timezone).strftime("%Y-%m-%d %H:%M:%S")

def get_bearer_token(): 
    request = google.auth.transport.requests.Request()
    target_audience = API_URLS["auth"]

    id_token = google.oauth2.id_token.fetch_id_token(request, target_audience)
    return id_token

def get_user_role(email):
    token = get_bearer_token()

    headers = {
        "Authorization": f"Bearer {token}"
    }

    CLOUD_RUN_URL = f"{API_URLS['auth']}/users/{email}"
    response = requests.get(CLOUD_RUN_URL, headers=headers)
    if response.status_code == 200:
        return response.json()  # Return JSON data from the response
    else:
        return {"error": response.text}

def login_user(email, password):
    token = get_bearer_token()

    # Headers including the Bearer token
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Payload to be sent to the API
    payload = {
        "email": email,
        "password": password
    }
    CLOUD_RUN_URL = f"{API_URLS['auth']}/login"

    # Send request to the FastAPI service
    response = requests.post(CLOUD_RUN_URL, json=payload, headers=headers)

    # Check the response
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": response.text}


def initialize_session_state(model=None):
    if "chat_session" not in st.session_state:
        st.session_state.chat_session = model.start_chat(history = [])
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "uploaded_uris_set" not in st.session_state:
        # st.session_state.uploaded_uris_set = FileObjectSet()
        st.session_state.uploaded_uris_set = []
        # st.session_state.uploaded_files = []
        # st.session_state.uploaded_files_uris = []
    if "uploaded_files_memory" not in st.session_state:
        st.session_state.uploaded_files_memory = []
    if "uploaded_xlsx" not in st.session_state:
        st.session_state.uploaded_xlsx = None
    if "xlsx_df" not in st.session_state:
        st.session_state.xlsx_df = None
    if 'user_input_prompt' not in st.session_state: # This one is specifically use for clearing the user text input after they hit enter
        st.session_state.user_input_prompt = 'None'
    if "file_uploader_key" not in st.session_state:
        st.session_state.file_uploader_key = 0
    if "file_uploader_xlsx_key" not in st.session_state:
        st.session_state.file_uploader_xlsx_key = 1000
    if "processing_xlsx" not in st.session_state:
        st.session_state.processing_xlsx = False
    if 'confirmed_upload' not in st.session_state:
        st.session_state.confirmed_upload = False 
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())  # Generate a unique session ID

# Función para subir archivos a Google Cloud Storage
def upload_to_gcs(bucket_name, file, destination_blob_name):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    # Reset the file pointer to the beginning
    file.seek(0)
    
    blob.upload_from_file(file)
    file_uri = f"gs://{bucket_name}/{destination_blob_name}"
    return file_uri

def save_xlsx(uploaded_xlsx):
    destination_blob_name = f"{SUBFOLDER}/{uploaded_xlsx.name}"
    uri = upload_to_gcs(BUCKET_NAME, uploaded_xlsx, destination_blob_name)
    print(f"uri del xlsx enviado a STORAGE: {uri}")
    return uri

def print_chat_history(chat):
    print("Chat History:")
    print(chat.history)

def create_multimodal_message(file_uris: list, prompt: str = ""):
    documents = [Part.from_uri(mime_type="application/pdf", uri=uri) for uri in file_uris]
    multimodal_message = documents + [Part.from_text(prompt)]
    user_input = prompt
    files_log = [{'file_name': uri, 'file_type': 'application/pdf'} for uri in file_uris]
    return multimodal_message, user_input, files_log

# def upload_files_without_uri():
#     """
#     Uploads all UploadedFileObjects with no URI to Google Cloud Storage and updates their URIs in the set.
#     Returns a list of URIs of the recently added files.
#     """
#     if 'uploaded_uris_set' not in st.session_state:
#         raise RuntimeError("Uploaded files set not found in session state.")

#     uploaded_uris_set = st.session_state.uploaded_uris_set
#     new_file_uris = []

#     for file_obj in list(uploaded_uris_set.file_set):
#         if file_obj.uri is None:  # Check if the URI is not set
#             destination_blob_name = f"{SUBFOLDER}/{file_obj.uploaded_file.name}"
#             file_uri = upload_to_gcs(BUCKET_NAME, file_obj.uploaded_file, destination_blob_name)
            
#             # Update the URI in the object
#             file_obj.set_uri(file_uri)
            
#             # Collect the new URI
#             new_file_uris.append(file_uri)

#     return new_file_uris


def display_instructions():
    st.info(HELP_INSTRUCTIONS)

def log_event(event_type, user_id=None, message=None, response=None, files=None, error_message=None, error_details=None):
    log_entry = {
        "severity": "INFO" if error_message is None else "ERROR",
        "session_id": st.session_state.session_id,
        "event": event_type,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    if user_id:
        log_entry["user_id"] = user_id
    if message:
        log_entry["message"] = message
    if response:
        log_entry["response"] = response
    if files:
        log_entry["files"] = files
    if error_message:
        log_entry["error_message"] = error_message
    if error_details:
        log_entry["error_details"] = error_details
    logger.log_struct(log_entry)

def publish_message(publisher, topic_path, df):
    for _, row in df.iterrows():
        data = row.to_json().encode('utf-8')

        try:
            future = publisher.publish(topic_path, data)
            print(f"Published message ID: {future.result()}")
        except Exception as e:
            print(f"Failed to publish message: {e}")

        return 1

def pre_process_xlsx_df(df):
    df.fillna("null", inplace=True)
    # Filter rows with .pdf files
    valid_df = df[df[XLSX_HEADERS["FILE_URL"]].str.endswith('.pdf')]

    # Filter rows with other kinds of documents
    invalid_df = df[~df[XLSX_HEADERS["FILE_URL"]].str.endswith('.pdf')]
    
    return valid_df, invalid_df

# PubSub
def get_pubsub_client():
    """Initialize Google Pub/Sub client"""
    return pubsub_v1.PublisherClient()

def publish_message(message, topic_name):
    """Function to publish a message to a Pub/Sub topic"""
    publisher = get_pubsub_client()
    try:
        topic_path = publisher.topic_path(PROJECT_ID, topic_name)
        future = publisher.publish(topic_path, data=json.dumps(message).encode('utf-8'))
        result = future.result()  # Wait for the publish to complete
        return result
    except Exception as e:
        st.error(f"Failed to publish message. Error: {str(e)}")
        return None

def process_row(row):
    """Function to process each row and publish to Pub/Sub"""

    row_dict = row.to_dict()
    message_data = {
        'file_type': "xlsx",
        'file_name': "prueba.xlsx",
        'data': row_dict,
    }
    result = publish_message(message_data, PUBSUB_XLSX_TOPIC_NAME)
    return result

def get_calification_from_bot(response: str):
    try:
        match = re.search(r'\*\*Calificación:\*\*\s*(.+?)\s*\n', response)
        if not match:
            raise ValueError("Calificación no encontrada en el texto.")
        calificacion = match.group(1)
        return calificacion
    except ValueError as e:
        print(f"Error: {e}")
        return None

def publish_pdf(file_uri: str, bot_response: str):
    """Function to process each row and publish to Pub/Sub"""
    # bot_calification = get_calification_from_bot(bot_response)
    message_data = {
        'file_type': "pdf",
        'file_uri': file_uri,
        'bot_response': bot_response,
        'sent_timestamp': get_current_time()
    }
    result = publish_message(message_data, PUBSUB_PDF_TOPIC_NAME)
    return result
