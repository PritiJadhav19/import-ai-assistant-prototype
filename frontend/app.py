import streamlit as st
import requests

API = "http://127.0.0.1:8000"

# -------------------- PAGE CONFIG --------------------
st.set_page_config(
    page_title="Import AI Assistant (Prototype)",
    layout="wide",
    page_icon="📦",
)

# -------------------- CSS (Modern UI) --------------------
CUSTOM_CSS = """
<style>
.block-container {padding-top: 1.1rem; padding-bottom: 2.5rem; max-width: 1220px;}
/* hero */
.hero {
  border-radius: 18px;
  padding: 18px 22px;
  margin-bottom: 16px;
  background: linear-gradient(135deg, rgba(59,130,246,0.18), rgba(16,185,129,0.14), rgba(168,85,247,0.12));
  border: 1px solid rgba(255,255,255,0.10);
}
.hero-title {font-size: 30px; font-weight: 850; letter-spacing: -0.4px; margin: 0;}
.hero-sub {opacity: 0.88; margin-top: 6px; font-size: 14px;}
/* cards */
.card {
  border-radius: 16px;
  padding: 14px 16px;
  border: 1px solid rgba(255,255,255,0.10);
  background: rgba(255,255,255,0.03);
  margin-bottom: 12px;
}
.card h3 {margin: 0 0 8px 0; font-size: 16px;}
/* pills */
.pill {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
  border: 1px solid rgba(255,255,255,0.14);
  background: rgba(255,255,255,0.06);
  margin-right: 6px;
  margin-bottom: 6px;
}
hr.soft {border: none; height: 1px; background: rgba(255,255,255,0.10); margin: 12px 0;}
.small {font-size: 12px; opacity: 0.85;}
/* sidebar */
section[data-testid="stSidebar"] .block-container {padding-top: 1rem;}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# -------------------- Helpers --------------------
def pill(text: str) -> str:
    return f"<span class='pill'>{text}</span>"

def fmt_inr(x):
    try:
        return f"₹{float(x):,.2f}"
    except Exception:
        return f"₹{x}"

# -------------------- Hero --------------------
st.markdown(
    """
    <div class="hero">
      <div class="hero-title">📦 Import AI Assistant <span class="small">(Prototype)</span></div>
      <div class="hero-sub">HSN suggestions • duty estimate • compliance flags • document checklist • RAG citations</div>
    </div>
    """,
    unsafe_allow_html=True
)

# Keep inputs in session for PDF export
if "last_inputs" not in st.session_state:
    st.session_state["last_inputs"] = {}

# -------------------- Sidebar: Knowledge Upload --------------------
with st.sidebar:
    st.markdown("## 🧠 Knowledge Base (RAG)")
    st.caption("Upload internal guides as **.txt** files. The backend indexes them and uses citations in answers.")

    files = st.file_uploader(
        "Upload .txt knowledge file(s)",
        type=["txt"],
        accept_multiple_files=True
    )

    colA, colB = st.columns(2)
    ingest_btn = colA.button("Ingest ✅", use_container_width=True)
    clear_btn = colB.button("Clear UI 🧹", use_container_width=True)

    if ingest_btn:
        if not files:
            st.warning("Upload one or more .txt files first.")
        else:
            ok = 0
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
            st.success(f"Ingested {ok}/{len(files)} files.")

    if clear_btn:
        st.session_state.pop("result", None)
        st.session_state["last_inputs"] = {}
        st.success("Cleared output.")

# -------------------- Layout --------------------
col1, col2 = st.columns([1, 1], gap="large")

# -------------------- Left: Inputs --------------------
with col1:
    st.markdown("<div class='card'><h3>🧾 Product Query</h3>", unsafe_allow_html=True)

    desc = st.text_area(
        "Product description *",
        height=150,
        placeholder="e.g., Importing plastic toys for children under 14, packed in sets..."
    )

    a, b = st.columns(2)
    with a:
        origin = st.text_input("Country of origin (optional)", placeholder="e.g., China")
    with b:
        value = st.number_input(
            "Assessable value (INR)",
            min_value=0.0,
            value=100000.0,
            step=1000.0
        )

    extra = st.text_area(
        "Extra details (optional)",
        height=95,
        placeholder="material, composition %, usage, invoice notes, battery/wireless, model no..."
    )

    run_btn = st.button("🚀 Check Import Details", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Quick demo chips
    st.markdown("<div class='card'><h3>⚡ Quick Demo</h3>", unsafe_allow_html=True)
    d1, d2, d3 = st.columns(3)
    if d1.button("🧸 Toys", use_container_width=True):
        desc = "Importing plastic toys for children under 14 years, packed in sets."
        origin = "Vietnam"
        extra = "Material: plastic. Age group: 3-8 years."
        value = 100000.0
        st.session_state["_prefill"] = {"desc": desc, "origin": origin, "extra": extra, "value": value}
        st.rerun()

    if d2.button("💡 LED", use_container_width=True):
        desc = "Importing LED decorative lighting fittings for home use, 220V."
        origin = "China"
        extra = "Finished consumer product for decoration."
        value = 120000.0
        st.session_state["_prefill"] = {"desc": desc, "origin": origin, "extra": extra, "value": value}
        st.rerun()

    if d3.button("⌚ Wireless", use_container_width=True):
        desc = "Importing smartwatch with WiFi and Bluetooth connectivity."
        origin = "China"
        extra = "Wireless datasheet available with RF module details."
        value = 150000.0
        st.session_state["_prefill"] = {"desc": desc, "origin": origin, "extra": extra, "value": value}
        st.rerun()

    st.caption("Tip: Upload your internal guide first, then run a demo to see strong citations.")
    st.markdown("</div>", unsafe_allow_html=True)

# Prefill helper (shows user what to paste if needed)
if "_prefill" in st.session_state:
    p = st.session_state.pop("_prefill")
    st.info(
        "Demo values ready. If fields didn’t auto-fill, copy-paste:\n\n"
        f"Description: {p['desc']}\n"
        f"Origin: {p['origin']}\n"
        f"Extra: {p['extra']}\n"
        f"Assessable Value: {p['value']}"
    )

# Run query
if run_btn:
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
            r = requests.post(f"{API}/query", json=payload, timeout=300)
            r.raise_for_status()
            st.session_state["result"] = r.json()
            st.session_state["last_inputs"] = payload
        except Exception as e:
            st.error(f"Query failed: {e}")

# -------------------- Right: Output --------------------
with col2:
    st.markdown("<div class='card'><h3>🤖 AI Output</h3>", unsafe_allow_html=True)
    result = st.session_state.get("result")

    if not result:
        st.info("Run a query to see output.")
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        # Pills summary
        hsns = result.get("hsn_suggestions", [])
        flags = result.get("restrictions", [])
        cits = result.get("citations", [])
        pills = []
        if hsns:
            pills.append(pill(f"Top HSN: {hsns[0].get('hsn','-')}"))
        if flags:
            pills.append(pill(f"Flags: {len(flags)}"))
        if cits:
            pills.append(pill(f"Citations: {len(cits)}"))
        st.markdown("".join(pills), unsafe_allow_html=True)
        st.markdown("<hr class='soft'/>", unsafe_allow_html=True)

        tab1, tab2, tab3 = st.tabs(["HSN & Duty", "Compliance & Docs", "Evidence (RAG)"])

        with tab1:
            st.markdown("#### HSN Suggestions")
            for s in hsns:
                st.write(f"• **{s['hsn']}** — confidence **{s['confidence']}**")
                st.caption(s.get("reason", ""))

            st.markdown("#### Duty Structure (Prototype)")
            d = result.get("duty_structure", {})
            if d.get("total_estimated") is not None:
                m1, m2 = st.columns(2)
                with m1:
                    st.metric("Assessable Value", fmt_inr(d.get("assessable_value")))
                    st.metric(f"BCD ({d.get('bcd_rate')}%)", fmt_inr(d.get("bcd_amount")))
                with m2:
                    st.metric(f"SWS ({d.get('sws_rate')}% of BCD)", fmt_inr(d.get("sws_amount")))
                    st.metric(f"IGST ({d.get('igst_rate')}%)", fmt_inr(d.get("igst_amount")))
                st.success(f"✅ Estimated Total Duty: {fmt_inr(d.get('total_estimated'))}")
                if d.get("note"):
                    st.caption(d["note"])
            else:
                st.info(d.get("note", "No duty estimate available."))

        with tab2:
            st.markdown("#### Restrictions / Compliance Flags")
            if flags:
                for f in flags:
                    sev = (f.get("severity") or "").lower()
                    msg = f"**{f['flag']}** ({sev}) — {f['why']}"
                    if sev == "high":
                        st.error(msg)
                    elif sev == "medium":
                        st.warning(msg)
                    else:
                        st.info(msg)
            else:
                st.success("No flags detected from description (prototype).")

            st.markdown("#### Required Documents")
            docs = result.get("required_documents", [])
            if docs:
                for doc in docs:
                    st.write(f"✅ {doc}")

            st.markdown("#### Verification Steps")
            for v in result.get("verification_steps", []):
                st.write(f"• **{v['source']}**: {v['how']}")

        with tab3:
            st.markdown("#### Citations (RAG)")
            if cits:
                st.dataframe(cits, use_container_width=True, hide_index=True)
            else:
                st.info("No RAG citations found (upload more knowledge).")

            with st.expander("RAG context preview"):
                for block in result.get("rag_context_preview", []):
                    st.write(block)

        st.markdown("<hr class='soft'/>", unsafe_allow_html=True)

        # PDF Export
        st.markdown("#### 📄 Download Report")
        if st.button("Generate PDF Report 📄", use_container_width=True):
            payload = st.session_state.get("last_inputs", {})
            if not payload:
                st.warning("Run a query first, then generate PDF.")
            else:
                try:
                    pdf_res = requests.post(f"{API}/export_pdf", json=payload, timeout=300)
                    pdf_res.raise_for_status()
                    st.download_button(
                        label="⬇️ Click to Download PDF",
                        data=pdf_res.content,
                        file_name="import_ai_report.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"PDF export failed: {e}")

        st.markdown("</div>", unsafe_allow_html=True)