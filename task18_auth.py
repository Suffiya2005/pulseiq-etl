"""PulseIQ username and password authentication."""

import hashlib
import hmac
import re
import streamlit as st

ALLOWED_ROLES = {"ADMIN", "HR", "MANAGER", "EXECUTIVE"}


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, iterations_text, salt_hex, digest_hex = stored_hash.split("$")
        if algorithm != "PBKDF2-SHA256":
            return False

        iterations = int(iterations_text)
        if not 100000 <= iterations <= 2000000:
            return False

        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
        if len(salt) != 16 or len(expected) != 32:
            return False

        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, iterations
        )
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError, AttributeError):
        return False


def get_user_record(username: str, password: str):
    try:
        users = st.secrets["auth"]["users"]
        login_id = username.strip().lower()

        # Prefer exact username match.
        matched_username = login_id if login_id in users else None

        # Otherwise, find a unique email match.
        if matched_username is None:
            email_matches = [
                key for key, value in users.items()
                if str(value.get("email", "")).strip().lower() == login_id
            ]
            if len(email_matches) != 1:
                return None
            matched_username = email_matches[0]

        record = users[matched_username]

        if not verify_password(
            password, str(record.get("password_hash", ""))
        ):
            return None

        role = str(record.get("role", "")).upper()
        if role not in ALLOWED_ROLES:
            return None

        department_ids = record.get("department_ids", [])
        team_ids = record.get("team_ids", [])

        if not isinstance(department_ids, (list, tuple)):
            return None
        if not isinstance(team_ids, (list, tuple)):
            return None

        department_ids = list(department_ids)
        team_ids = list(team_ids)

        if role == "MANAGER":
            if not department_ids or any(
                not isinstance(v, str) or not re.fullmatch(r"D\\d{2}", v)
                for v in department_ids
            ):
                return None

        return {
            "username": matched_username,
            "email": str(record.get("email", "")),
            "role": role,
            "department_ids": department_ids,
            "team_ids": team_ids,
        }
    except Exception:
        return None


def require_login():
    if "pulseiq_principal" not in st.session_state:
        st.title("PulseIQ Secure Login")
        st.caption("Sign in using your approved PulseIQ account.")

        with st.form("pulseiq_login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button(
                "Sign in", use_container_width=True
            )

        if submitted:
            principal = get_user_record(username, password)
            if principal is None:
                st.error("Invalid username or password.")
            else:
                st.session_state["pulseiq_principal"] = principal
                st.rerun()

        st.stop()

    principal = st.session_state["pulseiq_principal"]
    st.sidebar.caption(
        f"Signed in: {principal['username']} | {principal['role']}"
    )

    if st.sidebar.button("Log out", key="pulseiq_logout"):
        st.session_state.pop("pulseiq_principal", None)
        st.rerun()

    return principal
