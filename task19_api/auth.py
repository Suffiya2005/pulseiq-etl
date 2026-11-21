import base64
import hashlib
import hmac
import json
import os
import time
from pathlib import Path
import tomllib

from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from task18_auth import verify_password

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
load_dotenv(ROOT / ".env.example", override=False)

TOKEN_SECRET = os.getenv("TASK19_API_SECRET", "")
TOKEN_TTL_SECONDS = 1800
bearer_scheme = HTTPBearer(auto_error=False)

ALLOWED_API_ROLES = {"ADMIN", "EXECUTIVE"}


def load_users():
    secrets_path = ROOT / ".streamlit" / "secrets.toml"
    if not secrets_path.exists():
        raise RuntimeError("Authentication secrets file is missing.")

    with secrets_path.open("rb") as file:
        data = tomllib.load(file)

    users = data.get("auth", {}).get("users", {})
    if not isinstance(users, dict):
        raise RuntimeError("Authentication user configuration is invalid.")
    return users


def authenticate_user(username: str, password: str):
    login_id = username.strip().lower()
    users = load_users()

    matched = login_id if login_id in users else None

    if matched is None:
        matches = [
            key for key, record in users.items()
            if str(record.get("email", "")).strip().lower() == login_id
        ]
        if len(matches) != 1:
            return None
        matched = matches[0]

    record = users[matched]
    if not verify_password(password, str(record.get("password_hash", ""))):
        return None

    role = str(record.get("role", "")).upper()
    if role not in ALLOWED_API_ROLES:
        return None

    return {"username": matched, "role": role}


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def create_access_token(user: dict) -> str:
    if len(TOKEN_SECRET) < 40:
        raise RuntimeError("TASK19_API_SECRET is missing or too short.")

    now = int(time.time())
    payload = {
        "sub": user["username"],
        "role": user["role"],
        "iat": now,
        "exp": now + TOKEN_TTL_SECONDS,
    }

    body = _b64encode(
        json.dumps(payload, separators=(",", ":")).encode("utf-8")
    )
    signature = hmac.new(
        TOKEN_SECRET.encode("utf-8"),
        body.encode("ascii"),
        hashlib.sha256,
    ).digest()

    return body + "." + _b64encode(signature)


def decode_access_token(token: str):
    try:
        if len(TOKEN_SECRET) < 40:
            raise ValueError("Signing secret unavailable.")

        body, supplied_signature = token.split(".", 1)
        expected_signature = hmac.new(
            TOKEN_SECRET.encode("utf-8"),
            body.encode("ascii"),
            hashlib.sha256,
        ).digest()

        if not hmac.compare_digest(
            expected_signature, _b64decode(supplied_signature)
        ):
            raise ValueError("Invalid signature.")

        payload = json.loads(_b64decode(body))
        if int(payload["exp"]) <= int(time.time()):
            raise ValueError("Token expired.")

        if payload.get("role") not in ALLOWED_API_ROLES:
            raise ValueError("Role not allowed.")

        if not isinstance(payload.get("sub"), str):
            raise ValueError("Invalid subject.")

        return payload
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired bearer token.")


def require_api_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Bearer token required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decode_access_token(credentials.credentials)
