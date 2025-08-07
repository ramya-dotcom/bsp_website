import fitz  # PyMuPDF
import re
from pathlib import Path
import io
from PIL import Image
import pytesseract
import shutil
import os
import uuid
from datetime import date, datetime, timedelta

# --- Imports for .env and MySQL ---
from dotenv import load_dotenv
import mysql.connector

# --- FastAPI and Pydantic Imports ---
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Annotated, List

# --- Load Environment Variables ---
load_dotenv()

# --- Configuration: Define Storage Directories ---
# We now add a temporary directory for unverified files
TEMP_UPLOAD_DIR = Path("/home/mfnssihw/volunteers_files/temp")
PDF_UPLOAD_DIR = Path("/home/mfnssihw/volunteers_files/voterid_proof")
PHOTO_UPLOAD_DIR = Path("/home/mfnssihw/volunteers_files/photos")

# --- In-Memory State Management (for demonstration) ---
# Stores {verification_token: {path: "...", epic: "...", expiry: ...}}
VERIFICATION_SESSIONS = {}

# --- Initialize FastAPI App ---
app = FastAPI(
    title="Membership Workflow API",
    description="A multi-step API for document verification, member creation, and payment handling.",
    version="2.0.0"
)

# --- Pydantic Models ---
class MemberCreate(BaseModel):
    name: str = Field(..., description="Full Name")
    membership_no: str = Field(..., description="Membership Number")
    active_no: str | None = None
    profession: str | None = None
    designation: str | None = None
    mandal: str | None = None
    dob: date | None = Field(None, description="Date of Birth")
    blood_group: str | None = Field(None, description="Blood Group")
    contact_no: str = Field(..., description="Contact Number")
    address: str | None = None

class PaymentUpdate(BaseModel):
    member_id: int
    status: str # "successful" or "failed"

# --- Database and File System Management ---
def get_db_connection():
    try:
        return mysql.connector.connect(
            host=os.getenv("DATABASE_HOST"), user=os.getenv("DATABASE_USERNAME"),
            password=os.getenv("DATABASE_PASSWORD"), database=os.getenv("DATABASE_NAME")
        )
    except mysql.connector.Error as err:
        print(f"Database connection error: {err}"); return None

def cleanup_files(files_to_delete: List[Path]):
    for file_path in files_to_delete:
        try:
            if file_path and file_path.exists(): os.remove(file_path)
        except OSError as e: print(f"Error deleting file {file_path}: {e}")

# --- PDF Processing Functions (No changes) ---
def find_epic_in_text(text):
    if not text: return None
    patterns = [r'(?i)(?:EPIC No|Identity Card)\s*.*?\s*\b([A-Z]{3}[0-9]{7})\b', r'\b([A-Z]{3}[0-9]{7})\b']
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match: return match.group(1).strip().replace(" ", "")
    return None

def extract_epic_from_pdf(pdf_path: Path):
    try:
        doc = fitz.open(pdf_path)
        full_text = "".join(page.get_text() for page in doc)
        epic = find_epic_in_text(full_text)
        if epic: doc.close(); return epic
        ocr_text = ""
        for page in doc:
            pix = page.get_pixmap(dpi=300); img_data = pix.tobytes("png"); pil_image = Image.open(io.BytesIO(img_data)); ocr_text += pytesseract.image_to_string(pil_image, lang='eng')
        doc.close()
        return find_epic_in_text(ocr_text)
    except Exception as e: print(f"PDF processing error: {e}"); return None

# --- Startup Event ---
@app.on_event("startup")
def on_startup():
    print("Ensuring upload directories exist...")
    for dir_path in [TEMP_UPLOAD_DIR, PDF_UPLOAD_DIR, PHOTO_UPLOAD_DIR]:
        os.makedirs(dir_path, exist_ok=True)
    print("✅ Upload directories are ready.")

# --- API ENDPOINT 1: Document Verification ---
@app.post("/verify-document/")
async def verify_document_endpoint(
    epic_number: Annotated[str, Form()], 
    pdf_file: Annotated[UploadFile, File()]
):
    safe_epic = epic_number.strip().upper()
    temp_pdf_path = TEMP_UPLOAD_DIR / f"{uuid.uuid4()}_{Path(pdf_file.filename).name}"

    try:
        with temp_pdf_path.open("wb") as buffer:
            shutil.copyfileobj(pdf_file.file, buffer)
    finally:
        pdf_file.file.close()

    extracted_epic = extract_epic_from_pdf(temp_pdf_path)

    if not extracted_epic or safe_epic != extracted_epic:
        cleanup_files([temp_pdf_path])
        detail = "Could not extract a matching EPIC number from the PDF."
        if extracted_epic:
            detail = f"Mismatch: Entered EPIC '{safe_epic}' does not match PDF EPIC '{extracted_epic}'."
        raise HTTPException(status_code=400, detail=detail)

    # Verification successful, create a short-lived token
    token = str(uuid.uuid4())
    VERIFICATION_SESSIONS[token] = {
        "temp_pdf_path": temp_pdf_path,
        "epic": extracted_epic,
        "expiry": datetime.utcnow() + timedelta(minutes=15) # Token is valid for 15 minutes
    }
    
    return {
        "message": "Verification successful. Use this token to submit member details.",
        "verification_token": token
    }

# --- API ENDPOINT 2: Submit Member Details ---
@app.post("/submit-details/")
async def submit_details_endpoint(
    verification_token: Annotated[str, Form()],
    photo_file: Annotated[UploadFile, File()],
    member_data: MemberCreate = Depends()
):
    session = VERIFICATION_SESSIONS.get(verification_token)
    if not session or session["expiry"] < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Invalid or expired verification token. Please verify again.")

    temp_pdf_path = session["temp_pdf_path"]
    epic_number = session["epic"]

    # Move verified PDF to permanent storage
    unique_id = str(uuid.uuid4().hex)[:8]
    pdf_filename = f"{epic_number}_{unique_id}_{temp_pdf_path.name}"
    permanent_pdf_path = PDF_UPLOAD_DIR / pdf_filename
    shutil.move(str(temp_pdf_path), str(permanent_pdf_path))
    
    # Save photo to permanent storage
    photo_filename = f"{epic_number}_{unique_id}_{Path(photo_file.filename).name}"
    permanent_photo_path = PHOTO_UPLOAD_DIR / photo_filename
    try:
        with permanent_photo_path.open("wb") as buffer:
            shutil.copyfileobj(photo_file.file, buffer)
    finally:
        photo_file.file.close()

    # Create member record in DB with 'pending_payment' status
    conn = get_db_connection()
    if not conn:
        cleanup_files([permanent_pdf_path, permanent_photo_path])
        raise HTTPException(status_code=503, detail="Database service is unavailable.")
        
    cursor = None
    try:
        cursor = conn.cursor()
        sql = """INSERT INTO members (name, membership_no, active_no, profession, designation, mandal, dob, blood_group, contact_no, address, pdf_proof_path, photo_path, status)
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        values = (member_data.name, member_data.membership_no, member_data.active_no, member_data.profession, member_data.designation, member_data.mandal, member_data.dob, member_data.blood_group, member_data.contact_no, member_data.address, str(permanent_pdf_path), str(permanent_photo_path), 'pending_payment')
        cursor.execute(sql, values)
        new_member_id = cursor.lastrowid
        conn.commit()
    except mysql.connector.Error as err:
        cleanup_files([permanent_pdf_path, permanent_photo_path])
        if err.errno == 1062:
            raise HTTPException(status_code=409, detail=f"A member with membership number '{member_data.membership_no}' already exists.")
        raise HTTPException(status_code=500, detail="Failed to create member in the database.")
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()
        del VERIFICATION_SESSIONS[verification_token] # Clean up used token

    return {"message": "Details submitted. Proceed to payment.", "member_id": new_member_id}

# --- API ENDPOINT 3: Update Payment Status ---
@app.post("/update-payment/")
async def update_payment_endpoint(update_data: PaymentUpdate):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=503, detail="Database service is unavailable.")
        
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        if update_data.status.lower() == "successful":
            cursor.execute("UPDATE members SET status = 'active' WHERE id = %s", (update_data.member_id,))
            conn.commit()
            return {"message": f"Payment successful. Member {update_data.member_id} is now active."}
        
        elif update_data.status.lower() == "failed":
            # First, get file paths to delete them
            cursor.execute("SELECT pdf_proof_path, photo_path FROM members WHERE id = %s", (update_data.member_id,))
            record = cursor.fetchone()
            if record:
                cleanup_files([Path(record['pdf_proof_path']), Path(record['photo_path'])])
            
            # Now, delete the database record
            cursor.execute("DELETE FROM members WHERE id = %s", (update_data.member_id,))
            conn.commit()
            return {"message": f"Payment failed. Member {update_data.member_id} and associated files have been deleted."}
        
        else:
            raise HTTPException(status_code=400, detail="Invalid status. Must be 'successful' or 'failed'.")
    
    except mysql.connector.Error as err:
        print(f"Database update/delete error: {err}")
        raise HTTPException(status_code=500, detail="A database error occurred.")
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()

