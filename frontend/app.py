import streamlit as st
import requests

API = "http://127.0.0.1:8000"

# -------------------- PAGE CONFIG --------------------
st.set_page_config(
    page_title="Import AI Assistant (Prototype)",
    layout="wide",
    page_icon="📦",
)

# -------------------- LIGHT SAAS CSS --------------------
CUSTOM_CSS = """
<style>
.block-container {padding-top: 0.7rem; padding-bottom: 2rem; max-width: 1320px;}
div[data-testid="stToolbar"] {visibility: hidden; height: 0;}

/* background */
.stApp{
  background:
    radial-gradient(900px 500px at 12% 8%, rgba(59,130,246,0.14), transparent 60%),
    radial-gradient(900px 500px at 90% 18%, rgba(16,185,129,0.12), transparent 60%),
    radial-gradient(900px 500px at 55% 100%, rgba(236,72,153,0.08), transparent 55%),
    #f8fafc;
}

/* sticky header */
.header{
  position: sticky;
  top: 0;
  z-index: 10;
  backdrop-filter: blur(10px);
  background: rgba(248,250,252,0.75);
  border: 1px solid #e2e8f0;
  border-radius: 18px;
  padding: 14px 16px;
  margin-bottom: 14px;
  box-shadow: 0 10px 24px rgba(15,23,42,0.06);
}
.hrow{display:flex; justify-content:space-between; align-items:center; gap:14px;}
.title{font-size: 24px; font-weight: 900; letter-spacing: -0.4px; color:#0f172a; margin:0;}
.sub{font-size: 12px; color:#475569; margin-top:4px;}
.chips{display:flex; gap:8px; flex-wrap:wrap; justify-content:flex-end;}
.chip{
  display:inline-flex; align-items:center; gap:8px;
  padding: 6px 10px;
  border-radius: 999px;
  font-size: 12px;
  border: 1px solid rgba(37,99,235,0.18);
  background: rgba(59,130,246,0.10);
  color:#1e40af;
}
.chip-ok{border-color: rgba(16,185,129,0.22); background: rgba(16,185,129,0.10); color:#065f46;}
.chip-warn{border-color: rgba(245,158,11,0.25); background: rgba(245,158,11,0.14); color:#92400e;}

/* cards */
.card{
  border-radius: 16px;
  padding: 16px;
  background:#ffffff;
  border:1px solid #e2e8f0;
  box-shadow: 0 10px 26px rgba(15,23,42,0.05);
  margin-bottom: 14px;
}
.card h3{margin:0 0 10px 0; font-size:15px; color:#0f172a;}
.muted{color:#64748b; font-size:12px;}
hr.soft{border:none; height:1px; background:#e2e8f0; margin:12px 0;}

/* KPI cards */
.kpi{
  border-radius: 16px;
  padding: 14px 14px;
  background: linear-gradient(135deg, #ffffff, #f8fafc);
  border:1px solid #e2e8f0;
  box-shadow: 0 10px 22px rgba(15,23,42,0.05);
}
.kpi-label{font-size:12px; color:#64748b; margin:0;}
.kpi-value{font-size:22px; font-weight:900; color:#0f172a; margin:2px 0 0 0;}
.kpi-sub{font-size:12px; color:#475569; margin:4px 0 0 0;}

/* buttons */
.stButton button{
  border-radius: 14px !important;
  padding: 0.62rem 1rem !important;
  border: 1px solid #e2e8f0 !important;
  background: #ffffff !important;
  color: #0f172a !important;
}
.primary-btn .stButton button{
  background: linear-gradient(135deg, #2563eb, #10b981) !important;
  border: none !important;
  color: #ffffff !important;
  font-weight: 750;
  box-shadow: 0 10px 18px rgba(37,99,235,0.18);
}
.primary-btn .stButton button:hover{
  transform: translateY(-1px);
  box-shadow: 0 14px 24px rgba(37,99,235,0.22);
}
.danger-btn .stButton button{
  background: #fee2e2 !important;
  border: 1px solid #fecaca !important;
  color:#991b1b !important;
  font-weight:700;
}

/* inputs */
div[data-baseweb="textarea"] textarea,
div[data-baseweb="input"] input{
  border-radius: 14px !important;
  border: 1px solid #e2e8f0 !important;
  background:#fff !important;
}

/* severity pills */
.sev{
  display:inline-block;
  padding: 3px 8px;
  border-radius: 999px;
  font-size: 11px;
  margin-left: 8px;
  border:1px solid #e2e8f0;
  background:#f1f5f9;
  color:#334155;
}
.sev-high{border-color:#fecaca; background:#fee2e2; color:#991b1b;}
.sev-medium{border-color:#fde68a; background:#fef3c7; color:#92400e;}
.sev-low{border-color:#bbf7d0; background:#dcfce7; color:#065f46;}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# -------------------- Helpers --------------------
def fmt_inr(x):
    try:
        return f"₹{float(x):,.2f}"
    except Exception:
        return f"₹{x}"

def sev_badge(sev: str) -> str:
    s = (sev or "").lower()
    if s == "high":
        return "<span class='sev sev-high'>HIGH</span>"
    if s == "medium":
        return "<span class='sev sev-medium'>MED</span>"
    return "<span class='sev sev-low'>LOW</span>"

# -------------------- Session --------------------
if "last_inputs" not in st.session_state:
    st.session_state["last_inputs"] = {}

# -------------------- HEADER --------------------
result = st.session_state.get("result")
hsn_count = len(result.get("hsn_suggestions", [])) if result else 0
flag_count = len(result.get("restrictions", [])) if result else 0
cit_count = len(result.get("citations", [])) if result else 0

st.markdown(
    f"""
    <div class="header">
      <div class="hrow">
        <div>
          <div class="title">📦 Import AI Assistant <span class="muted">(Prototype)</span></div>
          <div class="sub">HSN suggestions • duty estimate • compliance flags • docs checklist • evidence (RAG)</div>
        </div>
        <div class="chips">
          <div class="chip chip-ok">✅ Ready</div>
          <div class="chip">HSN: {hsn_count}</div>
          <div class="chip {'chip-warn' if flag_count else 'chip-ok'}">Flags: {flag_count}</div>
          <div class="chip">Citations: {cit_count}</div>
        </div>
      </div>
    </div>
    """,
    unsafe_allow_html=True
)

# -------------------- TOP ACTIONS --------------------
a1, a2, a3 = st.columns([1.2, 1.2, 1.0])
with a1:
    with st.expander("🧠 Knowledge Base (RAG) — upload internal .txt guides", expanded=False):
        files = st.file_uploader("Upload .txt knowledge file(s)", type=["txt"], accept_multiple_files=True)
        c1, c2 = st.columns(2)
        ingest_btn = c1.button("Ingest ✅", use_container_width=True)
        if ingest_btn:
            if not files:
                st.warning("Upload one or more .txt files first.")
            else:
                ok = 0
                with st.spinner("Indexing knowledge files..."):
                    for f in files:
                        try:
                            r = requests.post(
                                f"{API}/ingest",
                                files={"file": (f.name, f.getvalue())},
                                timeout=600
                            )
                            r.raise_for_status()
                            ok += 1
                        except Exception as e:
                            st.error(f"Ingest failed for {f.name}: {e}")
                st.success(f"Ingested {ok}/{len(files)} file(s).")

with a2:
    with st.expander("🧾 Product Query", expanded=True):
        with st.form("query_form", clear_on_submit=False):
            desc = st.text_area(
                "Product description *",
                height=110,
                placeholder="e.g., Importing plastic toys for children under 14, packed in sets..."
            )
            r1, r2, r3 = st.columns([1, 1, 1])
            with r1:
                origin = st.text_input("Country of origin", placeholder="e.g., China")
            with r2:
                value = st.number_input("Assessable value (INR)", min_value=0.0, value=100000.0, step=1000.0)
            with r3:
                demo = st.selectbox("Quick demo", ["None", "🧸 Toys", "💡 LED", "⌚ Wireless"], index=0)

            extra = st.text_area(
                "Extra details",
                height=70,
                placeholder="material, composition %, end-use, model/specs, wireless/battery..."
            )

            st.markdown("<div class='primary-btn'>", unsafe_allow_html=True)
            submitted = st.form_submit_button("🚀 Run Analysis", use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        if demo != "None":
            st.caption("Demo notes (copy/paste into fields if needed):")
            if demo == "🧸 Toys":
                st.info("Desc: Importing plastic toys for children under 14 years, packed in sets.\n"
                        "Origin: Vietnam\nExtra: Material: plastic. Age group: 3-8 years.\nValue: 100000")
            elif demo == "💡 LED":
                st.info("Desc: Importing LED decorative lighting fittings for home use, 220V.\n"
                        "Origin: China\nExtra: Finished consumer product for decoration.\nValue: 120000")
            elif demo == "⌚ Wireless":
                st.info("Desc: Importing smartwatch with WiFi and Bluetooth connectivity.\n"
                        "Origin: China\nExtra: Wireless product with RF module; provide datasheet.\nValue: 150000")

with a3:
    st.markdown("<div class='card'><h3>⚙️ Actions</h3><div class='muted'>Report & output controls</div>", unsafe_allow_html=True)
    clear_output = st.button("Clear output 🧹", use_container_width=True)

    if clear_output:
        st.session_state.pop("result", None)
        st.session_state["last_inputs"] = {}
        st.success("Cleared output.")

    # PDF button appears enabled only after query
    can_pdf = bool(st.session_state.get("last_inputs"))
    if not can_pdf:
        st.caption("Run analysis to enable PDF export.")
    pdf_click = st.button("Generate PDF 📄", use_container_width=True, disabled=not can_pdf)

    if pdf_click and can_pdf:
        try:
            with st.spinner("Generating PDF..."):
                pdf_res = requests.post(f"{API}/export_pdf", json=st.session_state["last_inputs"], timeout=300)
                pdf_res.raise_for_status()
                st.download_button(
                    label="⬇️ Download PDF",
                    data=pdf_res.content,
                    file_name="import_ai_report.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
        except Exception as e:
            st.error(f"PDF export failed: {e}")

    st.markdown("</div>", unsafe_allow_html=True)

# -------------------- Run query --------------------
if "submitted" in locals() and submitted:
    if not desc.strip():
        st.warning("Please enter a product description.")
    else:
        payload = {
            "product_description": desc.strip(),
            "country_of_origin": origin.strip() if origin.strip() else None,
            "extra_details": extra.strip() if extra.strip() else None,
            "assessable_value_inr": float(value),
        }
        try:
            with st.spinner("Analyzing… pulling best HSN + compliance + evidence"):
                r = requests.post(f"{API}/query", json=payload, timeout=300)
                r.raise_for_status()
                st.session_state["result"] = r.json()
                st.session_state["last_inputs"] = payload
                st.rerun()
        except Exception as e:
            st.error(f"Query failed: {e}")

# -------------------- OUTPUT --------------------
result = st.session_state.get("result")
if not result:
    st.markdown("<div class='card'><h3>📊 Dashboard</h3><div class='muted'>Run analysis to see results.</div></div>", unsafe_allow_html=True)
    st.stop()

hsns = result.get("hsn_suggestions", [])
flags = result.get("restrictions", [])
cits = result.get("citations", [])
duty = result.get("duty_structure", {}) or {}
docs = result.get("required_documents", []) or []
steps = result.get("verification_steps", []) or []
preview = result.get("rag_context_preview", []) or []

# -------------------- KPIs --------------------
k1, k2, k3, k4 = st.columns(4)
with k1:
    st.markdown(f"<div class='kpi'><p class='kpi-label'>HSN candidates</p><p class='kpi-value'>{len(hsns)}</p><p class='kpi-sub'>Ranked suggestions</p></div>", unsafe_allow_html=True)
with k2:
    st.markdown(f"<div class='kpi'><p class='kpi-label'>Compliance flags</p><p class='kpi-value'>{len(flags)}</p><p class='kpi-sub'>Severity based</p></div>", unsafe_allow_html=True)
with k3:
    st.markdown(f"<div class='kpi'><p class='kpi-label'>Citations</p><p class='kpi-value'>{len(cits)}</p><p class='kpi-sub'>RAG evidence</p></div>", unsafe_allow_html=True)
with k4:
    total = duty.get("total_estimated")
    show = fmt_inr(total) if total is not None else "—"
    st.markdown(f"<div class='kpi'><p class='kpi-label'>Estimated duty</p><p class='kpi-value'>{show}</p><p class='kpi-sub'>Prototype</p></div>", unsafe_allow_html=True)

# -------------------- MAIN ROW --------------------
left, mid, right = st.columns([1.1, 1.3, 1.1], gap="large")

with left:
    st.markdown("<div class='card'><h3>🧾 HSN Suggestions</h3><div class='muted'>Top results + confidence</div>", unsafe_allow_html=True)
    if hsns:
        for i, s in enumerate(hsns[:6], start=1):
            st.write(f"**#{i}  {s.get('hsn','-')}** — confidence **{s.get('confidence','-')}**")
            if s.get("reason"):
                with st.expander("Why this HSN?", expanded=False):
                    st.write(s["reason"])
    else:
        st.info("No HSN suggestions returned.")
    st.markdown("</div>", unsafe_allow_html=True)

with mid:
    st.markdown("<div class='card'><h3>💰 Duty Estimate</h3><div class='muted'>Breakdown (prototype)</div>", unsafe_allow_html=True)
    if duty.get("total_estimated") is not None:
        m1, m2 = st.columns(2)
        m1.metric("Assessable Value", fmt_inr(duty.get("assessable_value")))
        m2.metric("Total Duty", fmt_inr(duty.get("total_estimated")))
        x1, x2, x3 = st.columns(3)
        x1.metric(f"BCD ({duty.get('bcd_rate')}%)", fmt_inr(duty.get("bcd_amount")))
        x2.metric(f"SWS ({duty.get('sws_rate')}%)", fmt_inr(duty.get("sws_amount")))
        x3.metric(f"IGST ({duty.get('igst_rate')}%)", fmt_inr(duty.get("igst_amount")))
        if duty.get("note"):
            st.caption(duty["note"])
    else:
        st.info(duty.get("note", "No duty estimate available."))
    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown("<div class='card'><h3>⚠️ Compliance</h3><div class='muted'>Flags + docs checklist</div>", unsafe_allow_html=True)

    st.markdown("**Flags**", unsafe_allow_html=True)
    if flags:
        for f in flags[:6]:
            sev = (f.get("severity") or "low")
            st.markdown(
                f"• **{f.get('flag','-')}** {sev_badge(sev)}<br/><span class='muted'>{f.get('why','')}</span>",
                unsafe_allow_html=True
            )
    else:
        st.success("No flags detected.")

    st.markdown("<hr class='soft'/>", unsafe_allow_html=True)
    st.markdown("**Required documents**", unsafe_allow_html=True)
    if docs:
        for doc in docs[:10]:
            st.write(f"✅ {doc}")
    else:
        st.caption("No document list returned.")

    st.markdown("</div>", unsafe_allow_html=True)

# -------------------- DETAILS TABS --------------------
st.markdown("<div class='card'><h3>🔎 Details</h3><div class='muted'>Deep dive + evidence</div>", unsafe_allow_html=True)
t1, t2, t3 = st.tabs(["Compliance & Steps", "Citations (RAG)", "RAG Context Preview"])

with t1:
    st.markdown("#### Verification Steps")
    if steps:
        for v in steps:
            st.write(f"• **{v.get('source','-')}**: {v.get('how','')}")
    else:
        st.info("No verification steps returned.")

with t2:
    st.markdown("#### Citations")
    if cits:
        st.dataframe(cits, use_container_width=True, hide_index=True)
    else:
        st.info("No citations found. Upload internal knowledge (.txt).")

with t3:
    st.markdown("#### Context Preview")
    if preview:
        for block in preview:
            st.write(block)
    else:
        st.info("No context preview returned.")

st.markdown("</div>", unsafe_allow_html=True)