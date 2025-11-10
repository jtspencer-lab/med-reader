import os
import pyodbc
from azure.storage.blob import BlobServiceClient
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential

# Azure credentials
FORM_RECOGNIZER_ENDPOINT = "https://<your-form-recognizer>.cognitiveservices.azure.com/"
FORM_RECOGNIZER_KEY = "<your-key>"
BLOB_CONNECTION_STRING = "<your-blob-connection-string>"

# Database connection
DB_CONN_STR = "Driver={ODBC Driver 17 for SQL Server};Server=<your-server>.database.windows.net;Database=<your-db>;Uid=<username>;Pwd=<password>;Encrypt=yes;"

# Initialize clients
blob_service_client = BlobServiceClient.from_connection_string(BLOB_CONNECTION_STRING)
form_recognizer_client = DocumentAnalysisClient(FORM_RECOGNIZER_ENDPOINT, AzureKeyCredential(FORM_RECOGNIZER_KEY))

def upload_to_blob(file_path, container_name):
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=os.path.basename(file_path))
    with open(file_path, "rb") as data:
        blob_client.upload_blob(data)
    return blob_client.url

def extract_data_from_document(blob_url):
    poller = form_recognizer_client.begin_analyze_document_from_url("prebuilt-document", blob_url)
    result = poller.result()
    
    extracted_data = {}
    for page in result.pages:
        for line in page.lines:
            print(line.content)  # Debug
    # TODO: Map fields like Name, DOB, Address using regex or layout
    return extracted_data

def insert_into_db(data):
    conn = pyodbc.connect(DB_CONN_STR)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO MedicalSignup (Name, DOB, Address, Insurance)
        VALUES (?, ?, ?, ?)
    """, (data.get("Name"), data.get("DOB"), data.get("Address"), data.get("Insurance")))
    conn.commit()
    conn.close()

# Example usage
file_path = "sample_form.pdf"
blob_url = upload_to_blob(file_path, "medical-forms")
data = extract_data_from_document(blob_url)
insert_into_db(data)