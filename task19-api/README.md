\# PulseIQ Metrics API — Task 19



\## 1. Overview



PulseIQ Metrics API is an authenticated, read-only FastAPI service exposing five approved financial KPIs.



| Metric ID | Metric |

|---|---|

| M16 | Revenue |

| M17 | Net profit |

| M18 | Operating margin |

| M19 | Payroll as % revenue |

| M20 | Days sales outstanding |



\## 2. Technology



\- Python

\- FastAPI

\- Uvicorn

\- PostgreSQL

\- Psycopg

\- Existing Task 18 authentication and role configuration



\## 3. Local Setup



Activate the virtual environment:



```powershell

.\\.venv\\Scripts\\Activate.ps1

```



Install dependencies:



```powershell

pip install -r requirements.txt

```



Start the API from the repository root:



```powershell

uvicorn task19\_api.main:app --host 127.0.0.1 --port 8000

```



API URL: `http://127.0.0.1:8000`



Interactive documentation: `http://127.0.0.1:8000/docs`



\## 4. Authentication



The API uses bearer-token authentication.



Endpoint: `POST /auth/token`



Example request:



```json

{

&#x20; "username": "admin",

&#x20; "password": "YOUR\_PASSWORD"

}

```



Example response structure:



```json

{

&#x20; "access\_token": "REDACTED\_TOKEN",

&#x20; "token\_type": "bearer",

&#x20; "expires\_in": 1800,

&#x20; "role": "ADMIN"

}

```



Use the returned token in the Authorization header:



`Authorization: Bearer YOUR\_ACCESS\_TOKEN`



Only ADMIN and EXECUTIVE roles are currently permitted to access these financial metrics. Tokens expire after 1800 seconds.



\## 5. API Endpoints



| Method | Endpoint | Purpose |

|---|---|---|

| GET | `/` | Service information |

| GET | `/health` | Health check |

| POST | `/auth/token` | Obtain access token |

| GET | `/metrics` | List permitted metrics |

| GET | `/metrics/{metric\_id}` | Retrieve metric data |

| GET | `/freshness` | Check freshness status |



Financial metric endpoints require authentication.



\## 6. Metric Request Example



```http

GET /metrics/M16

Authorization: Bearer YOUR\_ACCESS\_TOKEN

```



Replace M16 with M17, M18, M19 or M20.



Responses include the metric definition, formula, unit, source, reporting date, latest value, historical data and lineage.



\## 7. Data Freshness



Current freshness response:



\- Pipeline status: `not\_checked`

\- Financial feed status: `unverified`

\- Last refresh: `null`

\- Source refresh metadata available: `false`



The refresh timestamps for `dq\_reference.fact\_ledger` and `dq\_reference.fact\_invoice` have not been verified. The general ETL run summary is not sufficient evidence of financial feed freshness.



\## 8. Security



\- Read-only database connection.

\- Approved warehouse metric views.

\- Role-based API authorization.

\- Bearer-token authentication.

\- Secrets excluded from source control.

\- No direct API write access to warehouse tables.



\## 9. Architecture and Limitations



The API reads the existing warehouse metric views. The Streamlit dashboard and FastAPI are separate consumers of these views; the dashboard is not currently documented as consuming the API.



The upstream ingestion process populating the financial reference tables still requires verification.



\## 10. Deployment



Application entry point:



`task19\_api.main:app`



Deployment requires secure configuration of database credentials, authentication secrets and the API signing secret. Never commit these values to Git.

