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

from dotenv import load_dotenv

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Annotated, List, Optional, Union, Sequence

import sqlite3

# ================================================================
# Environment and Paths
# ================================================================
load_dotenv()

if platform.system() == "Darwin":  # macOS local dev
    BASE_UPLOAD_DIR = Path("./volunteers_files")
else:
    BASE_UPLOAD_DIR = Path(os.getenv("BASE_UPLOAD_DIR", "/home/mfnssihw/volunteers_files"))

TEMP_UPLOAD_DIR = Path(os.getenv("TEMP_UPLOAD_DIR", BASE_UPLOAD_DIR / "tmp"))
PDF_UPLOAD_DIR = Path(os.getenv("PDF_UPLOAD_DIR", BASE_UPLOAD_DIR / "voterid_proof"))
PHOTO_UPLOAD_DIR = Path(os.getenv("PHOTO_UPLOAD_DIR", BASE_UPLOAD_DIR / "photos"))
CARDS_DIR = Path(os.getenv("CARDS_DIR", BASE_UPLOAD_DIR / "cards"))
STATIC_DIR = Path("./static").resolve()

VERIFICATION_SESSIONS = {}

app = FastAPI(
    title="Membership Workflow API",
    description="Document verification, member creation, and Pillow card rendering.",
    version="3.2.0"
)

# ================================================================
# Models
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
    dob: Optional[date] = Field("1990-01-15", description="YYYY-MM-DD")
    blood_group: Optional[BloodGroup] = Field(BloodGroup.O_pos, description="Blood Group")
    contact_no: Optional[str] = Field("9876543210", description="10-digit Contact", pattern=r'^\d{10}$')
    address: Optional[str] = Field("123, V.H. Road, Coimbatore - 641001", description="Address")

class PaymentUpdate(BaseModel):
    member_id: int
    status: str

# ================================================================
# SQLite
# ================================================================
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

def scale_pos(pos: Union[int, float, Sequence[Union[int, float, str]], str], scale: float):
    def to_num(x):
        if isinstance(x, (int, float)):
            return x
        if isinstance(x, str):
            try:
                return float(x)
            except ValueError:
                raise TypeError(f"Non-numeric position element: {x!r}")
        raise TypeError(f"Unsupported position type: {type(x).__name__}")
    if isinstance(pos, (int, float, str)):
        return int(round(to_num(pos) * scale))
    if isinstance(pos, (list, tuple)):
        return tuple(int(round(to_num(v) * scale)) for v in pos)
    raise TypeError(f"Unsupported position container: {type(pos).__name__}")

# ================================================================
# EPIC extraction
# ================================================================
def find_epic_in_text(text):
    if not text:
        return None
    patterns = [
        r'(?i)(?:EPIC No|Identity Card)\s*.*?\s*\b([A-Z]{3}[0-9]{7})\b',
        r'\b([A-Z]{3}[0-9]{7})\b'
    ]
    for pattern in patterns:
        m = re.search(pattern, text, re.DOTALL)
        if m:
            return m.group(1).strip().replace(" ", "")
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
    for d in [TEMP_UPLOAD_DIR, PDF_UPLOAD_DIR, PHOTO_UPLOAD_DIR, CARDS_DIR, STATIC_DIR]:
        os.makedirs(d, exist_ok=True)
    sqlite_init_schema()
    print("✅ Startup ready")

# ================================================================
# Endpoints (DB work stubbed)
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
    return {"message": "Verification successful. Use this token to submit member details.",
            "verification_token": token}

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

    generated_membership_no = generate_membership_no(1)
    new_member_id = 1
    if verification_token in VERIFICATION_SESSIONS:
        del VERIFICATION_SESSIONS[verification_token]

    return {"message": "Details submitted. Proceed to payment.",
            "member_id": new_member_id,
            "membership_no": generated_membership_no}

@app.post("/update-payment/")
async def update_payment_endpoint(update_data: PaymentUpdate):
    return {"message": f"Payment {update_data.status}. (Stub response with MySQL disabled)"}

# ================================================================
# Pillow card generator (Option 1: overlay above photo)
# ================================================================
BASE_W = 1289.0  # Reference width for coordinates

PIL_POSITIONS = {
    # Header label colon Xs (base image measures)
    "id_colon_x":         210,
    "membership_colon_x": 690,
    "active_colon_x":    1080,

    # Shared Y baseline for header row
    "header_values_y":    275,

    # Left column text positions
    "left_value_x":       450,
    "name_y":             357,
    "profession_y":       398,
    "designation_y":      439,
    "mandal_y":           480,
    "dob_y":              521,
    "blood_y":            562,
    "contact_y":          603,
    "address_y":          644,

    # Photo box (x, y, w, h)
    "photo_box":          (923, 357, 200, 240),

    # Signature overlay anchor (top-left) at base width 1289 px
    "signature_overlay_xy": (860, 430)
}

AFTER_COLON_MARGIN = 12  # px after colon where header values begin (base)

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
    lines, cur = [], []
    for w in words:
        cand = " ".join(cur + [w])
        if len(cand) <= max_chars:
            cur.append(w)
        else:
            if cur:
                lines.append(" ".join(cur))
            cur = [w]
    if cur:
        lines.append(" ".join(cur))
    return lines

def fetch_member_data(member_id: Optional[int] = None, membership_no: Optional[str] = None) -> dict:
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
    template_path = STATIC_DIR / "card_template.png"
    if not template_path.exists():
        raise HTTPException(status_code=500, detail="Template not found at static/card_template.png")

    # RGBA for correct alpha compositing
    base = Image.open(template_path).convert("RGBA")
    draw = ImageDraw.Draw(base)

    W, H = base.size
    scale = W / BASE_W

    # Fonts
    text_font  = _load_font(int(22 * scale))
    bold_font  = _load_font(int(22 * scale), bold=True)
    small_font = _load_font(int(18 * scale))

    BLACK  = "#000000"
    GRAY   = "#333333"
    SILVER = "#CCCCCC"
    OUTLINE= "#666666"

    # Header values aligned with titles
    id_val = member.get("id")
    id_number = f"TN{id_val:06d}" if isinstance(id_val, int) else f"TN{datetime.utcnow().strftime('%y')}{str(uuid.uuid4())[:6].upper()}"
    membership_number = member.get("membership_no") or ""
    active_number     = member.get("active_no") or f"ACT{datetime.utcnow().strftime('%m%y')}{str(uuid.uuid4())[:4].upper()}"

    header_y = scale_pos(PIL_POSITIONS["header_values_y"], scale)
    id_x  = scale_pos(PIL_POSITIONS["id_colon_x"] + AFTER_COLON_MARGIN, scale)
    mem_x = scale_pos(PIL_POSITIONS["membership_colon_x"] + AFTER_COLON_MARGIN, scale)
    act_x = scale_pos(PIL_POSITIONS["active_colon_x"] + AFTER_COLON_MARGIN, scale)

    draw.text((id_x,  header_y), str(id_number),         font=small_font, fill=BLACK, anchor="ls")
    draw.text((mem_x, header_y), str(membership_number), font=small_font, fill=BLACK, anchor="ls")
    draw.text((act_x, header_y), str(active_number),     font=small_font, fill=BLACK, anchor="ls")

    # Left column values
    vx = scale_pos(PIL_POSITIONS["left_value_x"], scale)
    draw.text((vx, scale_pos(PIL_POSITIONS["name_y"], scale)),        (member.get("name") or "").upper(), font=bold_font,  fill=BLACK, anchor="ls")
    draw.text((vx, scale_pos(PIL_POSITIONS["profession_y"], scale)),  member.get("profession") or "",     font=text_font,  fill=BLACK, anchor="ls")
    draw.text((vx, scale_pos(PIL_POSITIONS["designation_y"], scale)), member.get("designation") or "",    font=text_font,  fill=BLACK, anchor="ls")
    draw.text((vx, scale_pos(PIL_POSITIONS["mandal_y"], scale)),      member.get("mandal") or "",         font=text_font,  fill=BLACK, anchor="ls")
    dob_val = member.get("dob")
    dob_str = str(dob_val) if dob_val is not None else ""
    draw.text((vx, scale_pos(PIL_POSITIONS["dob_y"], scale)),         dob_str,                            font=text_font,  fill=BLACK, anchor="ls")
    draw.text((vx, scale_pos(PIL_POSITIONS["blood_y"], scale)),       member.get("blood_group") or "",    font=text_font,  fill=BLACK, anchor="ls")
    draw.text((vx, scale_pos(PIL_POSITIONS["contact_y"], scale)),     member.get("contact_no") or "",     font=text_font,  fill=BLACK, anchor="ls")

    # Address (2 lines)
    addr = member.get("address") or ""
    lines = _wrap_text(addr, 35)
    addr_y = scale_pos(PIL_POSITIONS["address_y"], scale)
    line_gap = scale_pos(25, scale)
    for i, line in enumerate(lines[:2]):
        draw.text((vx, addr_y + i * line_gap), line, font=text_font, fill=BLACK, anchor="ls")

    # ------------------------------------------------------------
    # OPTION 1 IMPLEMENTATION: photo below, overlay above
    # ------------------------------------------------------------

    # 1) Paste member photo FIRST (below signature)
    px, py, pw, ph = scale_pos(PIL_POSITIONS["photo_box"], scale)
    photo_path = member.get("photo_path")
    if photo_path and Path(photo_path).exists():
        try:
            pimg = Image.open(photo_path).convert("RGBA").resize((pw, ph), Image.Resampling.LANCZOS)
            base.alpha_composite(pimg, (px, py))
        except Exception as e:
            print(f"Photo error: {e}")
            draw.rectangle([px, py, px + pw, py + ph], fill=SILVER, outline=OUTLINE, width=2)
            draw.text((px + pw // 2, py + ph // 2), "PHOTO\nERROR", font=small_font, fill=GRAY, anchor="mm")
    else:
        draw.rectangle([px, py, px + pw, py + ph], fill=SILVER, outline=OUTLINE, width=2)
        draw.text((px + pw // 2, py + ph // 2), "PHOTO\nNOT FOUND", font=small_font, fill=GRAY, anchor="mm")

    # 2) Composite signature overlay PNG ABOVE the photo
    overlay_path = STATIC_DIR / "signature_overlay.png"
    if overlay_path.exists():
        try:
            oimg = Image.open(overlay_path).convert("RGBA")
            # Scale overlay with overall template width
            ow, oh = oimg.size
            oimg = oimg.resize((int(ow * scale), int(oh * scale)), Image.Resampling.LANCZOS)

            # Anchor; tweak nudge_x / nudge_y for quick micro-adjustment (±5–10 px)
            sx_base, sy_base = PIL_POSITIONS["signature_overlay_xy"]
            nudge_x, nudge_y = 0, 0
            sx = scale_pos(sx_base + nudge_x, scale)
            sy = scale_pos(sy_base + nudge_y, scale)

            base.alpha_composite(oimg, (sx, sy))
        except Exception as e:
            print(f"Signature overlay error: {e}")
    else:
        # If overlay missing, do nothing (avoids ghosted double drawing)
        print("Warning: static/signature_overlay.png not found; skipping overlay composite")

    # ------------------------------------------------------------

    # Save
    file_stub = (membership_number or f"id-{member.get('id') or 'unknown'}").replace("/", "-")
    out_path = CARDS_DIR / f"bsp_membership_card_{file_stub}.png"
    base.convert("RGB").save(out_path, "PNG", quality=95, optimize=True)
    return out_path

# ================================================================
# Endpoints: generate and download
# ================================================================
@app.post("/generate-card-pillow/")
async def generate_card_pillow(
    member_id: Annotated[Optional[int], Form()] = None,
    membership_no: Annotated[Optional[str], Form()] = None
):
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
    p = Path(card_path)
    if not p.exists() or not p.is_file():
        raise HTTPException(status_code=404, detail="Card file not found")
    filename = f"membership_card_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.png"
    return FileResponse(path=str(p), filename=filename, media_type="image/png")

# ================================================================
# Helper to seed SQLite quickly
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
