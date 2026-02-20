from __future__ import annotations

from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from pathlib import Path
from typing import Any, Dict, List

from rag import SimpleRAG

app = FastAPI(title="Import AI Assistant - Prototype (Fast RAG)")

# -------------------- Persistent knowledge base folder --------------------
BASE_DIR = Path(__file__).parent
KB_DIR = BASE_DIR / "knowledge_base"
KB_DIR.mkdir(exist_ok=True)

rag = SimpleRAG()


def rebuild_index_from_kb() -> int:
    """
    Rebuild TF-IDF index from ALL .txt files in KB_DIR (fast).
    Returns number of files indexed.
    """
    rag.chunks = []  # reset chunks (SimpleRAG stores chunks here)
    files = sorted(KB_DIR.glob("*.txt"))
    for fp in files:
        rag.ingest_file(fp)
    return len(files)


# Copy starter knowledge into KB once (optional)
starter = BASE_DIR / "sample_knowledge.txt"
if starter.exists():
    starter_copy = KB_DIR / "sample_knowledge.txt"
    if not starter_copy.exists():
        starter_copy.write_text(
            starter.read_text(encoding="utf-8", errors="ignore"),
            encoding="utf-8",
            errors="ignore",
        )

rebuild_index_from_kb()

# -------------------- Demo duty rates (prototype only) --------------------
DEMO_DUTY_RATES = {
    "9503": {"bcd": 20.0, "igst": 18.0, "note": "Demo rates only. Verify with CBIC tariff."},  # Toys
    "9405": {"bcd": 10.0, "igst": 18.0, "note": "Demo rates only. Verify with CBIC tariff."},  # Lighting
    "8541": {"bcd": 7.5, "igst": 12.0, "note": "Demo rates only. Verify with CBIC tariff."},   # Solar
    "8501": {"bcd": 7.5, "igst": 18.0, "note": "Demo rates only. Verify with CBIC tariff."},   # Motors
}


class QueryRequest(BaseModel):
    product_description: str
    country_of_origin: str | None = None
    extra_details: str | None = None
    assessable_value_inr: float | None = None


# -------------------- HSN suggestion (ranked) --------------------
def naive_hsn_suggestions(text: str) -> List[Dict[str, Any]]:
    """
    Ranked keyword scoring so unrelated HSNs don't appear unless query truly matches them.
    """
    t = text.lower()

    rules = [
        ("9503", ["toy", "toys", "kid", "kids", "child", "children"], "Toys/children keywords found."),
        ("9405", ["led", "lamp", "light", "lighting", "decorative"], "Lighting keywords found."),
        ("8541", ["solar", "panel", "photovoltaic", "pv", "module", "cell"], "Solar keywords found."),
        ("8501", ["motor", "electric motor", "ac motor", "dc motor"], "Motor keywords found."),
    ]

    scored: List[tuple[int, Dict[str, Any]]] = []
    for hsn, keys, reason in rules:
        hits = sum(1 for k in keys if k in t)
        if hits > 0:
            conf = min(0.60 + hits * 0.08, 0.90)
            scored.append((hits, {"hsn": hsn, "confidence": round(conf, 2), "reason": reason}))

    if not scored:
        return [{
            "hsn": "TBD",
            "confidence": 0.40,
            "reason": "Not enough info. Need material/usage/technical specs."
        }]

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored[:3]]


# -------------------- Compliance flags --------------------
def compliance_flags(text: str) -> List[Dict[str, str]]:
    t = text.lower()
    flags = []

    if any(k in t for k in ["wifi", "bluetooth", "wireless", "rf", "radio"]):
        flags.append({"flag": "WPC/ETA", "severity": "medium", "why": "Wireless/RF features may require WPC/ETA compliance."})

    if any(k in t for k in ["food", "edible", "snack", "milk", "spice", "supplement"]):
        flags.append({"flag": "FSSAI", "severity": "high", "why": "Food items may require FSSAI compliance."})

    if any(k in t for k in ["toy", "toys"]):
        flags.append({"flag": "BIS", "severity": "high", "why": "Toys often require safety compliance checks (BIS)."})
    return flags


# -------------------- Duty calculator (demo) --------------------
def compute_demo_duty(hsn: str, assessable_value: float) -> Dict[str, Any]:
    """
    Demo estimation:
    - BCD = assessable_value * bcd_rate
    - SWS = 10% of BCD (demo)
    - IGST base = assessable_value + BCD + SWS
    - IGST = IGST base * igst_rate
    """
    r = DEMO_DUTY_RATES.get(hsn)
    if not r:
        return {
            "assessable_value": round(assessable_value, 2),
            "bcd_rate": None,
            "bcd_amount": None,
            "sws_rate": 10.0,
            "sws_amount": None,
            "igst_rate": None,
            "igst_amount": None,
            "total_estimated": None,
            "note": "No demo duty rate found for this HSN. Please verify using CBIC tariff.",
        }

    bcd = assessable_value * (r["bcd"] / 100.0)
    sws = bcd * 0.10
    igst_base = assessable_value + bcd + sws
    igst = igst_base * (r["igst"] / 100.0)
    total = bcd + sws + igst

    return {
        "assessable_value": round(assessable_value, 2),
        "bcd_rate": r["bcd"],
        "bcd_amount": round(bcd, 2),
        "sws_rate": 10.0,
        "sws_amount": round(sws, 2),
        "igst_rate": r["igst"],
        "igst_amount": round(igst, 2),
        "total_estimated": round(total, 2),
        "note": r["note"],
    }


# -------------------- Ingest many TXT files (persistent) --------------------
@app.post("/ingest")
async def ingest(file: UploadFile = File(...)):
    data = await file.read()
    name = file.filename or "uploaded.txt"

    # Keep prototype fast: accept TXT only
    if not name.lower().endswith(".txt"):
        return {
            "status": "error",
            "message": "For fast prototype, please upload .txt files only (convert PDF to TXT first)."
        }

    safe_name = name.replace("/", "_").replace("\\", "_")
    out = KB_DIR / safe_name
    out.write_bytes(data)

    total = rebuild_index_from_kb()
    return {"status": "ok", "message": f"Saved + indexed: {safe_name}. Total knowledge files: {total}"}


@app.get("/kb_list")
def kb_list():
    files = [p.name for p in sorted(KB_DIR.glob("*.txt"))]
    return {"count": len(files), "files": files}


# -------------------- Query --------------------
@app.post("/query")
async def query(req: QueryRequest):
    # Build query text for retrieval
    q = req.product_description.strip()
    if req.extra_details and req.extra_details.strip():
        q += "\nExtra: " + req.extra_details.strip()
    if req.country_of_origin and req.country_of_origin.strip():
        q += "\nOrigin: " + req.country_of_origin.strip()

    # RAG retrieval
    retrieved = rag.search(q, k=5)

    citations: List[Dict[str, Any]] = []
    context_blocks: List[str] = []

    for ch, score in retrieved:
        # Evidence snippet for table
        short = ch.text[:140].replace("\n", " ").strip()
        citations.append({
            "source": ch.source,
            "score": round(score, 3),
            "snippet": short + "..."
        })

        # Context preview in UI
        snippet = ch.text[:520].replace("\n", " ").strip()
        context_blocks.append(f"[{ch.source}] {snippet}...")

    # HSN + duty
    hsn_list = naive_hsn_suggestions(req.product_description)
    top_hsn = hsn_list[0]["hsn"]
    assessable_value = float(req.assessable_value_inr) if req.assessable_value_inr is not None else 100000.0
    duty_calc = compute_demo_duty(top_hsn, assessable_value)

    # Response
    return {
        "product_summary": req.product_description,
        "hsn_suggestions": hsn_list,
        "duty_structure": duty_calc,
        "restrictions": compliance_flags(req.product_description),
        "required_documents": [
            "Commercial Invoice",
            "Packing List",
            "Bill of Lading / Airway Bill",
            "Certificate of Origin",
            "Product specification / datasheet",
            "Insurance (if applicable)",
            "Importer IEC details",
        ],
        "verification_steps": [
            {"source": "CBIC Customs Tariff", "how": "Confirm chapter/heading notes for the suggested HSN and duty rates."},
            {"source": "DGFT / ITC(HS)", "how": "Check if the product is restricted, needs license, or has policy conditions."},
            {"source": "ICEGATE", "how": "Review filing requirements and clearance process documentation."},
        ],
        "rag_context_preview": context_blocks[:2],
        "citations": citations,
        "missing_info_questions": [
            "What is the exact product material/composition?",
            "Is it a finished consumer product or a component/part?",
            "Does it include wireless modules or batteries?",
            "What is the intended use and technical specification?",
        ],
    }