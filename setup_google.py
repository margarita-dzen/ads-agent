"""
Google OAuth Setup
Run this once to connect Gmail and Google Calendar to your Work Dashboard.
"""

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv, set_key

load_dotenv()

ENV_PATH   = Path(__file__).parent / ".env"
TOKEN_PATH = Path.home() / ".dashboard" / "token.json"

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar.readonly",
]


def run():
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
    except ImportError:
        print("Installing required packages...")
        os.system(f"{sys.executable} -m pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client --quiet")
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request

    print("\n✦ Google OAuth Setup")
    print("─" * 40)

    client_id     = os.environ.get("GOOGLE_OAUTH_CLIENT_ID", "")
    client_secret = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        raise SystemExit("Set GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET env vars")
    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        }
    }

    print("\nA browser window will open — sign in and allow access.")
    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    creds = flow.run_local_server(port=0)

    # Save to ~/.dashboard/token.json
    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    token_data = {
        "refresh_token": creds.refresh_token,
        "client_id":     client_id,
        "client_secret": client_secret,
    }
    TOKEN_PATH.write_text(json.dumps(token_data, indent=2))

    # Also save to .env
    set_key(str(ENV_PATH), "GOOGLE_CLIENT_ID",     client_id)
    set_key(str(ENV_PATH), "GOOGLE_CLIENT_SECRET",  client_secret)
    set_key(str(ENV_PATH), "GOOGLE_REFRESH_TOKEN",  creds.refresh_token)

    print(f"\n✅ Connected! Credentials saved to {TOKEN_PATH}")
    print("   Restart the dashboard and open the Work page.\n")


if __name__ == "__main__":
    run()
