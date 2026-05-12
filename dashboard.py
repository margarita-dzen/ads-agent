"""Ad Copy Agent — Web Dashboard"""

import base64
import os
import sys
import time
import random
from pathlib import Path

import anthropic
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ── Page config ────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Ad Copy Agent",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Styles ─────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Hide Streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stDecoration"] { display: none; }
.block-container { padding: 2.5rem 3rem 2rem 3rem; max-width: 1200px; }

/* Background */
.stApp { background-color: #0d0d0d; }

/* Typography */
h1 { font-size: 1.5rem !important; font-weight: 500 !important; letter-spacing: -0.02em !important; color: #f0f0f0 !important; }
p, label, div { color: #a0a0a0; }

/* Upload zone */
[data-testid="stFileUploader"] {
    background: #161616;
    border: 1px dashed #2a2a2a;
    border-radius: 12px;
    padding: 1rem;
    transition: border-color 0.2s;
}
[data-testid="stFileUploader"]:hover { border-color: #444; }
[data-testid="stFileUploadDropzone"] { background: transparent !important; }

/* Radio buttons → pill selectors */
[data-testid="stRadio"] > div {
    display: flex;
    gap: 8px;
    flex-direction: row !important;
}
[data-testid="stRadio"] label {
    background: #1a1a1a;
    border: 1px solid #2a2a2a;
    border-radius: 20px;
    padding: 6px 18px !important;
    cursor: pointer;
    font-size: 0.85rem !important;
    color: #888 !important;
    transition: all 0.15s;
}
[data-testid="stRadio"] label:hover { border-color: #555; color: #ccc !important; }
[data-testid="stRadio"] input:checked + div p { color: #f0f0f0 !important; }
[data-testid="stRadio"] label:has(input:checked) {
    background: #1f1f1f;
    border-color: #555;
    color: #f0f0f0 !important;
}

/* Select box */
[data-testid="stSelectbox"] > div > div {
    background: #161616 !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 8px !important;
    color: #ccc !important;
}

/* Text input & area */
[data-testid="stTextArea"] textarea,
[data-testid="stTextInput"] input {
    background: #161616 !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 8px !important;
    color: #ccc !important;
    font-size: 0.9rem !important;
}

/* Generate button */
[data-testid="stButton"] > button {
    background: #f0f0f0;
    color: #0d0d0d;
    border: none;
    border-radius: 8px;
    font-weight: 500;
    font-size: 0.9rem;
    padding: 0.6rem 1.5rem;
    width: 100%;
    transition: background 0.15s;
}
[data-testid="stButton"] > button:hover { background: #d8d8d8; }

/* Result cards */
.result-card {
    background: #161616;
    border: 1px solid #222;
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 12px;
}
.card-label {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #555;
    margin-bottom: 8px;
}
.card-content {
    color: #e0e0e0;
    font-size: 0.95rem;
    line-height: 1.65;
}
.headline-item {
    padding: 10px 0;
    border-bottom: 1px solid #1e1e1e;
    color: #e8e8e8;
    font-size: 1rem;
    font-weight: 500;
    line-height: 1.4;
}
.headline-item:last-child { border-bottom: none; }
.headline-num {
    color: #444;
    font-size: 0.8rem;
    margin-right: 8px;
}
.cta-badge {
    display: inline-block;
    background: #1e1e1e;
    border: 1px solid #333;
    border-radius: 6px;
    padding: 8px 16px;
    color: #e0e0e0;
    font-weight: 500;
    font-size: 0.9rem;
}
.divider { border: none; border-top: 1px solid #1e1e1e; margin: 8px 0; }

/* Spinner */
[data-testid="stSpinner"] { color: #555 !important; }

/* Image preview */
.image-preview img {
    border-radius: 10px;
    width: 100%;
    object-fit: cover;
}
</style>
""", unsafe_allow_html=True)

# ── Constants ──────────────────────────────────────────────────────────────────

SUPPORTED_FORMATS = {
    "jpg": "image/jpeg", "jpeg": "image/jpeg",
    "png": "image/png", "gif": "image/gif", "webp": "image/webp",
}

PLATFORMS = [
    "Instagram / Facebook",
    "TikTok",
    "Google Display",
    "YouTube",
    "LinkedIn",
    "Pinterest",
    "Twitter / X",
]

COPY_LENGTH_INSTRUCTIONS = {
    "Short": (
        "Primary Text: 1–2 sentences only. "
        "Ultra-concise — hook immediately, every word earns its place."
    ),
    "Medium": (
        "Primary Text: 3–4 sentences. "
        "Hook + context + payoff. Balanced for standard feed placements."
    ),
    "Long": (
        "Primary Text: 6–10 sentences. "
        "Story arc: strong hook, build desire, present the product as the solution, "
        "close with urgency or social proof. Write for cold audiences."
    ),
}

SYSTEM_PROMPT = """You are an expert direct-response advertising copywriter with 15+ years of experience across Meta, Google, TikTok, and display advertising.

When given an ad image, you:
1. Analyze the visual: product, mood, colors, people, setting, and overall aesthetic
2. Identify the ad angle (e.g. problem/solution, transformation, lifestyle, curiosity hook, social proof, urgency, aspiration)
3. Write copy that amplifies what the image communicates — the words and visual should feel like one unified message

Respond in this EXACT format with these exact section headers:

AD ANGLE
[one sentence naming the angle and why it fits this visual]

HEADLINES
1. [headline]
2. [headline]
3. [headline]

PRIMARY TEXT
[the copy]

CTA
[call-to-action button text only]

Rules:
- No generic copy. Every line must feel specific to THIS image.
- Headlines under 10 words each, strong enough to stop a scroll.
- If a product, brand, or offer is visible, incorporate it directly.
- Match tone to the visual energy."""


# ── Core logic ─────────────────────────────────────────────────────────────────

def generate_copy(image_bytes: bytes, media_type: str, platform: str, length: str, context: str) -> str:
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
    length_instruction = COPY_LENGTH_INSTRUCTIONS[length]

    user_content = [
        {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": image_b64}},
        {"type": "text", "text": (
            f"Write ad copy for this image.\n"
            f"Target platform: {platform}.\n"
            f"Length instruction: {length_instruction}"
            + (f"\n\nExtra context: {context}" if context.strip() else "")
        )},
    ]

    max_retries = 5
    for attempt in range(max_retries):
        try:
            response = client.messages.create(
                model="claude-opus-4-6",
                max_tokens=2048,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_content}],
            )
            return response.content[0].text
        except anthropic.APIStatusError as e:
            if e.status_code in (529, 500) and attempt < max_retries - 1:
                wait = min(2 ** attempt + random.uniform(0, 1), 30)
                time.sleep(wait)
            else:
                raise


def parse_result(text: str) -> dict:
    """Parse Claude's structured response into sections."""
    sections = {"angle": "", "headlines": [], "primary": "", "cta": ""}
    current = None
    lines = text.strip().splitlines()

    for line in lines:
        stripped = line.strip()
        if stripped == "AD ANGLE":
            current = "angle"
        elif stripped == "HEADLINES":
            current = "headlines"
        elif stripped == "PRIMARY TEXT":
            current = "primary"
        elif stripped == "CTA":
            current = "cta"
        elif stripped and current:
            if current == "angle" and not sections["angle"]:
                sections["angle"] = stripped
            elif current == "headlines":
                clean = stripped.lstrip("123456789.-) ").strip()
                if clean:
                    sections["headlines"].append(clean)
            elif current == "primary":
                sections["primary"] += (" " if sections["primary"] else "") + stripped
            elif current == "cta" and not sections["cta"]:
                sections["cta"] = stripped

    return sections


# ── UI ─────────────────────────────────────────────────────────────────────────

# Header
col_title, col_spacer = st.columns([3, 1])
with col_title:
    st.markdown("## ✦ Ad Copy Agent")
    st.markdown("<p style='margin-top:-12px;font-size:0.85rem;color:#444;'>Upload an ad image · get headlines & copy instantly</p>", unsafe_allow_html=True)

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# Check API key
if not os.getenv("ANTHROPIC_API_KEY"):
    st.error("ANTHROPIC_API_KEY not found. Add it to your .env file.")
    st.stop()

# Two-column layout
left_col, gap, right_col = st.columns([5, 1, 6])

with left_col:
    # Image upload
    st.markdown("<p style='font-size:0.8rem;font-weight:500;color:#666;letter-spacing:0.05em;text-transform:uppercase;margin-bottom:8px;'>Ad Image</p>", unsafe_allow_html=True)
    uploaded = st.file_uploader(
        "Drop an image here or click to browse",
        type=list(SUPPORTED_FORMATS.keys()),
        label_visibility="collapsed",
    )

    if uploaded:
        st.markdown("<br>", unsafe_allow_html=True)
        st.image(uploaded, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Platform
    st.markdown("<p style='font-size:0.8rem;font-weight:500;color:#666;letter-spacing:0.05em;text-transform:uppercase;margin-bottom:4px;'>Platform</p>", unsafe_allow_html=True)
    platform = st.selectbox("Platform", PLATFORMS, label_visibility="collapsed")

    st.markdown("<br>", unsafe_allow_html=True)

    # Copy length
    st.markdown("<p style='font-size:0.8rem;font-weight:500;color:#666;letter-spacing:0.05em;text-transform:uppercase;margin-bottom:4px;'>Copy Length</p>", unsafe_allow_html=True)
    length = st.radio("Length", ["Short", "Medium", "Long"], horizontal=True, label_visibility="collapsed")

    st.markdown("<br>", unsafe_allow_html=True)

    # Context
    st.markdown("<p style='font-size:0.8rem;font-weight:500;color:#666;letter-spacing:0.05em;text-transform:uppercase;margin-bottom:4px;'>Extra Context <span style='font-weight:300;text-transform:none;letter-spacing:0;'>(optional)</span></p>", unsafe_allow_html=True)
    context = st.text_area(
        "Context",
        placeholder="e.g. Luxury skincare brand, targeting women 35–55, 20% off launch offer",
        height=80,
        label_visibility="collapsed",
    )

    st.markdown("<br>", unsafe_allow_html=True)

    generate_btn = st.button("Generate Copy →", disabled=uploaded is None)


with right_col:
    if "result" not in st.session_state:
        st.session_state.result = None
    if "error" not in st.session_state:
        st.session_state.error = None

    if generate_btn and uploaded:
        st.session_state.result = None
        st.session_state.error = None
        ext = uploaded.name.rsplit(".", 1)[-1].lower()
        media_type = SUPPORTED_FORMATS.get(ext, "image/jpeg")
        image_bytes = uploaded.read()

        with st.spinner("Analyzing image…"):
            try:
                raw = generate_copy(image_bytes, media_type, platform, length, context)
                st.session_state.result = parse_result(raw)
            except Exception as e:
                st.session_state.error = str(e)

    if st.session_state.error:
        st.error(f"Error: {st.session_state.error}")

    elif st.session_state.result:
        r = st.session_state.result

        # Ad Angle
        if r["angle"]:
            st.markdown(f"""
            <div class='result-card'>
                <div class='card-label'>Ad Angle</div>
                <div class='card-content'>{r['angle']}</div>
            </div>""", unsafe_allow_html=True)

        # Headlines
        if r["headlines"]:
            headlines_html = "".join(
                f"<div class='headline-item'><span class='headline-num'>{i+1}</span>{h}</div>"
                for i, h in enumerate(r["headlines"])
            )
            st.markdown(f"""
            <div class='result-card'>
                <div class='card-label'>Headlines</div>
                {headlines_html}
            </div>""", unsafe_allow_html=True)

        # Primary Text
        if r["primary"]:
            st.markdown(f"""
            <div class='result-card'>
                <div class='card-label'>Primary Text</div>
                <div class='card-content'>{r['primary']}</div>
            </div>""", unsafe_allow_html=True)

        # CTA
        if r["cta"]:
            st.markdown(f"""
            <div class='result-card'>
                <div class='card-label'>CTA</div>
                <span class='cta-badge'>{r['cta']}</span>
            </div>""", unsafe_allow_html=True)

    else:
        # Empty state
        st.markdown("""
        <div style='height:300px;display:flex;flex-direction:column;align-items:center;justify-content:center;color:#2a2a2a;'>
            <div style='font-size:2.5rem;margin-bottom:12px;'>✦</div>
            <div style='font-size:0.9rem;'>Upload an image to get started</div>
        </div>
        """, unsafe_allow_html=True)
