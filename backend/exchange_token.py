"""
Fyers Token Exchange Script
============================
Step 2 of the Fyers OAuth flow: exchanges an auth_code for a live access_token.

Usage:
    1. Run generate_access_token.py first → copy the browser URL → login → copy auth_code from redirect URL
    2. Run this script and paste the auth_code when prompted
    3. The access_token will be printed AND automatically written to backend/.env

The auth_code is the raw code from the redirect URL query param ?auth_code=...
Do NOT paste the full JWT — paste only the raw code string from the URL.
"""

from fyers_apiv3 import fyersModel
from dotenv import load_dotenv
import os
import re

# Load .env from the backend directory
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path)

client_id = os.getenv("FYERS_CLIENT_ID")
secret_key = os.getenv("FYERS_SECRET_KEY")
redirect_uri = os.getenv("FYERS_REDIRECT_URI")

if not all([client_id, secret_key, redirect_uri]):
    print("ERROR: Missing FYERS_CLIENT_ID, FYERS_SECRET_KEY, or FYERS_REDIRECT_URI in .env")
    exit(1)

print(f"\nUsing CLIENT_ID: {client_id}")
print(f"Using REDIRECT_URI: {redirect_uri}\n")

auth_code = input("Paste auth_code (from redirect URL ?auth_code=...): ").strip()

if not auth_code:
    print("ERROR: No auth_code provided.")
    exit(1)

session = fyersModel.SessionModel(
    client_id=client_id,
    secret_key=secret_key,
    redirect_uri=redirect_uri,
    response_type="code",
    grant_type="authorization_code"
)

session.set_token(auth_code)

response = session.generate_token()
print("\nFYERS TOKEN RESPONSE:")
print(response)

access_token = response.get("access_token")

if not access_token:
    print("\nERROR: No access_token in response. Check auth_code is valid and not expired.")
    exit(1)

print(f"\nSUCCESS - access_token obtained (first 40 chars): {access_token[:40]}...")

# Auto-update FYERS_ACCESS_TOKEN in .env
with open(env_path, "r") as f:
    env_content = f.read()

if "FYERS_ACCESS_TOKEN" in env_content:
    env_content = re.sub(
        r"FYERS_ACCESS_TOKEN=.*",
        f"FYERS_ACCESS_TOKEN={access_token}",
        env_content
    )
else:
    env_content += f"\nFYERS_ACCESS_TOKEN={access_token}\n"

with open(env_path, "w") as f:
    f.write(env_content)

print(f"\n✅ .env updated with new FYERS_ACCESS_TOKEN")
print("   Restart the FastAPI backend to pick up the new token.")