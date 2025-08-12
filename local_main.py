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

# Production compatibility (unchanged for existing endpoints)
from dotenv import load_dotenv
import mysql.connector

# FastAPI
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Annotated, List, Optional

# New: templates, PDF, QR, SQLite, ReportLab
import sqlite3
import qrcode
import base64
from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A6
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, black
from reportlab.lib.utils import ImageReader  # <-- needed to draw from memory buffers

# ---------------------------------------------------------------
# Load env
# ---------------------------------------------------------------
load_dotenv()

# ---------------------------------------------------------------
# Paths
# ---------------------------------------------------------------
if platform.system() == "Darwin":
    BASE_UPLOAD_DIR = Path("./volunteers_files")
else:
    BASE_UPLOAD_DIR = Path(os.getenv("BASE_UPLOAD_DIR", "/home/mfnssihw/volunteers_files"))

TEMP_UPLOAD_DIR = Path(os.getenv("TEMP_UPLOAD_DIR", BASE_UPLOAD_DIR / "tmp"))
PDF_UPLOAD_DIR = Path(os.getenv("PDF_UPLOAD_DIR", BASE_UPLOAD_DIR / "voterid_proof"))
PHOTO_UPLOAD_DIR = Path(os.getenv("PHOTO_UPLOAD_DIR", BASE_UPLOAD_DIR / "photos"))
CARDS_DIR = Path(os.getenv("CARDS_DIR", BASE_UPLOAD_DIR / "cards"))
TEMPLATES_DIR = Path("./templates").resolve()

# ---------------------------------------------------------------
# In-memory state
# ---------------------------------------------------------------
VERIFICATION_SESSIONS = {}

# ---------------------------------------------------------------
# FastAPI
# ---------------------------------------------------------------
app = FastAPI(
    title="Membership Workflow API",
    description="A multi-step API for document verification, member creation, and payment handling.",
    version="2.5.1"
)

# ---------------------------------------------------------------
# Enums/Models (unchanged)
# ---------------------------------------------------------------
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
    status: str

# ---------------------------------------------------------------
# Production MySQL (unchanged)
# ---------------------------------------------------------------
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

# ---------------------------------------------------------------
# Local SQLite (active for new endpoints)
# ---------------------------------------------------------------
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

# ---------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------
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

def encode_image_to_data_url(path: Optional[Path]) -> Optional[str]:
    if not path or not path.exists():
        return None
    mime = "image/jpeg" if path.suffix.lower() in [".jpg", ".jpeg"] else "image/png"
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return f"data:{mime};base64,{b64}"

def generate_qr_image_bytes(payload: str) -> bytes:
    img = qrcode.make(payload)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def generate_qr_data_url(payload: str) -> str:
    b = generate_qr_image_bytes(payload)
    return "data:image/png;base64," + base64.b64encode(b).decode("ascii")

# ---------------------------------------------------------------
# EPIC extraction (unchanged)
# ---------------------------------------------------------------
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

# ---------------------------------------------------------------
# Startup
# ---------------------------------------------------------------
@app.on_event("startup")
def on_startup():
    for d in [TEMP_UPLOAD_DIR, PDF_UPLOAD_DIR, PHOTO_UPLOAD_DIR, CARDS_DIR, TEMPLATES_DIR]:
        os.makedirs(d, exist_ok=True)
    sqlite_init_schema()
    html_path = TEMPLATES_DIR / "bsp_card_exact_v2.html"
    if not html_path.exists():
        html_path.write_text(_CARD_HTML_TEMPLATE_V2(), encoding="utf-8")
    print("✅ Ready")

# ---------------------------------------------------------------
# Original endpoints (UNCHANGED)
# ---------------------------------------------------------------
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

    return {"message": "Verification successful. Use this token to submit member details.", "verification_token": token}

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
        else:
            raise HTTPException(status_code=400, detail="Invalid status. Must be 'successful' or 'failed'.")
    except mysql.connector.Error as err:
        print(f"Database update/delete error: {err}")
        raise HTTPException(status_code=500, detail="A database error occurred.")
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()

# ---------------------------------------------------------------
# Templating
# ---------------------------------------------------------------
env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html"])
)

# ---------------------------------------------------------------
# Data fetch + QR builder
# ---------------------------------------------------------------
def _fetch_member_by_id_or_no(member_id: Optional[int], membership_no: Optional[str]) -> sqlite3.Row:
    with sqlite_conn() as conn:
        cur = conn.cursor()
        if member_id:
            cur.execute("SELECT * FROM members WHERE id = ?", (member_id,))
        else:
            cur.execute("SELECT * FROM members WHERE membership_no = ?", (membership_no,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Member not found in SQLite")
        return row

def _qr_payload_for(row: sqlite3.Row) -> str:
    return f"https://bsp.local/verify-membership?id={row['id']}&membership_no={(row_get(row,'membership_no') or '')}"

# ---------------------------------------------------------------
# Option A: WeasyPrint endpoint (revised HTML/CSS)
# ---------------------------------------------------------------
@app.post("/generate-card-weasy/")
async def generate_card_weasy(member_id: Annotated[Optional[int], Form()] = None,
                              membership_no: Annotated[Optional[str], Form()] = None):
    if not member_id and not membership_no:
        raise HTTPException(status_code=400, detail="Provide member_id or membership_no")
    row = _fetch_member_by_id_or_no(member_id, membership_no)

    tpl = env.get_template("bsp_card_exact_v2.html")
    photo_path = Path(row_get(row, "photo_path")) if row_get(row, "photo_path") else None
    ctx = {
        "membership_no": row_get(row, "membership_no") or "",
        "active_no": row_get(row, "active_no") or "",
        "name": row_get(row, "name") or "",
        "profession": row_get(row, "profession") or "",
        "designation": row_get(row, "designation") or "",
        "mandal": row_get(row, "mandal") or "",
        "dob": row_get(row, "dob") or "",
        "blood_group": row_get(row, "blood_group") or "",
        "contact_no": row_get(row, "contact_no") or "",
        "address": row_get(row, "address") or "",
        "qr_data_url": generate_qr_data_url(_qr_payload_for(row)),
        "photo_data_url": encode_image_to_data_url(photo_path),
        "generated_on": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    }

    file_stub = (row_get(row, "membership_no") or f"id-{row['id']}").replace("/", "-")
    out_pdf = CARDS_DIR / f"{file_stub}_weasy.pdf"
    HTML(string=tpl.render(**ctx), base_url=str(TEMPLATES_DIR)).write_pdf(str(out_pdf))
    return {"message": "Card generated (WeasyPrint)", "card_path": str(out_pdf)}

# ---------------------------------------------------------------
# Option B: ReportLab endpoint (absolute drawing)
# ---------------------------------------------------------------
def _draw_dotted_line(c: canvas.Canvas, x1, y, x2, dot=1.2, gap=1.8):
    x = x1
    while x < x2:
        c.line(x, y, min(x + dot, x2), y)
        x += dot + gap

def _draw_text(c: canvas.Canvas, txt, x, y, size=9, color=black, bold=False):
    c.setFillColor(color)
    c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
    c.drawString(x, y, txt or "")

@app.post("/generate-card-reportlab/")
async def generate_card_reportlab(member_id: Annotated[Optional[int], Form()] = None,
                                  membership_no: Annotated[Optional[str], Form()] = None):
    if not member_id and not membership_no:
        raise HTTPException(status_code=400, detail="Provide member_id or membership_no")
    row = _fetch_member_by_id_or_no(member_id, membership_no)

    file_stub = (row_get(row, "membership_no") or f"id-{row['id']}").replace("/", "-")
    out_pdf = CARDS_DIR / f"{file_stub}_reportlab.pdf"

    # Page: A6 portrait
    c = canvas.Canvas(str(out_pdf), pagesize=A6)
    width, height = A6  # points
    blue = HexColor("#1e3a8a")

    # Border
    margin = 8 * mm
    c.setLineWidth(2)
    c.setStrokeColor(blue)
    c.rect(margin, margin, width - 2*margin, height - 2*margin)

    # Header
    y = height - 15*mm
    _draw_text(c, "EDUCATE AGITATE ORGANISE", 22*mm, y, size=9, color=blue, bold=True)
    y -= 5*mm
    _draw_text(c, "JAI BHIM JAI BHARAT", 30*mm, y, size=9, color=blue, bold=True)
    y -= 6*mm
    _draw_text(c, "BAHUJAN SAMAJ PARTY (BSP)", 18*mm, y, size=12, color=blue, bold=True)
    y -= 5*mm
    _draw_text(c, "TAMILNADU UNIT", 40*mm, y, size=10, color=blue, bold=True)

    # Left column start
    left_x = margin + 6*mm
    right_col_x = width - margin - 40*mm  # photo/qr column left edge
    y = height - 45*mm

    label_w = 30*mm
    line_w = 35*mm
    row_h = 6.2*mm

    def row_line(label, value):
        nonlocal y
        _draw_text(c, label, left_x, y, size=9, bold=True)
        _draw_dotted_line(c, left_x + label_w, y+1.5, left_x + label_w + line_w)
        _draw_text(c, value, left_x + label_w + line_w + 2*mm, y, size=10)
        y -= row_h

    row_line("MEMBERSHIP NO:", row_get(row, "membership_no") or "")
    row_line("ACTIVE NO:", row_get(row, "active_no") or "")
    row_line("Name :", row_get(row, "name") or "")
    row_line("Profession :", row_get(row, "profession") or "")
    row_line("Designation :", row_get(row, "designation") or "")
    row_line("Mandal :", row_get(row, "mandal") or "")
    row_line("D.O.B :", row_get(row, "dob") or "")
    row_line("Blood Group :", row_get(row, "blood_group") or "")
    row_line("Contact No :", row_get(row, "contact_no") or "")
    address = (row_get(row, "address") or "")
    row_line("Address :", address[:60])
    if len(address) > 60:
        _draw_text(c, "", left_x, y, size=9, bold=True)
        _draw_text(c, address[60:120], left_x + label_w + line_w + 2*mm, y, size=10)
        y -= row_h

    # Photo box
    c.setStrokeColor(black)
    photo_w, photo_h = 32*mm, 38*mm
    photo_x = right_col_x
    photo_y = height - 58*mm
    c.rect(photo_x, photo_y, photo_w, photo_h)

    photo_path = row_get(row, "photo_path")
    if photo_path and Path(photo_path).exists():
        try:
            c.drawImage(str(photo_path), photo_x+1, photo_y+1, photo_w-2, photo_h-2,
                        preserveAspectRatio=True, anchor='c')
        except Exception:
            pass

    # QR box
    qr_w = 28*mm
    qr_x = right_col_x + 2*mm
    qr_y = photo_y - qr_w - 4*mm
    c.rect(qr_x-1, qr_y-1, qr_w+2, qr_w+2)
    qr_png = generate_qr_image_bytes(_qr_payload_for(row))
    # FIX: wrap the BytesIO with ImageReader for ReportLab
    qr_img_reader = ImageReader(io.BytesIO(qr_png))
    c.drawImage(qr_img_reader, qr_x, qr_y, qr_w, qr_w, preserveAspectRatio=True, anchor='c')

    # Signature block
    sig_y = margin + 20*mm
    sig_x = width - margin - 45*mm
    c.line(sig_x, sig_y, sig_x + 40*mm, sig_y)
    _draw_text(c, "Holder Sign :", sig_x + 5*mm, sig_y + 3*mm, size=9)
    _draw_text(c, "(P. ANANDAN)", sig_x + 12*mm, sig_y - 6*mm, size=9, bold=True)
    _draw_text(c, "President", sig_x + 17*mm, sig_y - 12*mm, size=8)

    # Footer
    c.setFillColor(black)
    footer_text = ("Dadasaheb Kanshiram Bhavan, 2/14 - A Veteran Lines, Pallavaram Cantonment, "
                   "St. Stephen's School Near, Chennai, Tamil Nadu 600043")
    c.setFont("Helvetica", 8)
    c.drawCentredString(width/2, margin + 8*mm, "https://tnbsp.org/")
    c.setFont("Helvetica", 8)
    textobj = c.beginText(margin + 4*mm, margin + 5*mm)
    textobj.setLeading(10)
    max_chars = 80
    lines = [footer_text[i:i+max_chars] for i in range(0, len(footer_text), max_chars)]
    for ln in lines:
        textobj.textLine(ln)
    c.drawText(textobj)

    c.showPage()
    c.save()

    return {"message": "Card generated (ReportLab)", "card_path": str(out_pdf)}

# ---------------------------------------------------------------
# Verify endpoint (QR target)
# ---------------------------------------------------------------
@app.get("/verify-membership/")
async def verify_membership(id: Optional[int] = None, membership_no: Optional[str] = None):
    if not id and not membership_no:
        raise HTTPException(status_code=400, detail="Provide id or membership_no")
    with sqlite_conn() as conn:
        cur = conn.cursor()
        if id:
            cur.execute("SELECT id, name, membership_no, status, created_at FROM members WHERE id = ?", (id,))
        else:
            cur.execute("SELECT id, name, membership_no, status, created_at FROM members WHERE membership_no = ?", (membership_no,))
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Member not found")
    return {"id": row["id"], "name": row["name"], "membership_no": row_get(row,"membership_no"),
            "status": row_get(row,"status"), "created_at": row_get(row,"created_at")}

# ---------------------------------------------------------------
# Local seeding helper
# ---------------------------------------------------------------
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
        """, (name, membership_no, active_no, profession, designation, mandal, dob, blood_group,
              contact_no, address, pdf_proof_path, photo_path, status))
        conn.commit()
        new_id = cur.lastrowid
    return {"message": "Seeded", "id": new_id}

# ---------------------------------------------------------------
# HTML template content (revised CSS)
# ---------------------------------------------------------------
def _CARD_HTML_TEMPLATE_V2() -> str:
    return """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>BSP Membership Card</title>
<style>
  @page { size: A6; margin: 6mm; }
  * { box-sizing: border-box; }
  body { font-family: Arial, Helvetica, sans-serif; color: #111; margin: 0; }
  .wrap { position: relative; width: 100%; height: 100%; border: 2px solid #1e3a8a; border-radius: 6px; padding: 6mm; }

  .top { text-align: center; margin-top: 1mm; }
  .m1 { color: #1e3a8a; font-weight: 800; font-size: 9pt; letter-spacing: 0.5pt; text-transform: uppercase; }
  .m2 { color: #1e3a8a; font-weight: 800; font-size: 9pt; letter-spacing: 0.5pt; text-transform: uppercase; margin-top: 1mm; }
  .title { color: #1e3a8a; font-weight: 900; font-size: 12pt; margin-top: 1.2mm; }
  .unit { color: #1e3a8a; font-weight: 800; font-size: 10pt; margin-top: 0.6mm; }

  .grid { display: grid; grid-template-columns: 1fr 34mm; gap: 3mm; margin-top: 4mm; }

  .rows { display: grid; grid-template-columns: 30mm 38mm 45mm; grid-auto-rows: 6.2mm; column-gap: 2mm; }
  .label { font-weight: 700; font-size: 9pt; align-self: end; }
  .dots { align-self: end; height: 2px; background-image: radial-gradient(#444 1px, transparent 1px); background-size: 4px 2px; background-repeat: repeat-x; background-position: left center; margin-bottom: 1.6mm; }
  .value { font-size: 10pt; align-self: end; white-space: pre-wrap; }

  .row { display: contents; }

  .photoBox { width: 34mm; height: 40mm; border: 1px solid #333; display: flex; align-items: center; justify-content: center; overflow: hidden; }
  .photoBox img { width: 100%; height: 100%; object-fit: cover; }
  .qrBox { width: 30mm; height: 30mm; border: 1px solid #333; display: flex; align-items: center; justify-content: center; margin-top: 2mm; }
  .qrBox img { width: 95%; height: 95%; object-fit: contain; }

  .sig { position: absolute; right: 12mm; bottom: 18mm; text-align: center; }
  .sig .line { width: 42mm; border-bottom: 1px solid #333; margin-bottom: 1mm; }
  .sig small { font-size: 9pt; }
  .sig .name { font-weight: 700; margin-top: 2mm; }
  .sig .role { font-size: 8pt; }

  .footer { position: absolute; left: 6mm; right: 6mm; bottom: 6mm; text-align: center; font-size: 8pt; color: #333; }
  .url { color: #1e3a8a; }
</style>
</head>
<body>
  <div class="wrap">
    <div class="top">
      <div class="m1">EDUCATE AGITATE ORGANISE</div>
      <div class="m2">JAI BHIM JAI BHARAT</div>
      <div class="title">BAHUJAN SAMAJ PARTY (BSP)</div>
      <div class="unit">TAMILNADU UNIT</div>
    </div>

    <div class="grid">
      <div class="rows">
        <div class="row">
          <div class="label">MEMBERSHIP NO:</div>
          <div class="dots"></div>
          <div class="value">{{ membership_no }}</div>
        </div>
        <div class="row">
          <div class="label">ACTIVE NO:</div>
          <div class="dots"></div>
          <div class="value">{{ active_no }}</div>
        </div>
        <div class="row">
          <div class="label">Name :</div>
          <div class="dots"></div>
          <div class="value">{{ name }}</div>
        </div>
        <div class="row">
          <div class="label">Profession :</div>
          <div class="dots"></div>
          <div class="value">{{ profession }}</div>
        </div>
        <div class="row">
          <div class="label">Designation :</div>
          <div class="dots"></div>
          <div class="value">{{ designation }}</div>
        </div>
        <div class="row">
          <div class="label">Mandal :</div>
          <div class="dots"></div>
          <div class="value">{{ mandal }}</div>
        </div>
        <div class="row">
          <div class="label">D.O.B :</div>
          <div class="dots"></div>
          <div class="value">{{ dob }}</div>
        </div>
        <div class="row">
          <div class="label">Blood Group :</div>
          <div class="dots"></div>
          <div class="value">{{ blood_group }}</div>
        </div>
        <div class="row">
          <div class="label">Contact No :</div>
          <div class="dots"></div>
          <div class="value">{{ contact_no }}</div>
        </div>
        <div class="row">
          <div class="label">Address :</div>
          <div class="dots"></div>
          <div class="value">{{ address }}</div>
        </div>
      </div>

      <div>
        <div class="photoBox">
          {% if photo_data_url %}
          <img src="{{ photo_data_url }}" alt="Photo">
          {% else %}
          <span style="font-size:8pt;color:#666;">Photo</span>
          {% endif %}
        </div>
        <div class="qrBox">
          <img src="{{ qr_data_url }}" alt="QR">
        </div>
      </div>
    </div>

    <div class="sig">
      <div class="line"></div>
      <small>Holder Sign :</small>
      <div class="name">(P. ANANDAN)</div>
      <div class="role">President</div>
    </div>

    <div class="footer">
      <div>Dadasaheb Kanshiram Bhavan, 2/14 - A Veteran Lines, Pallavaram Cantonment, St. Stephen's School Near, Chennai, Tamil Nadu 600043</div>
      <div class="url">https://tnbsp.org/</div>
    </div>
  </div>
</body>
</html>
"""
