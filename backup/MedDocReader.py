import os
import psycopg2
import spacy
import re
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential

# Azure Form Recognizer credentials
AZURE_ENDPOINT = "https://<your-form-recognizer-endpoint>.cognitiveservices.azure.com/"
AZURE_KEY = "<your-form-recognizer-key>"

# Initialize Azure client
document_client = DocumentAnalysisClient(endpoint=AZURE_ENDPOINT, credential=AzureKeyCredential(AZURE_KEY))

# Load NLP model (replace with ClinicalBERT for healthcare)
nlp = spacy.load("en_core_web_sm")

# Database connection
conn = psycopg2.connect(
    dbname="healthcare_db",
    user="db_user",
    password="db_pass",
    host="localhost",
    port="5432"
)
cursor = conn.cursor()

# Step 1: OCR using Azure Form Recognizer
def extract_text_from_image(image_path):
    with open(image_path, "rb") as f:
        poller = document_client.begin_analyze_document("prebuilt-document", document=f)
    result = poller.result()
    
    # Combine all text lines
    text = " ".join([line.content for page in result.pages for line in page.lines])
    return text

# Step 2: NLP validation & cleaning with confidence scoring
def clean_and_validate(text):
    doc = nlp(text)
    data = {
        "name": {"value": None, "confidence": 0},
        "dob": {"value": None, "confidence": 0},
        "insurance_id": {"value": None, "confidence": 0}
    }
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            data["name"]["value"] = ent.text
            data["name"]["confidence"] = ent._.confidence if hasattr(ent._, "confidence") else 0.8
        elif ent.label_ == "DATE":
            data["dob"]["value"] = re.sub(r"[^0-9-]", "", ent.text)
            data["dob"]["confidence"] = 0.7
        elif "insurance" in ent.text.lower():
            data["insurance_id"]["value"] = ent.text
            data["insurance_id"]["confidence"] = 0.6
    return data

# Step 3: Human review for low-confidence fields
def needs_review(data, threshold=0.75):
    low_conf_fields = {k: v for k, v in data.items() if v["confidence"] < threshold}
    return low_conf_fields

# Step 4: Insert into SQL database
def insert_into_db(data):
    cursor.execute("""
        INSERT INTO patients (name, dob, insurance_id)
        VALUES (%s, %s, %s)
    """, (data["name"]["value"], data["dob"]["value"], data["insurance_id"]["value"]))
    conn.commit()

# Batch processing
def process_batch(folder_path):
    for file_name in os.listdir(folder_path):
        if file_name.lower().endswith(('.jpg', '.jpeg', '.png', '.tiff', '.pdf')):
            image_path = os.path.join(folder_path, file_name)
            print(f"Processing: {image_path}")
            text = extract_text_from_image(image_path)
            cleaned_data = clean_and_validate(text)
            
            # Check confidence
            review_fields = needs_review(cleaned_data)
            if review_fields:
                print(f"⚠ Low confidence fields for {file_name}: {review_fields}")
                # Optionally: send to human review queue or dashboard
            else:
                insert_into_db(cleaned_data)
    print("Batch processing completed!")

# Run batch
process_batch("scanned_forms_folder")
``