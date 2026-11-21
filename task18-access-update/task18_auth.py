"""Fail-closed Streamlit authentication for PulseIQ Task 18.

Configure [auth.users.<username>] in Streamlit secrets with:
password_hash = "<salt_hex>$<pbkdf2_sha256_hex>"
role = "ADMIN|HR|MANAGER|EXECUTIVE"
department_ids = ["D01"]  # required for MANAGER
team_ids = ["TEAM-01"]    # optional manager scope
"""
import hashlib
import hmac
def verify_password(password: str, encoded_hash: str) -> bool:
    try:
        salt_hex, expected_hex = encoded_hash.split("$", 1)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(expected_hex)
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, 310_000
        )
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError, AttributeError):
        return False


def get_user_record(username: str):
    import streamlit as st
    try:
        users = st.secrets["auth"]["users"]
        record = users.get(username)
        if record is None:
            return None
        role = str(record.get("role", "")).upper()
        if role not in {"ADMIN", "HR", "MANAGER", "EXECUTIVE"}:
            return None
        password_hash = str(record.get("password_hash", ""))
        if not password_hash:
            return None
        if role == "MANAGER" and not record.get("department_ids"):
            return None
        return {
            "username": username,
            "role": role,
            "department_ids": list(record.get("department_ids", [])),
            "team_ids": list(record.get("team_ids", [])),
            "password_hash": password_hash,
        }
    except Exception:
        return None


def require_login():
    """Render login and return authenticated principal, or stop."""
    import streamlit as st
    if st.session_state.get("pulseiq_user"):
        principal = st.session_state["pulseiq_user"]
        st.sidebar.caption(
            f"Signed in: {principal['username']} · {principal['role']}"
        )
        if st.sidebar.button("Log out", key="pulseiq_logout"):
            st.session_state.pop("pulseiq_user", None)
            st.rerun()
        return principal

    st.title("PulseIQ Secure Login")
    st.caption("Sign in with your assigned account.")
    with st.form("pulseiq_login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in", use_container_width=True)

    if submitted:
        record = get_user_record(username.strip())
        if record and verify_password(password, record["password_hash"]):
            record.pop("password_hash", None)
            st.session_state["pulseiq_user"] = record
            st.rerun()
        st.error("Invalid username or password.")

    st.warning(
        "Access is disabled until an administrator configures user accounts "
        "in Streamlit secrets. Do not store passwords in source code."
    )
    st.stop()
