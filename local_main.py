import fitz  # PyMuPDF
import re
from pathlib import Path
import io
from PIL import Image, ImageDraw, ImageFont
import pytesseract
import shutil
import os
import uuid
from datetime import date, datetime, timedelta
import platform
import enum

# --- Env (dotenv) ---
from dotenv import load_dotenv
# --- MySQL (kept but commented below where used) ---
# import mysql.connector

# --- FastAPI and Pydantic ---
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Annotated, List, Optional, Union, Sequence

# --- SQLite (active data source for card rendering) ---
import sqlite3

# ================================================================
# Load environment
# ================================================================
load_dotenv()

# ================================================================
# Paths and directories
# ================================================================
if platform.system() == "Darwin":  # macOS local dev
    BASE_UPLOAD_DIR = Path("./volunteers_files")
else:
    BASE_UPLOAD_DIR = Path(os.getenv("BASE_UPLOAD_DIR", "/home/mfnssihw/volunteers_files"))

TEMP_UPLOAD_DIR = Path(os.getenv("TEMP_UPLOAD_DIR", BASE_UPLOAD_DIR / "tmp"))
PDF_UPLOAD_DIR = Path(os.getenv("PDF_UPLOAD_DIR", BASE_UPLOAD_DIR / "voterid_proof"))
PHOTO_UPLOAD_DIR = Path(os.getenv("PHOTO_UPLOAD_DIR", BASE_UPLOAD_DIR / "photos"))
CARDS_DIR = Path(os.getenv("CARDS_DIR", BASE_UPLOAD_DIR / "cards"))
STATIC_DIR = Path("./static").resolve()

# ================================================================
# In-memory state
# ================================================================
VERIFICATION_SESSIONS = {}

# ================================================================
# FastAPI app
# ================================================================
app = FastAPI(
    title="Membership Workflow API",
    description="A multi-step API for document verification, member creation, payment handling, and card rendering.",
    version="2.7.0"
)

# ================================================================
# Enums and models
# ================================================================
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
    contact_no: Optional[str] = Field("9876543210", description="10-digit Contact Number", pattern=r'^\d{10}$')
    address: Optional[str] = Field("123, V.H. Road, Coimbatore - 641001", description="Address")

class PaymentUpdate(BaseModel):
    member_id: int
    status: str  # "successful" or "failed"

# ================================================================
# Database connections
# ================================================================
# NOTE: MySQL connection is kept but commented. Re-enable if needed.
# def get_db_connection():
#     try:
#         return mysql.connector.connect(
#             host=os.getenv("DATABASE_HOST"),
#             user=os.getenv("DATABASE_USERNAME"),
#             password=os.getenv("DATABASE_PASSWORD"),
#             database=os.getenv("DATABASE_NAME")
#         )
#     except mysql.connector.Error as err:
#         print(f"Database connection error: {err}")
#         return None

SQLITE_DB_PATH = Path(os.getenv("SQLITE_DB_PATH", "./members_local.sqlite")).resolve()

def sqlite_conn():
    conn = sqlite3.connect(str(SQLITE_DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def sqlite_init_schema():
    with sqlite_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255) NOT NULL,
            membership_no VARCHAR(100),
            active_no VARCHAR(100),
            profession VARCHAR(255),
            designation VARCHAR(255),
            mandal VARCHAR(255),
            dob DATE,
            blood_group VARCHAR(10),
            contact_no VARCHAR(20) NOT NULL,
            address TEXT,
            pdf_proof_path VARCHAR(512),
            photo_path VARCHAR(512),
            status VARCHAR(50) DEFAULT 'pending_payment',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        conn.commit()

# ================================================================
# Utils
# ================================================================
def cleanup_files(files_to_delete: List[Path]):
    for file_path in files_to_delete:
        try:
            if file_path and file_path.exists():
                os.remove(file_path)
        except OSError as e:
            print(f"Error deleting file {file_path}: {e}")

def row_get(row: sqlite3.Row, key: str):
    try:
        return row[key]
    except Exception:
        return None

# Safe scaler for positions: accepts number or tuple/list of numbers
def scale_pos(pos: Union[int, float, Sequence[Union[int, float, str]], str], scale: float):
    def to_num(x):
        if isinstance(x, (int, float)):
            return x
        if isinstance(x, str):
            try:
                return float(x)
            except ValueError:
                raise TypeError(f"Non-numeric string in position: {x!r}")
        raise TypeError(f"Unsupported type in position: {type(x).__name__}")
    if isinstance(pos, (int, float, str)):
        return int(round(to_num(pos) * scale))
    if isinstance(pos, (list, tuple)):
        return tuple(int(round(to_num(v) * scale)) for v in pos)
    raise TypeError(f"Unsupported position type: {type(pos).__name__}")

# ================================================================
# PDF text extraction to verify EPIC
# ================================================================
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

# ================================================================
# Startup
# ================================================================
@app.on_event("startup")
def on_startup():
    print("Ensuring directories exist...")
    for d in [TEMP_UPLOAD_DIR, PDF_UPLOAD_DIR, PHOTO_UPLOAD_DIR, CARDS_DIR, STATIC_DIR]:
        os.makedirs(d, exist_ok=True)
    sqlite_init_schema()
    print("✅ Startup ready")

# ================================================================
# Original endpoints (MySQL operations remain commented out)
# ================================================================
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

def generate_membership_no(new_member_id: int) -> str:
    now = datetime.utcnow()
    return f"BSP-{now.year}{now.month:02d}-{new_member_id:06d}"

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
    shutil.move(str(temp_pdf_path), str(permanent_pdf_path))

    photo_filename = f"{epic_number}_{unique_id}_{Path(photo_file.filename).name}"
    permanent_photo_path = PHOTO_UPLOAD_DIR / photo_filename
    try:
        with permanent_photo_path.open("wb") as buffer:
            shutil.copyfileobj(photo_file.file, buffer)
    finally:
        photo_file.file.close()

    # NOTE: MySQL insert/update commented out; keep files in place for local testing.
    # conn = get_db_connection()
    # if not conn:
    #     cleanup_files([permanent_pdf_path, permanent_photo_path])
    #     raise HTTPException(status_code=503, detail="Database service is unavailable.")
    #
    # cursor = None
    # try:
    #     cursor = conn.cursor()
    #     sql_insert = """INSERT INTO members
    #     (name, profession, designation, mandal, dob, blood_group, contact_no,
    #     address, pdf_proof_path, photo_path, status, active_no)
    #     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
    #     values_insert = (
    #         member_data.name, member_data.profession, member_data.designation,
    #         member_data.mandal, member_data.dob,
    #         member_data.blood_group.value if member_data.blood_group else None,
    #         member_data.contact_no, member_data.address, str(permanent_pdf_path),
    #         str(permanent_photo_path), 'pending_payment', None
    #     )
    #     cursor.execute(sql_insert, values_insert)
    #     new_member_id = cursor.lastrowid
    #     conn.commit()
    #
    #     generated_membership_no = generate_membership_no(new_member_id)
    #     sql_update = "UPDATE members SET membership_no = %s WHERE id = %s"
    #     cursor.execute(sql_update, (generated_membership_no, new_member_id))
    #     conn.commit()
    # except Exception as err:
    #     cleanup_files([permanent_pdf_path, permanent_photo_path])
    #     print(f"DB error: {err}")
    #     raise HTTPException(status_code=500, detail="Failed to create member in the database.")
    # finally:
    #     if cursor: cursor.close()
    #     if conn: conn.close()

    # For local usage without MySQL, just mimic a response
    generated_membership_no = generate_membership_no(1)
    new_member_id = 1
    if verification_token in VERIFICATION_SESSIONS:
        del VERIFICATION_SESSIONS[verification_token]

    return {
        "message": "Details submitted. Proceed to payment.",
        "member_id": new_member_id,
        "membership_no": generated_membership_no
    }

@app.post("/update-payment/")
async def update_payment_endpoint(update_data: PaymentUpdate):
    # NOTE: This would normally hit MySQL. Keeping logic stubbed.
    # conn = get_db_connection()
    # if not conn:
    #     raise HTTPException(status_code=503, detail="Database service is unavailable.")
    #
    # cursor = None
    # try:
    #     cursor = conn.cursor(dictionary=True)
    #     if update_data.status.lower() == "successful":
    #         cursor.execute("UPDATE members SET status = 'active' WHERE id = %s", (update_data.member_id,))
    #         conn.commit()
    #         return {"message": f"Payment successful. Member {update_data.member_id} is now active."}
    #     elif update_data.status.lower() == "failed":
    #         cursor.execute("SELECT pdf_proof_path, photo_path FROM members WHERE id = %s", (update_data.member_id,))
    #         record = cursor.fetchone()
    #         if record:
    #             files_to_delete = []
    #             if record.get('pdf_proof_path'):
    #                 files_to_delete.append(Path(record['pdf_proof_path']))
    #             if record.get('photo_path'):
    #                 files_to_delete.append(Path(record['photo_path']))
    #             cleanup_files(files_to_delete)
    #             cursor.execute("DELETE FROM members WHERE id = %s", (update_data.member_id,))
    #             conn.commit()
    #             return {"message": f"Payment failed. Member {update_data.member_id} and associated files have been deleted."}
    #         else:
    #             raise HTTPException(status_code=400, detail="Invalid status. Must be 'successful' or 'failed'.")
    #     else:
    #         raise HTTPException(status_code=400, detail="Invalid status. Must be 'successful' or 'failed'.")
    # except Exception as err:
    #     print(f"Database update/delete error: {err}")
    #     raise HTTPException(status_code=500, detail="A database error occurred.")
    # finally:
    #     if cursor: cursor.close()
    #     if conn: conn.close()
    return {"message": f"Payment {update_data.status}. (Stub response with MySQL disabled)"}

# ================================================================
# Pillow-based membership card generator (template PNG)
# ================================================================
# Coordinates assume a base width of 1289 px; scaled by actual template width.
PIL_POSITIONS = {
    "left_value_x": 450,       # X where the value text begins for most rows
    "id_no":      (130, 275),
    "membership": (530, 275),
    "active_no":  (970, 275),
    "name":       (0, 357),    # Y only; X from left_value_x
    "profession": (0, 398),
    "designation":(0, 439),
    "mandal":     (0, 480),
    "dob":        (0, 521),
    "blood":      (0, 562),
    "contact":    (0, 603),
    "address":    (0, 644),
    # Photo box (x, y, w, h)
    "photo_box":  (923, 357, 200, 240)
}

def _load_font(size_px: int, bold: bool = False):
    try:
        if bold:
            return ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", size_px)
        return ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans.ttf", size_px)
    except Exception:
        return ImageFont.load_default()

def _wrap_text(text: str, max_chars: int):
    if not text:
        return [""]
    words = text.split()
    lines = []
    current = []
    for w in words:
        candidate = " ".join(current + [w])
        if len(candidate) <= max_chars:
            current.append(w)
        else:
            if current:
                lines.append(" ".join(current))
            current = [w]
    if current:
        lines.append(" ".join(current))
    return lines

def fetch_member_data(member_id: Optional[int] = None, membership_no: Optional[str] = None) -> dict:
    # With MySQL disabled, use SQLite directly
    with sqlite_conn() as scon:
        scur = scon.cursor()
        if member_id:
            scur.execute("SELECT * FROM members WHERE id = ?", (member_id,))
        else:
            scur.execute("SELECT * FROM members WHERE membership_no = ?", (membership_no,))
        srow = scur.fetchone()
        if not srow:
            raise HTTPException(status_code=404, detail="Member not found in database")
        return {k: srow[k] for k in srow.keys()}

def render_pillow_card(member: dict) -> Path:
    """
    Renders a membership card PNG based on static/card_template.png and member data.
    Saves to CARDS_DIR and returns the file path.
    """
    template_path = STATIC_DIR / "card_template.png"
    if not template_path.exists():
        raise HTTPException(status_code=500, detail="Template not found at static/card_template.png")

    # Load template
    card = Image.open(template_path)
    if card.mode != "RGB":
        card = card.convert("RGB")
    draw = ImageDraw.Draw(card)

    # Dimensions and scaling
    base_w = 1289.0  # Reference width used to define coordinates above
    W, H = card.size
    scale = W / base_w

    # Fonts
    text_font = _load_font(int(22 * scale))
    bold_font = _load_font(int(22 * scale), bold=True)
    small_font = _load_font(int(18 * scale))

    # Colors
    BLACK = "#000000"
    GRAY = "#333333"
    SILVER = "#CCCCCC"
    OUTLINE = "#666666"

    # Numbers at top
    id_val = member.get("id")
    id_number = f"TN{id_val:06d}" if isinstance(id_val, int) else f"TN{datetime.utcnow().strftime('%y')}{str(uuid.uuid4())[:6].upper()}"
    membership_number = member.get("membership_no") or ""
    active_number = member.get("active_no") or f"ACT{datetime.utcnow().strftime('%m%y')}{str(uuid.uuid4())[:4].upper()}"

    # Scaled positions
    id_x, id_y = scale_pos(PIL_POSITIONS["id_no"], scale)
    mem_x, mem_y = scale_pos(PIL_POSITIONS["membership"], scale)
    act_x, act_y = scale_pos(PIL_POSITIONS["active_no"], scale)
    vx = scale_pos(PIL_POSITIONS["left_value_x"], scale)

    def y_scaled(key: str) -> int:
        _, y = PIL_POSITIONS[key]
        return scale_pos(y, scale)

    draw.text((id_x,  id_y),  str(id_number),         font=small_font, fill=BLACK, anchor="lt")
    draw.text((mem_x, mem_y), str(membership_number), font=small_font, fill=BLACK, anchor="mt")
    draw.text((act_x, act_y), str(active_number),     font=small_font, fill=BLACK, anchor="rt")

    # Left column values
    draw.text((vx, y_scaled("name")), (member.get("name") or "").upper(), font=bold_font, fill=BLACK, anchor="lt")
    draw.text((vx, y_scaled("profession")), member.get("profession") or "", font=text_font, fill=BLACK, anchor="lt")
    draw.text((vx, y_scaled("designation")), member.get("designation") or "", font=text_font, fill=BLACK, anchor="lt")
    draw.text((vx, y_scaled("mandal")), member.get("mandal") or "", font=text_font, fill=BLACK, anchor="lt")
    dob_val = member.get("dob")
    dob_str = str(dob_val) if dob_val is not None else ""
    draw.text((vx, y_scaled("dob")), dob_str, font=text_font, fill=BLACK, anchor="lt")
    draw.text((vx, y_scaled("blood")), member.get("blood_group") or "", font=text_font, fill=BLACK, anchor="lt")
    draw.text((vx, y_scaled("contact")), member.get("contact_no") or "", font=text_font, fill=BLACK, anchor="lt")

    # Address wrapping
    addr = member.get("address") or ""
    max_chars = 35
    lines = _wrap_text(addr, max_chars)
    addr_y = y_scaled("address")
    line_gap = scale_pos(25, scale)  # vertical gap between address lines
    for i, line in enumerate(lines[:2]):  # up to 2 lines
        draw.text((vx, addr_y + i * line_gap), line, font=text_font, fill=BLACK, anchor="lt")

    # Photo box
    px, py, pw, ph = scale_pos(PIL_POSITIONS["photo_box"], scale)
    photo_path = member.get("photo_path")
    if photo_path and Path(photo_path).exists():
        try:
            img = Image.open(photo_path).convert("RGB")
            img = img.resize((pw, ph), Image.Resampling.LANCZOS)
            card.paste(img, (px, py))
        except Exception:
            draw.rectangle([px, py, px + pw, py + ph], fill=SILVER, outline=OUTLINE, width=2)
            draw.text((px + pw // 2, py + ph // 2), "PHOTO\nERROR", font=text_font, fill=GRAY, anchor="mm")
    else:
        draw.rectangle([px, py, px + pw, py + ph], fill=SILVER, outline=OUTLINE, width=2)
        draw.text((px + pw // 2, py + ph // 2), "PHOTO\nNOT FOUND", font=text_font, fill=GRAY, anchor="mm")

    # Save
    file_stub = membership_number or f"id-{member.get('id') or 'unknown'}"
    file_stub = str(file_stub).replace("/", "-")
    out_path = CARDS_DIR / f"bsp_membership_card_{file_stub}.png"
    card.save(out_path, "PNG", quality=95, optimize=True)
    return out_path

# ================================================================
# FastAPI endpoints to generate and download Pillow card
# ================================================================
@app.post("/generate-card-pillow/")
async def generate_card_pillow(
    member_id: Annotated[Optional[int], Form()] = None,
    membership_no: Annotated[Optional[str], Form()] = None
):
    """
    Generate a membership card PNG using Pillow and the static/card_template.png template.
    Data is pulled from SQLite (MySQL disabled).
    """
    if not member_id and not membership_no:
        raise HTTPException(status_code=400, detail="Provide member_id or membership_no")

    member = fetch_member_data(member_id=member_id, membership_no=membership_no)
    out_path = render_pillow_card(member)
    return {
        "message": "Card generated (Pillow)",
        "member_id": member.get("id"),
        "membership_no": member.get("membership_no"),
        "card_path": str(out_path)
    }

@app.get("/download-card-pillow")
async def download_card_pillow(card_path: Annotated[str, Query(description="Absolute path returned by /generate-card-pillow/")]):
    """
    Download previously generated card PNG.
    """
    p = Path(card_path)
    if not p.exists() or not p.is_file():
        raise HTTPException(status_code=404, detail="Card file not found")
    filename = f"membership_card_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.png"
    return FileResponse(path=str(p), filename=filename, media_type="image/png")

# ================================================================
# Helper to seed SQLite for local tests
# ================================================================
@app.post("/seed-sqlite-member/")
async def seed_sqlite_member(
    name: Annotated[str, Form()],
    contact_no: Annotated[str, Form()] = "0000000000",
    membership_no: Annotated[Optional[str], Form()] = None,
    active_no: Annotated[Optional[str], Form()] = None,
    profession: Annotated[Optional[str], Form()] = None,
    designation: Annotated[Optional[str], Form()] = None,
    mandal: Annotated[Optional[str], Form()] = None,
    dob: Annotated[Optional[str], Form()] = None,
    blood_group: Annotated[Optional[str], Form()] = None,
    address: Annotated[Optional[str], Form()] = None,
    photo_path: Annotated[Optional[str], Form()] = None,
    pdf_proof_path: Annotated[Optional[str], Form()] = None,
    status: Annotated[str, Form()] = "active"
):
    with sqlite_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO members
            (name, membership_no, active_no, profession, designation, mandal, dob, blood_group,
             contact_no, address, pdf_proof_path, photo_path, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name, membership_no, active_no, profession, designation, mandal, dob, blood_group,
            contact_no, address, pdf_proof_path, photo_path, status
        ))
        conn.commit()
        new_id = cur.lastrowid
    return {"message": "Seeded", "id": new_id}
