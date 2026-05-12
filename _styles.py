"""Shared styles — matching drfit-roadmap.vercel.app design system."""

import streamlit as st

ANCHOR_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@300;400;500;600&family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&display=swap');

:root {
    --bg: #0a0a12;
    --bg-card: rgba(255,255,255,0.03);
    --bg-card-solid: #12121e;
    --blue: #2563EB;
    --blue-bright: #3B82F6;
    --green: #10B981;
    --red: #EF4444;
    --w95: rgba(255,255,255,0.95);
    --w55: rgba(255,255,255,0.55);
    --w40: rgba(255,255,255,0.4);
    --w35: rgba(255,255,255,0.35);
    --w25: rgba(255,255,255,0.25);
    --w15: rgba(255,255,255,0.15);
    --w06: rgba(255,255,255,0.06);
    --glass-border: rgba(255,255,255,0.06);
    --blue-glow: rgba(37,99,235,0.25);
    --glass-border-hover: rgba(37,99,235,0.35);
}

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
    -webkit-font-smoothing: antialiased;
}

#MainMenu, footer, header { visibility: hidden; }
[data-testid="stDecoration"] { display: none; }
[data-testid="stSidebar"] { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }

.block-container {
    padding: 60px 24px 120px;
    max-width: 960px;
}

.stApp {
    background-color: var(--bg);
}

/* Mesh gradient blobs */
.stApp::before, .stApp::after {
    content: '';
    position: fixed;
    border-radius: 50%;
    filter: blur(120px);
    opacity: 0.35;
    pointer-events: none;
    z-index: 0;
}
.stApp::before {
    width: 600px; height: 600px;
    background: radial-gradient(circle, rgba(37,99,235,0.18), transparent 70%);
    top: -200px; right: -100px;
    animation: meshFloat1 22s ease-in-out infinite;
}
.stApp::after {
    width: 500px; height: 500px;
    background: radial-gradient(circle, rgba(16,185,129,0.1), transparent 70%);
    bottom: -150px; left: -100px;
    animation: meshFloat2 28s ease-in-out infinite;
}

@keyframes meshFloat1 {
    0%, 100% { transform: translate(0, 0); }
    50% { transform: translate(-40px, 60px); }
}
@keyframes meshFloat2 {
    0%, 100% { transform: translate(0, 0); }
    50% { transform: translate(50px, -40px); }
}

/* Typography */
h1 {
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 48px !important;
    font-weight: 700 !important;
    color: var(--w95) !important;
    line-height: 1.1 !important;
    letter-spacing: -0.02em !important;
}
h2 {
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 24px !important;
    font-weight: 600 !important;
    color: var(--w95) !important;
}
h3 {
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 20px !important;
    font-weight: 600 !important;
    color: var(--w95) !important;
}
p, label, div, span { color: var(--w55); }

/* Buttons */
[data-testid="stButton"] > button {
    background: var(--blue) !important;
    color: var(--w95) !important;
    border: 1px solid rgba(37,99,235,0.4) !important;
    border-radius: 12px !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 600 !important;
    font-size: 15px !important;
    padding: 0.6rem 1.6rem !important;
    transition: all 0.35s cubic-bezier(0.16,1,0.3,1) !important;
    letter-spacing: 0.01em;
}
[data-testid="stButton"] > button:hover {
    background: var(--blue-bright) !important;
    border-color: var(--glass-border-hover) !important;
    box-shadow: 0 8px 32px var(--blue-glow) !important;
    transform: translateY(-2px);
}
[data-testid="stButton"] > button:disabled {
    background: var(--w06) !important;
    color: var(--w25) !important;
    border-color: var(--glass-border) !important;
    box-shadow: none !important;
    transform: none !important;
}

/* Inputs */
[data-testid="stTextArea"] textarea,
[data-testid="stTextInput"] input {
    background: var(--bg-card-solid) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: 12px !important;
    color: var(--w55) !important;
    font-size: 14px !important;
    font-family: 'Inter', sans-serif !important;
    transition: border-color 0.35s cubic-bezier(0.16,1,0.3,1);
}
[data-testid="stTextArea"] textarea:focus,
[data-testid="stTextInput"] input:focus {
    border-color: var(--glass-border-hover) !important;
    box-shadow: 0 0 0 3px rgba(37,99,235,0.08) !important;
}

/* Selectbox */
[data-testid="stSelectbox"] > div > div {
    background: var(--bg-card-solid) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: 12px !important;
    color: var(--w55) !important;
}

/* Radio pills */
[data-testid="stRadio"] > div { display: flex; gap: 8px; flex-direction: row !important; }
[data-testid="stRadio"] label {
    background: var(--bg-card) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: 100px !important;
    padding: 6px 18px !important;
    cursor: pointer;
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    color: var(--w55) !important;
    transition: all 0.35s cubic-bezier(0.16,1,0.3,1);
    letter-spacing: 0.04em;
}
[data-testid="stRadio"] label:hover {
    border-color: var(--glass-border-hover) !important;
    color: var(--w95) !important;
    background: rgba(37,99,235,0.06) !important;
}
[data-testid="stRadio"] label:has(input:checked) {
    background: rgba(37,99,235,0.12) !important;
    border-color: rgba(37,99,235,0.3) !important;
    color: var(--blue-bright) !important;
}

/* File uploader */
[data-testid="stFileUploader"] {
    background: var(--bg-card);
    border: 1px dashed var(--w15);
    border-radius: 20px;
    padding: 1.2rem;
    transition: all 0.35s cubic-bezier(0.16,1,0.3,1);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
}
[data-testid="stFileUploader"]:hover {
    border-color: var(--glass-border-hover);
    background: rgba(37,99,235,0.03);
}
[data-testid="stFileUploadDropzone"] { background: transparent !important; }

/* Expander */
[data-testid="stExpander"] {
    background: var(--bg-card-solid) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: 16px !important;
}
[data-testid="stExpanderToggleIcon"] { color: var(--w25) !important; }

/* Tabs */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid var(--glass-border) !important;
    gap: 4px;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    background: transparent !important;
    color: var(--w35) !important;
    border-radius: 8px 8px 0 0 !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 8px 16px !important;
    transition: color 0.2s ease;
}
[data-testid="stTabs"] [data-baseweb="tab"]:hover {
    color: var(--w55) !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
    color: var(--blue-bright) !important;
    border-bottom: 2px solid var(--blue-bright) !important;
}

/* Status widget */
[data-testid="stStatusWidget"] {
    background: var(--bg-card-solid) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: 16px !important;
}

/* Alerts */
[data-testid="stAlert"] { border-radius: 16px !important; font-size: 14px !important; }

/* Spinner */
[data-testid="stSpinner"] { color: var(--blue-bright) !important; }

/* Divider */
hr { border-color: var(--glass-border) !important; }

/* Columns gap */
[data-testid="stHorizontalBlock"] { gap: 24px; }

/* ── Custom components ─────────────────────────────────────────────────── */

.label {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: rgba(59,130,246,0.6);
}

.gradient-text {
    background: linear-gradient(135deg, #2563EB 0%, #3B82F6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.serif-italic {
    font-family: 'Libre Baskerville', serif;
    font-style: italic;
}

.tag {
    display: inline-block;
    font-family: 'Space Grotesk', sans-serif;
    font-size: 12px;
    font-weight: 500;
    padding: 4px 12px;
    border-radius: 100px;
    letter-spacing: 0.04em;
}
.tag-blue {
    background: rgba(37,99,235,0.12);
    color: #3B82F6;
    border: 1px solid rgba(37,99,235,0.2);
}
.tag-green {
    background: rgba(16,185,129,0.12);
    color: #10B981;
    border: 1px solid rgba(16,185,129,0.2);
}
.tag-white {
    background: rgba(255,255,255,0.06);
    color: rgba(255,255,255,0.55);
    border: 1px solid rgba(255,255,255,0.1);
}

/* Glass card */
.card {
    background: var(--bg-card);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid var(--glass-border);
    border-radius: 20px;
    padding: 24px;
    transition: transform 0.35s cubic-bezier(0.16,1,0.3,1), border-color 0.35s;
}
.card:hover {
    transform: translateY(-4px);
    border-color: var(--glass-border-hover);
}
.card-lg { padding: 32px; }
.card-no-hover:hover { transform: none; }

/* Solid card */
.card-solid {
    background: var(--bg-card-solid);
    border: 1px solid var(--glass-border);
    border-radius: 16px;
    padding: 24px;
    transition: transform 0.35s cubic-bezier(0.16,1,0.3,1), border-color 0.35s;
}
.card-solid:hover {
    transform: translateY(-2px);
    border-color: rgba(255,255,255,0.1);
}

/* Result cards */
.result-card {
    background: var(--bg-card);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid var(--glass-border);
    border-radius: 20px;
    padding: 24px 28px;
    margin-bottom: 16px;
    transition: transform 0.35s cubic-bezier(0.16,1,0.3,1), border-color 0.35s;
    position: relative;
    overflow: hidden;
}
.result-card:hover {
    transform: translateY(-2px);
    border-color: var(--glass-border-hover);
}
.result-card .accent-bar {
    position: absolute;
    top: 0; left: 0;
    width: 4px;
    height: 100%;
    border-radius: 4px 0 0 4px;
    background: linear-gradient(180deg, #2563EB, #3B82F6);
}

.card-label {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: rgba(59,130,246,0.6);
    margin-bottom: 10px;
}
.card-content {
    color: rgba(255,255,255,0.95);
    font-size: 15px;
    line-height: 1.6;
}
.headline-item {
    padding: 12px 0;
    border-bottom: 1px solid var(--glass-border);
    color: rgba(255,255,255,0.95);
    font-family: 'Space Grotesk', sans-serif;
    font-size: 16px;
    font-weight: 600;
    line-height: 1.4;
}
.headline-item:last-child { border-bottom: none; }
.headline-num {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 22px;
    height: 22px;
    border-radius: 50%;
    background: rgba(37,99,235,0.12);
    border: 1px solid rgba(37,99,235,0.2);
    color: #3B82F6;
    font-size: 11px;
    font-weight: 700;
    margin-right: 12px;
    flex-shrink: 0;
}
.cta-badge {
    display: inline-block;
    background: rgba(37,99,235,0.12);
    border: 1px solid rgba(37,99,235,0.3);
    border-radius: 100px;
    padding: 10px 24px;
    color: #3B82F6;
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 600;
    font-size: 15px;
    letter-spacing: 0.02em;
    transition: all 0.35s cubic-bezier(0.16,1,0.3,1);
}
.cta-badge:hover {
    background: rgba(37,99,235,0.2);
    border-color: rgba(37,99,235,0.5);
    transform: translateY(-2px);
}

.page-label {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: rgba(59,130,246,0.6);
    margin-bottom: 6px;
}

/* Fade-up animation for results */
@keyframes fadeUp {
    from { opacity: 0; transform: translateY(32px); }
    to   { opacity: 1; transform: translateY(0); }
}
.fade-up {
    animation: fadeUp 0.9s cubic-bezier(0.16, 1, 0.3, 1) both;
}
.delay-1 { animation-delay: 0.1s; }
.delay-2 { animation-delay: 0.2s; }
.delay-3 { animation-delay: 0.3s; }
.delay-4 { animation-delay: 0.4s; }

/* Pulsing dot */
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
}
.timeline-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #3B82F6;
    animation: pulse 2s ease-in-out infinite;
    display: inline-block;
}
</style>
"""


def apply_styles():
    st.markdown(ANCHOR_CSS, unsafe_allow_html=True)


def page_header(icon: str, title: str, subtitle: str = ""):
    pass  # Headers are now custom HTML in each page


def label(text: str):
    st.markdown(f"<p class='page-label'>{text}</p>", unsafe_allow_html=True)
