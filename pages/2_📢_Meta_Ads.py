"""Meta Ads Intelligence page."""

import json, os, sys, subprocess
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
from pathlib import Path
from _styles import apply_styles, page_header, label

st.set_page_config(page_title="Meta Ads", page_icon="📢", layout="wide", initial_sidebar_state="expanded")
apply_styles()
page_header("📢", "Meta Ads Intelligence", "Competitor ads from the Meta Ads Library")

REPORT_PATH = Path(os.path.dirname(os.path.dirname(__file__))) / "report.json"
VENV_PYTHON = "/Users/magi/dashboard/venv/bin/python3"
AGENT_PATH  = Path(os.path.dirname(os.path.dirname(__file__))) / "agent_scraper.py"

# ── Run agent button ────────────────────────────────────────────────────────

col_btn, col_status = st.columns([2, 5])
with col_btn:
    run = st.button("▶ Run Scraper")
with col_status:
    if run:
        with st.spinner("Scraping Meta Ads Library…"):
            result = subprocess.run(
                [VENV_PYTHON, str(AGENT_PATH)],
                cwd=str(AGENT_PATH.parent),
                capture_output=True, text=True, timeout=600,
            )
        if result.returncode == 0:
            st.success("Report updated.")
            st.cache_data.clear()
        else:
            st.error(f"Scraper failed:\n{result.stderr[-500:]}")

st.markdown("<br>", unsafe_allow_html=True)

# ── Report viewer ────────────────────────────────────────────────────────────

if not REPORT_PATH.exists():
    st.markdown("""
    <div style='text-align:center;color:#2a2a2a;padding:80px 0;'>
        <div style='font-size:2rem;margin-bottom:12px;'>📢</div>
        <div>No report yet. Click <b>▶ Run Scraper</b> to fetch ads.</div>
    </div>""", unsafe_allow_html=True)
else:
    data = json.loads(REPORT_PATH.read_text())
    st.markdown(f"<p style='font-size:0.75rem;color:#444;'>Last run: {data.get('generated_at','')[:19].replace('T',' ')} UTC</p>", unsafe_allow_html=True)

    brands = list(data.get("brands", {}).keys())
    if not brands:
        st.info("No brands in report.")
    else:
        selected = st.selectbox("Brand", brands, label_visibility="collapsed")
        brand_data = data["brands"][selected]
        ads = brand_data.get("ads", [])
        # API format: active if no stop time; scraper format: status field
        def is_active(ad):
            if "status" in ad:
                return ad["status"] == "Active"
            return not ad.get("ad_delivery_stop_time")
        active = [a for a in ads if is_active(a)]

        m1, m2, m3 = st.columns(3)
        m1.metric("Total Ads", brand_data.get("total_ads", len(ads)))
        m2.metric("Active", len(active))
        m3.metric("Inactive", len(ads) - len(active))

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<p style='font-size:0.8rem;font-weight:500;color:#666;letter-spacing:0.05em;text-transform:uppercase;'>Ads</p>", unsafe_allow_html=True)

        for i, ad in enumerate(ads[:20], 1):
            active_ad = is_active(ad)
            status_color = "#22c55e" if active_ad else "#555"
            status_label = "Active" if active_ad else "Inactive"
            start = ad.get("start_date") or ad.get("ad_delivery_start_time", "—")[:10]
            advertiser = ad.get("advertiser") or ad.get("page_name", selected)
            bodies = ad.get("ad_creative_bodies") or []
            body = ad.get("body") or (bodies[0] if bodies else "")
            platforms = ad.get("platforms") or ad.get("publisher_platforms") or []
            snapshot = ad.get("snapshot_url") or ad.get("ad_snapshot_url", "")
            with st.expander(f"#{i}  ·  {start}  ·  {advertiser}"):
                st.markdown(f"<span style='color:{status_color};font-size:0.8rem;font-weight:500;'>● {status_label}</span>", unsafe_allow_html=True)
                if body:
                    st.markdown(f"<p style='color:#ccc;font-size:0.9rem;line-height:1.6;margin-top:8px;'>{body}</p>", unsafe_allow_html=True)
                if platforms:
                    st.caption("Platforms: " + ", ".join(platforms))
                if snapshot:
                    st.markdown(f"[View on Facebook →]({snapshot})")
