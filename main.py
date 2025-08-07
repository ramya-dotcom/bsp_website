import fitz  # PyMuPDF
import re
from pathlib import Path
import io
from PIL import Image
import pytesseract
import shutil
import os
import uuid
from datetime import date

# --- Imports for .env and MySQL ---
from dotenv import load_dotenv
import mysql.connector

# --- FastAPI and Pydantic Imports ---
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Annotated, List

# --- Load Environment Variables ---
load_dotenv()

# --- Configuration: Define Permanent Storage Directories ---
PDF_UPLOAD_DIR = Path("/home/mfnssihw/volunteers_files/voterid_proof")
PHOTO_UPLOAD_DIR = Path("/home/mfnssihw/volunteers_files/photos")

# --- Initialize FastAPI App ---
app = FastAPI(
    title="Membership Creation API",
    description="An API to verify documents, create new members, and return their unique ID.",
    version="1.2.0"
)

# --- Pydantic Model for Member Data ---
# This model defines the data expected from the form.
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


# --- Database and File System Management ---

def get_db_connection():
    """Establishes and returns a connection to the MySQL database."""
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DATABASE_HOST"),
            user=os.getenv("DATABASE_USERNAME"),
            password=os.getenv("DATABASE_PASSWORD"),
            database=os.getenv("DATABASE_NAME")
        )
        return connection
    except mysql.connector.Error as err:
        print(f"Database connection error: {err}")
        return None

def create_member_in_db(member_data: MemberCreate, pdf_path: str, photo_path: str):
    """Inserts a new member into the database and returns their new ID."""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=503, detail="Database service is unavailable.")
    
    cursor = None
    try:
        cursor = conn.cursor()
        sql = """
            INSERT INTO members (name, membership_no, active_no, profession, designation, mandal, dob, blood_group, contact_no, address, pdf_proof_path, photo_path)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            member_data.name, member_data.membership_no, member_data.active_no, 
            member_data.profession, member_data.designation, member_data.mandal, 
            member_data.dob, member_data.blood_group, member_data.contact_no, 
            member_data.address, pdf_path, photo_path
        )
        cursor.execute(sql, values)
        conn.commit()
        # Return the ID of the newly created record
        return cursor.lastrowid
    except mysql.connector.Error as err:
        # Handle specific errors, like a duplicate membership number
        if err.errno == 1062: # Duplicate entry
            raise HTTPException(status_code=409, detail=f"A member with membership number '{member_data.membership_no}' already exists.")
        print(f"Database INSERT error: {err}")
        raise HTTPException(status_code=500, detail="Failed to create member in the database.")
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()

def cleanup_files(files_to_delete: List[Path]):
    """Safely deletes a list of files."""
    for file_path in files_to_delete:
        try:
            if file_path and file_path.exists():
                os.remove(file_path)
        except OSError as e:
            print(f"Error deleting file {file_path}: {e}")

# --- PDF Processing Functions ---

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
        if epic:
            doc.close()
            return epic
        ocr_text = ""
        for page in doc:
            pix = page.get_pixmap(dpi=300); img_data = pix.tobytes("png"); pil_image = Image.open(io.BytesIO(img_data)); ocr_text += pytesseract.image_to_string(pil_image, lang='eng')
        doc.close()
        return find_epic_in_text(ocr_text)
    except Exception as e:
        print(f"PDF processing error: {e}"); return None

# --- API Endpoint and Startup Event ---

@app.on_event("startup")
def on_startup():
    print("Testing database connection..."); conn = get_db_connection()
    if conn and conn.is_connected(): print("✅ Database connection successful."); conn.close()
    else: print("❌ FAILED to connect to the database.")
    print("Ensuring upload directories exist..."); os.makedirs(PDF_UPLOAD_DIR, exist_ok=True); os.makedirs(PHOTO_UPLOAD_DIR, exist_ok=True); print("✅ Upload directories are ready.")

@app.post("/create-member/")
async def create_member_endpoint(
    epic_number: Annotated[str, Form()], 
    pdf_file: Annotated[UploadFile, File()],
    photo_file: Annotated[UploadFile, File()],
    member_data: MemberCreate = Depends() # Injects form data into the Pydantic model
):
    unique_id = str(uuid.uuid4().hex)[:8]; safe_epic = epic_number.strip().upper()
    pdf_filename = f"{safe_epic}_{unique_id}_{Path(pdf_file.filename).name}"
    photo_filename = f"{safe_epic}_{unique_id}_{Path(photo_file.filename).name}"
    saved_pdf_path = PDF_UPLOAD_DIR / pdf_filename
    saved_photo_path = PHOTO_UPLOAD_DIR / photo_filename
    files_to_cleanup = [saved_pdf_path, saved_photo_path]

    try:
        with saved_pdf_path.open("wb") as buffer: shutil.copyfileobj(pdf_file.file, buffer)
        with saved_photo_path.open("wb") as buffer: shutil.copyfileobj(photo_file.file, buffer)
    finally:
        pdf_file.file.close(); photo_file.file.close()

    extracted_epic = extract_epic_from_pdf(saved_pdf_path)

    if not extracted_epic:
        cleanup_files(files_to_cleanup)
        raise HTTPException(status_code=422, detail="Could not extract an EPIC number from the provided PDF.")
    
    if safe_epic != extracted_epic:
        cleanup_files(files_to_cleanup)
        raise HTTPException(status_code=400, detail=f"Mismatch: Entered EPIC '{safe_epic}' does not match PDF EPIC '{extracted_epic}'.")

    # If verification is successful, create the member
    try:
        new_member_id = create_member_in_db(member_data, str(saved_pdf_path), str(saved_photo_path))
    except HTTPException as e:
        # If DB insertion fails (e.g., duplicate member), clean up the files and re-raise the exception
        cleanup_files(files_to_cleanup)
        raise e

    return {
        "message": "Member created successfully.",
        "member_id": new_member_id, # This is the primary key from the database
        "name": member_data.name,
        "membership_no": member_data.membership_no
    }
