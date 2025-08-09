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
import platform
import enum


# --- Imports for .env and MySQL ---
from dotenv import load_dotenv
import mysql.connector


# --- FastAPI and Pydantic Imports ---
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Annotated, List, Optional


# --- Load Environment Variables ---
load_dotenv()


# --- Base upload folder definition ---
# The base directory for all uploads, configured via environment variable or a fixed default path.
BASE_UPLOAD_DIR = Path(os.getenv("BASE_UPLOAD_DIR", "/home/mfnssihw/volunteers_files"))


# Upload directories configured with env override or default under BASE_UPLOAD_DIR
TEMP_UPLOAD_DIR = Path(os.getenv("TEMP_UPLOAD_DIR", BASE_UPLOAD_DIR / "tmp"))
PDF_UPLOAD_DIR = Path(os.getenv("PDF_UPLOAD_DIR", BASE_UPLOAD_DIR / "voterid_proof"))
PHOTO_UPLOAD_DIR = Path(os.getenv("PHOTO_UPLOAD_DIR", BASE_UPLOAD_DIR / "photos"))


# --- In-Memory State Management (for demo) ---
VERIFICATION_SESSIONS = {}


# --- Initialize FastAPI App ---
app = FastAPI(
    title="Membership Workflow API",
    description="A multi-step API for document verification, member creation, and payment handling.",
    version="2.2.2" # Version bump for the new changes
)


# --- Blood Group Enum (Dropdown enforcement) ---
class BloodGroup(str, enum.Enum):
    A_pos = "A+"
    A_neg = "A-"
    B_pos = "B+"
    B_neg = "B-"
    AB_pos = "AB+"
    AB_neg = "AB-"
    O_pos = "O+"
    O_neg = "O-"


# --- Pydantic Models ---
class MemberCreate(BaseModel):
    # Sample defaults shown in Swagger UI
    name: str = Field("John Doe", description="Full Name")
    # active_no is now handled on the backend (not asked from user)
    profession: Optional[str] = Field("Software Engineer", description="Profession")
    designation: Optional[str] = Field("Senior Developer", description="Designation")
    mandal: Optional[str] = Field("Coimbatore South", description="Mandal")
    # Changed default to a clear example string; description clarifies format
    dob: Optional[date] = Field("1990-01-15", description="Date of Birth (YYYY-MM-DD)")
    blood_group: Optional[BloodGroup] = Field(BloodGroup.O_pos, description="Select from dropdown")
    contact_no: Optional[str] = Field("9876543210", description="10-digit Contact Number", pattern=r'^\d{10}$')
    address: Optional[str] = Field("123, V.H. Road, Coimbatore - 641001", description="Address")


class PaymentUpdate(BaseModel):
    member_id: int
    status: str  # "successful" or "failed"


# --- Database and File System Management ---
def get_db_connection():
    try:
        return mysql.connector.connect(
            host=os.getenv("DATABASE_HOST"),
            user=os.getenv("DATABASE_USERNAME"),
            password=os.getenv("DATABASE_PASSWORD"),
            database=os.getenv("DATABASE_NAME")
        )
    except mysql.connector.Error as err:
        print(f"Database connection error: {err}")
        return None


def cleanup_files(files_to_delete: List[Path]):
    for file_path in files_to_delete:
        try:
            if file_path and file_path.exists():
                os.remove(file_path)
        except OSError as e:
            print(f"Error deleting file {file_path}: {e}")


# --- PDF Processing Functions ---
def find_epic_in_text(text):
    if not text:
        return None
    patterns = [
        r'(?i)(?:EPIC No|Identity Card)\s*.*?\s*\b([A-Z]{3}[0-9]{7})\b',
        r'\b([A-Z]{3}[0-9]{7})\b'
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip().replace(" ", "")
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
            pix = page.get_pixmap(dpi=300)
            img_data = pix.tobytes("png")
            pil_image = Image.open(io.BytesIO(img_data))
            ocr_text += pytesseract.image_to_string(pil_image, lang='eng')
        doc.close()
        return find_epic_in_text(ocr_text)
    except Exception as e:
        print(f"PDF processing error: {e}")
        return None


# --- Startup Event ---
@app.on_event("startup")
def on_startup():
    print("Ensuring upload directories exist...")
    try:
        for dir_path in [TEMP_UPLOAD_DIR, PDF_UPLOAD_DIR, PHOTO_UPLOAD_DIR]:
            os.makedirs(dir_path, exist_ok=True)
    except Exception as e:
        print(f"Failed to create directory {dir_path}: {e}")
        raise
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


    token = str(uuid.uuid4())
    VERIFICATION_SESSIONS[token] = {
        "temp_pdf_path": temp_pdf_path,
        "epic": extracted_epic,
        "expiry": datetime.utcnow() + timedelta(minutes=15)
    }


    return {
        "message": "Verification successful. Use this token to submit member details.",
        "verification_token": token
    }


# --- Helper: generate membership number from id ---
def generate_membership_no(new_member_id: int) -> str:
    now = datetime.utcnow()
    return f"BSP-{now.year}{now.month:02d}-{new_member_id:06d}"


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


    unique_id = str(uuid.uuid4().hex)[:8]
    pdf_filename = f"{epic_number}_{unique_id}_{temp_pdf_path.name}"
    permanent_pdf_path = PDF_UPLOAD_DIR / pdf_filename
    
    # --- START DEBUG LOGGING ---
    print(f"DEBUG: Attempting to move temporary PDF from: {temp_pdf_path}")
    print(f"DEBUG: Destination PDF path: {permanent_pdf_path}")
    # --- END DEBUG LOGGING ---
    
    shutil.move(str(temp_pdf_path), str(permanent_pdf_path))
    
    # --- START DEBUG LOGGING ---
    print(f"DEBUG: PDF move complete. Checking if file exists at destination...")
    if permanent_pdf_path.exists():
        print("✅ DEBUG: PDF file successfully exists at permanent path.")
    else:
        print("❌ DEBUG: ERROR! PDF file does not exist at permanent path after move.")
    # --- END DEBUG LOGGING ---


    photo_filename = f"{epic_number}_{unique_id}_{Path(photo_file.filename).name}"
    permanent_photo_path = PHOTO_UPLOAD_DIR / photo_filename


    # --- START DEBUG LOGGING ---
    print(f"DEBUG: Attempting to save photo to: {permanent_photo_path}")
    # --- END DEBUG LOGGING ---


    try:
        with permanent_photo_path.open("wb") as buffer:
            shutil.copyfileobj(photo_file.file, buffer)
    finally:
        photo_file.file.close()
    
    # --- START DEBUG LOGGING ---
    print(f"DEBUG: Photo save complete. Checking if file exists...")
    if permanent_photo_path.exists():
        print("✅ DEBUG: Photo file successfully exists.")
    else:
        print("❌ DEBUG: ERROR! Photo file does not exist after saving.")
    # --- END DEBUG LOGGING ---


    conn = get_db_connection()
    if not conn:
        cleanup_files([permanent_pdf_path, permanent_photo_path])
        raise HTTPException(status_code=503, detail="Database service is unavailable.")


    cursor = None
    try:
        cursor = conn.cursor()
        sql_insert = """INSERT INTO members
            (name, profession, designation, mandal, dob, blood_group, contact_no,
             address, pdf_proof_path, photo_path, status, active_no)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        values_insert = (
            member_data.name, member_data.profession, member_data.designation,
            member_data.mandal, member_data.dob,
            member_data.blood_group.value if member_data.blood_group else None,
            member_data.contact_no, member_data.address, str(permanent_pdf_path),
            str(permanent_photo_path), 'pending_payment', None
        )
        cursor.execute(sql_insert, values_insert)
        new_member_id = cursor.lastrowid
        conn.commit()


        generated_membership_no = generate_membership_no(new_member_id)
        sql_update = "UPDATE members SET membership_no = %s WHERE id = %s"
        cursor.execute(sql_update, (generated_membership_no, new_member_id))
        conn.commit()


    except mysql.connector.Error as err:
        cleanup_files([permanent_pdf_path, permanent_photo_path])
        print(f"DB error: {err}")
        raise HTTPException(status_code=500, detail="Failed to create member in the database.")
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()
        if verification_token in VERIFICATION_SESSIONS:
            del VERIFICATION_SESSIONS[verification_token]


    return {
        "message": "Details submitted. Proceed to payment.",
        "member_id": new_member_id,
        "membership_no": generated_membership_no
    }
    
    
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
            cursor.execute("SELECT pdf_proof_path, photo_path FROM members WHERE id = %s", (update_data.member_id,))
            record = cursor.fetchone()
            if record:
                files_to_delete = []
                if record.get('pdf_proof_path'):
                    files_to_delete.append(Path(record['pdf_proof_path']))
                if record.get('photo_path'):
                    files_to_delete.append(Path(record['photo_path']))
                cleanup_files(files_to_delete)
            
            cursor.execute("DELETE FROM members WHERE id = %s", (update_data.member_id,))
            conn.commit()
            return {"message": f"Payment failed. Member {update_data.member_id} and associated files have been deleted."}
        else:
            raise HTTPException(status_code=400, detail="Invalid status. Must be 'successful' or 'failed'.")
    except mysql.connector.Error as err:
        print(f"Database update/delete error: {err}")
        raise HTTPException(status_code=500, detail="A database error occurred.")
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
