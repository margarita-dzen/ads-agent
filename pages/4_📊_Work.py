"""Work Dashboard page — Tasks, Email, Calendar."""

import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv
from _styles import apply_styles, page_header

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

st.set_page_config(page_title="Work Dashboard", page_icon="📊", layout="wide", initial_sidebar_state="expanded")
apply_styles()
page_header("📊", "Work Dashboard", datetime.now().strftime("%A, %B %d · %I:%M %p"))

# ── Auth helpers ──────────────────────────────────────────────────────────────

def get_google_config() -> Optional[Tuple[str, str, str]]:
    try:
        g = st.secrets["google"]
        return g["refresh_token"], g["client_id"], g["client_secret"]
    except Exception:
        pass
    try:
        token_path = Path.home() / ".dashboard" / "token.json"
        data = json.loads(token_path.read_text())
        return data["refresh_token"], data["client_id"], data["client_secret"]
    except Exception:
        return None

def get_notion_config():
    try:
        n = st.secrets["notion"]
        return n["token"], n["database_id"]
    except Exception:
        return os.getenv("NOTION_TOKEN"), os.getenv("NOTION_DATABASE_ID")

# ── Data fetchers ─────────────────────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def fetch_tasks(token, db_id):
    import requests
    r = requests.post(
        f"https://api.notion.com/v1/databases/{db_id}/query",
        headers={"Authorization": f"Bearer {token}", "Notion-Version": "2022-06-28", "Content-Type": "application/json"},
        json={"page_size": 25}, timeout=10,
    )
    r.raise_for_status()
    return r.json().get("results", [])

def _make_creds(refresh_token, client_id, client_secret, scopes):
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    creds = Credentials(token=None, refresh_token=refresh_token, token_uri="https://oauth2.googleapis.com/token",
                        client_id=client_id, client_secret=client_secret, scopes=scopes)
    creds.refresh(Request())
    return creds

@st.cache_data(ttl=300, show_spinner=False)
def fetch_calendar(rt, ci, cs):
    from googleapiclient.discovery import build
    creds = _make_creds(rt, ci, cs, ["https://www.googleapis.com/auth/calendar.readonly"])
    service = build("calendar", "v3", credentials=creds)
    now = datetime.now(timezone.utc).isoformat()
    result = service.events().list(calendarId="primary", timeMin=now, maxResults=12, singleEvents=True, orderBy="startTime").execute()
    return result.get("items", [])

@st.cache_data(ttl=300, show_spinner=False)
def fetch_emails(rt, ci, cs):
    from googleapiclient.discovery import build
    creds = _make_creds(rt, ci, cs, ["https://www.googleapis.com/auth/gmail.readonly"])
    service = build("gmail", "v1", credentials=creds)
    result = service.users().messages().list(userId="me", q="is:unread", maxResults=10).execute()
    messages = []
    for msg in result.get("messages", []):
        detail = service.users().messages().get(userId="me", id=msg["id"], format="metadata", metadataHeaders=["From", "Subject"]).execute()
        messages.append(detail)
    return messages

# ── Helpers ───────────────────────────────────────────────────────────────────

STATUS_EMOJI  = {"done": "✅", "in progress": "🔄", "in review": "👀", "blocked": "🚫", "todo": "⬜", "not started": "⬜"}
PRIORITY_EMOJI = {"urgent": "🚨", "high": "🔴", "medium": "🟡", "low": "🟢"}

def _prop_text(props, key):
    prop = props.get(key, {})
    t = prop.get("type", "")
    if t == "status": return (prop.get("status") or {}).get("name", "")
    if t == "select": return (prop.get("select") or {}).get("name", "")
    return ""

def _task_name(props):
    for key in ("Name", "Title", "Task", "Todo"):
        parts = props.get(key, {}).get("title", [])
        if parts: return "".join(t.get("plain_text", "") for t in parts)
    return "Untitled"

# ── Refresh ───────────────────────────────────────────────────────────────────

_, refresh_col = st.columns([8, 1])
with refresh_col:
    if st.button("⟳ Refresh"):
        st.cache_data.clear()
        st.rerun()

google_cfg    = get_google_config()
notion_token, notion_db = get_notion_config()

left, right = st.columns(2)

# ── Tasks ─────────────────────────────────────────────────────────────────────
with left:
    st.markdown("### 📋 Tasks")
    if notion_token and notion_db:
        try:
            with st.spinner(""):
                tasks = fetch_tasks(notion_token, notion_db)
            if not tasks:
                st.info("No tasks found.")
            else:
                for task in tasks:
                    props  = task.get("properties", {})
                    name   = _task_name(props)
                    status = _prop_text(props, "Status")
                    priority = _prop_text(props, "Priority")
                    s_icon = STATUS_EMOJI.get(status.lower(), "⬜")
                    p_icon = PRIORITY_EMOJI.get(priority.lower(), "")
                    st.markdown(
                        f"<div style='padding:8px 0;border-bottom:1px solid #1a1a1a;color:#ccc;font-size:0.9rem;'>"
                        f"{s_icon} <b style='color:#e0e0e0;'>{name}</b> {p_icon}</div>",
                        unsafe_allow_html=True,
                    )
        except Exception as e:
            st.error(f"Notion: {e}")
    else:
        st.warning("Notion not configured.")

# ── Email ─────────────────────────────────────────────────────────────────────
with left:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📧 Unread Email")
    if google_cfg:
        rt, ci, cs = google_cfg
        try:
            with st.spinner(""):
                emails = fetch_emails(rt, ci, cs)
            if not emails:
                st.success("Inbox zero! 🎉")
            else:
                for email in emails:
                    hdrs    = {h["name"]: h["value"] for h in email.get("payload", {}).get("headers", [])}
                    subject = hdrs.get("Subject", "(No subject)")
                    sender  = hdrs.get("From", "Unknown")
                    if "<" in sender: sender = sender.split("<")[0].strip().strip('"')
                    st.markdown(
                        f"<div style='padding:8px 0;border-bottom:1px solid #1a1a1a;'>"
                        f"<span style='font-weight:600;color:#e0e0e0;font-size:0.9rem;'>{sender[:35]}</span><br>"
                        f"<span style='color:#555;font-size:0.83rem;'>{subject[:65]}</span></div>",
                        unsafe_allow_html=True,
                    )
        except Exception as e:
            st.error(f"Gmail: {e}")
    else:
        st.warning("Google not configured.")

# ── Calendar ──────────────────────────────────────────────────────────────────
with right:
    st.markdown("### 📅 Calendar")
    if google_cfg:
        rt, ci, cs = google_cfg
        try:
            with st.spinner(""):
                events = fetch_calendar(rt, ci, cs)
            today = datetime.now().date()
            if not events:
                st.info("No upcoming events.")
            else:
                for event in events:
                    summary = event.get("summary", "(No title)")
                    start   = event.get("start", {})
                    if "dateTime" in start:
                        dt       = datetime.fromisoformat(start["dateTime"].replace("Z", "+00:00")).astimezone()
                        is_today = dt.date() == today
                        label_t  = "Today" if is_today else dt.strftime("%a %b %d")
                        time_str = dt.strftime("%-I:%M %p")
                    elif "date" in start:
                        dt       = datetime.strptime(start["date"], "%Y-%m-%d")
                        is_today = dt.date() == today
                        label_t  = "Today" if is_today else dt.strftime("%a %b %d")
                        time_str = "All day"
                    else:
                        continue
                    name_color = "#f0f0f0" if is_today else "#aaa"
                    marker     = "▶ " if is_today else "   "
                    st.markdown(
                        f"<div style='padding:8px 0;border-bottom:1px solid #1a1a1a;'>"
                        f"<span style='color:{name_color};font-size:0.88rem;'>{marker}<b>{label_t}</b>"
                        f" <span style='color:#555;font-weight:400;'>· {time_str}</span></span><br>"
                        f"<span style='color:#666;font-size:0.85rem;margin-left:14px;'>{summary}</span></div>",
                        unsafe_allow_html=True,
                    )
        except Exception as e:
            st.error(f"Calendar: {e}")
    else:
        st.warning("Google not configured.")
