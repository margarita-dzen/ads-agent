"""Instagram Reels Intelligence page."""

import json, os, sys, subprocess
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
from pathlib import Path
from _styles import apply_styles, page_header

st.set_page_config(page_title="Instagram Reels", page_icon="🎬", layout="wide", initial_sidebar_state="expanded")
apply_styles()
page_header("🎬", "Instagram Reels", "Competitor reel performance scored by engagement & views")

REPORT_PATH = Path(os.path.dirname(os.path.dirname(__file__))) / "instagram_report.json"
VENV_PYTHON = "/Users/magi/dashboard/venv/bin/python3"
AGENT_PATH  = Path(os.path.dirname(os.path.dirname(__file__))) / "instagram_agent.py"

# ── Run agent button ─────────────────────────────────────────────────────────

col_btn, col_status = st.columns([2, 5])
with col_btn:
    run = st.button("▶ Run Instagram Agent")
with col_status:
    if run:
        with st.spinner("Scraping Instagram reels… (this may take a few minutes)"):
            result = subprocess.run(
                [VENV_PYTHON, str(AGENT_PATH)],
                cwd=str(AGENT_PATH.parent),
                capture_output=True, text=True, timeout=600,
            )
        if result.returncode == 0:
            st.success("Report updated.")
            st.cache_data.clear()
        else:
            st.error(f"Agent failed:\n{result.stderr[-500:]}")

st.markdown("<br>", unsafe_allow_html=True)

# ── Report viewer ─────────────────────────────────────────────────────────────

if not REPORT_PATH.exists():
    st.markdown("""
    <div style='text-align:center;color:#2a2a2a;padding:80px 0;'>
        <div style='font-size:2rem;margin-bottom:12px;'>🎬</div>
        <div>No report yet. Click <b>▶ Run Instagram Agent</b> to fetch reels.</div>
    </div>""", unsafe_allow_html=True)
else:
    data = json.loads(REPORT_PATH.read_text())
    st.markdown(f"<p style='font-size:0.75rem;color:#444;'>Last run: {data.get('generated_at','')[:19].replace('T',' ')} UTC</p>", unsafe_allow_html=True)

    handles = list(data.get("brands", {}).keys())
    if not handles:
        st.info("No accounts in report.")
    else:
        selected = st.selectbox("Account", [f"@{h}" for h in handles], label_visibility="collapsed")
        handle = selected.lstrip("@")
        brand = data["brands"][handle]
        reels = brand.get("top_reels", [])

        m1, m2, m3 = st.columns(3)
        m1.metric("Followers", f"{brand.get('followers', 0):,}")
        m2.metric("Reels Scraped", brand.get("total_reels_scraped", 0))
        m3.metric("Top Score", reels[0]["score"] if reels else "—")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<p style='font-size:0.8rem;font-weight:500;color:#666;letter-spacing:0.05em;text-transform:uppercase;'>Top Reels by Score</p>", unsafe_allow_html=True)

        for i, reel in enumerate(reels, 1):
            with st.expander(
                f"#{i}  ·  👁 {reel.get('views',0):,}  ·  ❤️ {reel.get('likes',0):,}  ·  💬 {reel.get('comments',0):,}  ·  Score {reel.get('score','—')}"
            ):
                caption = reel.get("caption", "")
                if caption:
                    st.markdown(f"<p style='color:#ccc;font-size:0.9rem;line-height:1.6;'>{caption[:400]}</p>", unsafe_allow_html=True)
                cols = st.columns(3)
                cols[0].caption(f"📅 {reel.get('date','')[:10]}")
                if reel.get("hashtags"):
                    cols[1].caption(" ".join(f"#{h}" for h in reel["hashtags"][:5]))
                if reel.get("url"):
                    st.markdown(f"[Watch Reel →]({reel['url']})")
