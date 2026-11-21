# Task 18 access-control setup

## Important implementation boundary
- Login is required before dashboard content loads.
- User passwords are stored as PBKDF2-SHA256 hashes in Streamlit secrets.
- Task 18 KPI selection is checked against the authenticated role's metric allowlist.
- Restricted metric IDs are excluded.
- Non-admin roles are limited to Task 18 until role-specific authorization and row-level SQL scoping are added to every legacy dashboard page.
- Manager accounts are deliberately denied dashboard data until manager department/team filters are implemented in every relevant query. This is fail-closed; it is not yet a usable manager dashboard.

## Configure credentials
1. Run `python generate_task18_password_hash.py` for each user and copy the generated `salt_hex$hash_hex` output.
2. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`.
3. Replace each placeholder with a generated hash and set the actual account names and roles.
4. For manager users, add explicit `department_ids` (and optionally `team_ids`). Manager sign-in remains blocked from data pages until row-level scope is implemented.
5. Never commit `.streamlit/secrets.toml`. Add it to `.gitignore` if not already present.
6. For Streamlit Community Cloud, paste the same TOML configuration into App Settings -> Secrets.

## Validation
Run:
- `python -m py_compile app.py task18_config.py task18_auth.py`
- `python test_task18_access.py`
- `python test_task18_suppression.py`

## Before claiming Task 18 is 100% complete
Implement and test manager department/team filters in every dashboard SQL query, add page-level permissions for HR and EXECUTIVE, and run Streamlit integration tests with real test accounts and the deployed secrets configuration.
