import os
import psycopg2
import spacy
import re
import logging
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential

# Configure logging
logging.basicConfig(filename='processing.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Azure Form Recognizer credentials
AZURE_ENDPOINT = "https://<your-form-recognizer-endpoint>.cognitiveservices.azure.com/"
AZURE_KEY = "<your-form-recognizer-key>"

# Initialize Azure client
try:
    document_client = DocumentAnalysisClient(endpoint=AZURE_ENDPOINT, credential=AzureKeyCredential(AZURE_KEY))
    logging.info("Azure Form Recognizer client initialized successfully.")
except Exception as e:
    logging.error(f"Failed to initialize Azure Form Recognizer client: {e}")
    raise

# Load NLP model
try:
    nlp = spacy.load("en_core_web_sm")
    logging.info("SpaCy NLP model loaded successfully.")
except Exception as e:
    logging.error(f"Failed to load SpaCy model: {e}")
    raise

# Database connection
try:
    conn = psycopg2.connect(
        dbname="healthcare_db",
        user="db_user",
        password="db_pass",
        host="localhost",
        port="5432"
    )
    cursor = conn.cursor()
    logging.info("Database connection established successfully.")
except psycopg2.Error as e:
    logging.error(f"Database connection error: {e}")
    raise

# Step 1: OCR using Azure Form Recognizer
def extract_text_from_image(image_path):
    try:
        with open(image_path, "rb") as f:
            poller = document_client.begin_analyze_document("prebuilt-document", document=f)
        result = poller.result()
        text = " ".join([line.content for page in result.pages for line in page.lines])
        return text
    except Exception as e:
        logging.error(f"Error extracting text from {image_path}: {e}")
        return None

# Step 2: NLP validation & cleaning
def clean_and_validate(text):
    try:
        doc = nlp(text)
        data = {
            "name": {"value": None, "confidence": 0},
            "dob": {"value": None, "confidence": 0},
            "insurance_id": {"value": None, "confidence": 0}
        }
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                data["name"]["value"] = ent.text
                data["name"]["confidence"] = getattr(ent._, "confidence", 0.8)
            elif ent.label_ == "DATE":
                data["dob"]["value"] = re.sub(r"[^0-9-]", "", ent.text)
                data["dob"]["confidence"] = 0.7
            elif "insurance" in ent.text.lower():
                data["insurance_id"]["value"] = ent.text
                data["insurance_id"]["confidence"] = 0.6
        return data
    except Exception as e:
        logging.error(f"Error during NLP validation: {e}")
        return None

# Step 3: Confidence check
def needs_review(data, threshold=0.75):
    try:
        return {k: v for k, v in data.items() if v["confidence"] < threshold}
    except Exception as e:
        logging.error(f"Error checking confidence: {e}")
        return {}

# Step 4: Insert into DB
def insert_into_db(data):
    try:
        if conn.closed:
            logging.warning("Database connection is closed. Attempting reconnect...")
        cursor.execute("""
            INSERT INTO patients (name, dob, insurance_id)
            VALUES (%s, %s, %s)
        """, (data["name"]["value"], data["dob"]["value"], data["insurance_id"]["value"]))
        conn.commit()
        logging.info(f"Inserted data into database: {data}")
    except psycopg2.Error as e:
        logging.error(f"Database error: {e}")

# Batch processing
def process_batch(folder_path):
    for file_name in os.listdir(folder_path):
        try:
            if file_name.lower().endswith(('.jpg', '.jpeg', '.png', '.tiff', '.pdf')):
                image_path = os.path.join(folder_path, file_name)
                logging.info(f"Processing: {image_path}")
                text = extract_text_from_image(image_path)
                if not text or text.strip() == "":
                    logging.warning(f"No text extracted from {file_name}. Skipping...")
                    continue
                cleaned_data = clean_and_validate(text)
                if not cleaned_data:
                    logging.warning(f"Failed to clean and validate data for {file_name}. Skipping...")
                    continue
                review_fields = needs_review(cleaned_data)
                if review_fields:
                    logging.warning(f"Low confidence fields for {file_name}: {review_fields}")
                else:
                    insert_into_db(cleaned_data)
        except Exception as e:
            logging.error(f"Error processing {file_name}: {e}")
    logging.info("Batch processing completed!")

# Run batch with graceful shutdown
try:
    process_batch("scanned_forms_folder")
except Exception as e:
    logging.error(f"Unexpected error during batch processing: {e}")
finally:
    try:
        cursor.close()
        conn.close()
        logging.info("Database connection closed successfully.")
    except Exception as e:
        logging.error(f"Error closing database connection: {e}")