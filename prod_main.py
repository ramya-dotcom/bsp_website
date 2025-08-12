import os
import io
import re
import uuid
import shutil
import enum
import platform
from pathlib import Path
from datetime import date, datetime, timedelta
from typing import Annotated, List, Optional

import fitz  # PyMuPDF
from PIL import Image
import pytesseract
from dotenv import load_dotenv
import mysql.connector
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends
from pydantic import BaseModel, Field

load_dotenv()

# Point pytesseract to the system binary if provided
TESSERACT_CMD = os.getenv("TESSERACT_CMD")
if TESSERACT_CMD:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

if platform.system() == "Darwin":
    BASE_UPLOAD_DIR = Path("./volunteers_files")
else:
    BASE_UPLOAD_DIR = Path(os.getenv("BASE_UPLOAD_DIR", "/home/mfnssihw/volunteers_files"))

TEMP_UPLOAD_DIR = Path(os.getenv("TEMP_UPLOAD_DIR", str(BASE_UPLOAD_DIR / "tmp")))
PDF_UPLOAD_DIR = Path(os.getenv("PDF_UPLOAD_DIR", str(BASE_UPLOAD_DIR / "voterid_proof")))
PHOTO_UPLOAD_DIR = Path(os.getenv("PHOTO_UPLOAD_DIR", str(BASE_UPLOAD_DIR / "photos")))

VERIFICATION_SESSIONS: dict[str, dict] = {}

app = FastAPI(
    title="Membership Workflow API",
    description="A multi-step API for document verification, member creation, and payment handling.",
    version="2.2.6",
)

class BloodGroup(str, enum.Enum):
    A_pos = "A+"
    A_neg = "A-"
    B_pos = "B+"
    B_neg = "B-"
    AB_pos = "AB+"
    AB_neg = "AB-"
    O_pos = "O+"
    O_neg = "O-"

class MemberCreate(BaseModel):
    name: str = Field("John Doe", description="Full Name")
    profession: Optional[str] = Field("Software Engineer", description="Profession")
    designation: Optional[str] = Field("Senior Developer", description="Designation")
    mandal: Optional[str] = Field("Coimbatore South", description="Mandal")
    dob: Optional[date] = Field("1990-01-15", description="Date of Birth (YYYY-MM-DD)")
    blood_group: Optional[BloodGroup] = Field(BloodGroup.O_pos, description="Select from dropdown")
    contact_no: Optional[str] = Field("9876543210", description="10-digit Contact Number", pattern=r"^\d{10}$")
    address: Optional[str] = Field("123, V.H. Road, Coimbatore - 641001", description="Address")

class PaymentUpdate(BaseModel):
    member_id: int
    status: str  # "successful" or "failed"

def get_db_connection():
    try:
        return mysql.connector.connect(
            host=os.getenv("DATABASE_HOST"),
            user=os.getenv("DATABASE_USERNAME"),
            password=os.getenv("DATABASE_PASSWORD"),
            database=os.getenv("DATABASE_NAME"),
        )
    except mysql.connector.Error as err:
        print(f"Database connection error: {err}", flush=True)
        return None

def cleanup_files(files_to_delete: List[Path]):
    for file_path in files_to_delete:
        try:
            if file_path and file_path.exists():
                os.remove(file_path)
        except OSError as e:
            print(f"Error deleting file {file_path}: {e}", flush=True)

EPIC_CORE = r"[A-Z]{3}[0-9]{7}"
EPIC_PATTERNS = [
    rf"(?i)(?:EPIC\s*No\.?|Identity\s*Card)\s*.*?\b({EPIC_CORE})\b",
    rf"\b({EPIC_CORE})\b",
]

def normalize_text(s: str) -> str:
    if not s:
        return ""
    s = re.sub(r"[\s\-\:_]+", "", s)
    s = s.replace("О", "O").replace("Ｏ", "O")
    s = s.replace("०", "0")
    s = s.replace("l", "I")
    return s

def find_epic_in_text_any(text: str) -> Optional[str]:
    if not text:
        return None
    for pat in EPIC_PATTERNS:
        m = re.search(pat, text, re.DOTALL)
        if m:
            return m.group(1).strip().replace(" ", "")
    norm = normalize_text(text)
    m2 = re.search(EPIC_CORE, norm)
    if m2:
        return m2.group(0)
    return None

def extract_text_multimode(doc: fitz.Document) -> str:
    parts = []
    for page in doc:
        try:
            parts.append(page.get_text("text"))
            words = page.get_text("words") or []
            words_sorted = sorted(words, key=lambda w: (w[1], w))
            parts.append(" ".join(w[1] for w in words_sorted if len(w) >= 5))
            blocks = page.get_text("blocks") or []
            for b in blocks:
                if len(b) >= 5 and isinstance(b[1], str):
                    parts.append(b[1])
        except Exception as e:
            print(f"Text extraction error on page {page.number}: {e}", flush=True)
    text = "\n".join(parts)
    print(f"DEBUG: Combined text length: {len(text)}", flush=True)
    return text

def ocr_pdf_with_tesseract(doc: fitz.Document) -> str:
    ocr_text = ""
    for page in doc:
        pix = page.get_pixmap(dpi=300)
        img_data = pix.tobytes("png")
        pil_image = Image.open(io.BytesIO(img_data))
        ocr_text += pytesseract.image_to_string(pil_image, lang="eng")
    return ocr_text

def extract_epic_from_pdf(pdf_path: Path) -> Optional[str]:
    try:
        doc = fitz.open(pdf_path)
        try:
            text = extract_text_multimode(doc)
            epic = find_epic_in_text_any(text)
            if epic:
                print(f"DEBUG: EPIC from text: {epic}", flush=True)
                return epic

            tess_path = shutil.which("tesseract") or TESSERACT_CMD
            if not tess_path:
                print("Tesseract not found on system; skipping OCR fallback.", flush=True)
                return None

            print(f"DEBUG: Using Tesseract at: {tess_path}", flush=True)
            ocr_text = ocr_pdf_with_tesseract(doc)
            epic_ocr = find_epic_in_text_any(ocr_text)
            if epic_ocr:
                print(f"DEBUG: EPIC from OCR: {epic_ocr}", flush=True)
            else:
                print("DEBUG: OCR completed but EPIC not found.", flush=True)
            return epic_ocr
        finally:
            doc.close()
    except Exception as e:
        print(f"PDF processing error: {e}", flush=True)
        return None

@app.on_event("startup")
def on_startup():
    print("Ensuring upload directories exist...", flush=True)
    for d in [TEMP_UPLOAD_DIR, PDF_UPLOAD_DIR, PHOTO_UPLOAD_DIR]:
        os.makedirs(d, exist_ok=True)
    print("Upload directories are ready.", flush=True)

@app.get("/healthz")
def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}

@app.post("/verify-document/")
async def verify_document_endpoint(
    epic_number: Annotated[str, Form()],
    pdf_file: Annotated[UploadFile, File()],
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
        if not extracted_epic:
            raise HTTPException(status_code=400, detail="Could not extract EPIC from PDF.")
        else:
            raise HTTPException(status_code=400, detail=f"Mismatch: Entered EPIC '{safe_epic}' does not match PDF EPIC '{extracted_epic}'.")

    token = str(uuid.uuid4())
    VERIFICATION_SESSIONS[token] = {
        "temp_pdf_path": temp_pdf_path,
        "epic": extracted_epic,
        "expiry": datetime.utcnow() + timedelta(minutes=15),
    }
    return {"message": "Verification successful. Use this token to submit member details.", "verification_token": token}

def generate_membership_no(new_member_id: int) -> str:
    now = datetime.utcnow()
    return f"BSP-{now.year}{now.month:02d}-{new_member_id:06d}"

@app.post("/submit-details/")
async def submit_details_endpoint(
    verification_token: Annotated[str, Form()],
    photo_file: Annotated[UploadFile, File()],
    member_data: MemberCreate = Depends(),
):
    session = VERIFICATION_SESSIONS.get(verification_token)
    if not session or session["expiry"] < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Invalid or expired verification token. Please verify again.")

    temp_pdf_path: Path = session["temp_pdf_path"]
    epic_number: str = session["epic"]
    unique_id = str(uuid.uuid4().hex)[:8]

    pdf_filename = f"{epic_number}_{unique_id}_{temp_pdf_path.name}"
    permanent_pdf_path = PDF_UPLOAD_DIR / pdf_filename
    shutil.move(str(temp_pdf_path), str(permanent_pdf_path))

    photo_filename = f"{epic_number}_{unique_id}_{Path(photo_file.filename).name}"
    permanent_photo_path = PHOTO_UPLOAD_DIR / photo_filename
    try:
        with permanent_photo_path.open("wb") as buffer:
            shutil.copyfileobj(photo_file.file, buffer)
    finally:
        photo_file.file.close()

    conn = get_db_connection()
    if not conn:
        cleanup_files([permanent_pdf_path, permanent_photo_path])
        raise HTTPException(status_code=503, detail="Database service is unavailable.")

    cursor = None
    try:
        cursor = conn.cursor()
        sql_insert = """
            INSERT INTO members
            (name, profession, designation, mandal, dob, blood_group, contact_no,
             address, pdf_proof_path, photo_path, status, active_no)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        values_insert = (
            member_data.name, member_data.profession, member_data.designation,
            member_data.mandal, member_data.dob,
            member_data.blood_group.value if member_data.blood_group else None,
            member_data.contact_no, member_data.address, str(permanent_pdf_path),
            str(permanent_photo_path), "pending_payment", None,
        )
        cursor.execute(sql_insert, values_insert)
        new_member_id = cursor.lastrowid
        conn.commit()

        generated_membership_no = generate_membership_no(new_member_id)
        cursor.execute("UPDATE members SET membership_no = %s WHERE id = %s", (generated_membership_no, new_member_id))
        conn.commit()
    except mysql.connector.Error as err:
        cleanup_files([permanent_pdf_path, permanent_photo_path])
        print(f"DB error: {err}", flush=True)
        raise HTTPException(status_code=500, detail="Failed to create member in the database.")
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

    if verification_token in VERIFICATION_SESSIONS:
        del VERIFICATION_SESSIONS[verification_token]

    return {"message": "Details submitted. Proceed to payment.", "member_id": new_member_id, "membership_no": generated_membership_no}

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
                files_to_delete: list[Path] = []
                if record.get("pdf_proof_path"):
                    files_to_delete.append(Path(record["pdf_proof_path"]))
                if record.get("photo_path"):
                    files_to_delete.append(Path(record["photo_path"]))
                cleanup_files(files_to_delete)
            cursor.execute("DELETE FROM members WHERE id = %s", (update_data.member_id,))
            conn.commit()
            return {"message": f"Payment failed. Member {update_data.member_id} and associated files have been deleted."}
        else:
            raise HTTPException(status_code=400, detail="Invalid status. Must be 'successful' or 'failed'.")
    except mysql.connector.Error as err:
        print(f"Database update/delete error: {err}", flush=True)
        raise HTTPException(status_code=500, detail="A database error occurred.")
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()