# InsightAI

Upload a CSV, analyze it in Python, and explore what the numbers actually show.

InsightAI is a data-analysis platform: a FastAPI backend computes real statistics
with pandas, a React dashboard presents them, and an optional Gemini-powered
assistant explains the results. The assistant never sees the raw dataset and never
produces a statistic of its own — it only reads the analysis the application
computed.

**The governing principle: Python performs the analysis. The AI explains it.**

---

## Features

- **CSV upload** with drag-and-drop, type and size validation, and filename sanitising.
- **Dataset preview** — shape, detected column types, missing-value counts, duplicate
  rows, and the first rows exactly as parsed.
- **Analysis engine** — descriptive statistics, data-quality checks, categorical
  frequency analysis, Pearson correlation, IQR outlier detection, and multivariate
  anomaly detection.
- **Automatic insights** — findings derived from computed numbers, each with a title,
  an explanation, the supporting metric, and a severity.
- **Visualizations** — histograms, category bars, a box-plot summary, a scatter plot of
  the most correlated pair, a correlation heatmap, and a time series when the data has
  a date column.
- **Optional AI assistant** — answers questions about a dataset from its stored
  analysis, with a system prompt that forbids inventing values.
- **Analysis history** — results are persisted, so an analysis is computed once and
  reused.

---

## Architecture

```mermaid
flowchart TD
    UI[React + TypeScript frontend]
    API[FastAPI routes]
    SVC[Services: datasets, analysis, AI]
    ENG[Analysis engine: pandas, NumPy, scikit-learn]
    DB[(PostgreSQL)]
    FS[[CSV files on disk]]
    AI[AI service]
    G[Gemini API]

    UI -->|REST /api| API
    API --> SVC
    SVC --> ENG
    SVC --> DB
    SVC --> FS
    ENG -->|statistics and insights| SVC
    SVC --> AI
    AI -->|structured analysis context| G
    G -->|explanation| AI
```

### Why this shape

**The analysis engine is a pure Python package.** `app/analysis` imports pandas and
NumPy and nothing else — no FastAPI, no SQLAlchemy, no Gemini. That makes every
statistic testable as a plain function call, and it makes the dependency direction
obvious: routes depend on services, services depend on the engine, and nothing
depends on the AI.

**Insights are generated from the computed summary, not from the DataFrame.**
`insights.py` receives the dictionary of already-calculated numbers. It is
structurally incapable of reporting a statistic the application did not calculate.

**The AI is a plug-in, behind a protocol.** `app/ai/provider.py` defines the
interface; `GeminiProvider` implements it, `NullProvider` stands in when no key is
configured, and `MockAIProvider` serves the tests. No test touches the network, and
the application starts and runs fully without an API key.

**Raw rows live on disk, never in PostgreSQL.** The database stores metadata,
analysis results, insights and conversations. Storing CSV contents in Postgres would
add cost and risk for no analytical benefit, since every read is a full-file read.

**Analysis results are persisted as JSON.** The uploaded file is immutable, so a
computed result stays correct. Re-opening an analysis page is a database read, not a
recomputation.

---

## Technology stack

| Layer | Technology | Why |
| --- | --- | --- |
| API | FastAPI, Pydantic | Typed request/response validation and generated OpenAPI docs |
| Analysis | pandas, NumPy | The standard tools for tabular statistics |
| Anomalies | scikit-learn | Isolation Forest for multivariate outliers, which per-column rules cannot find |
| Persistence | SQLAlchemy 2.0, PostgreSQL | Relational data with real foreign keys; JSONB for analysis results |
| AI | google-genai (Gemini) | Optional explanation layer behind a provider interface |
| Frontend | React, TypeScript, Vite, Recharts | Component-based UI with typed API contracts and composable charts |
| Tests | pytest, httpx | Unit tests for the engine, API tests through the FastAPI test client |

---

## Project structure

```
insightai/
├── backend/
│   ├── app/
│   │   ├── analysis/        # Pure analysis: profiler, statistics, quality,
│   │   │                    # categorical, correlation, anomalies, insights,
│   │   │                    # visualizations, engine
│   │   ├── ai/              # Provider protocol, Gemini, mock, context builder, prompts
│   │   ├── api/             # Routes and dependencies (thin)
│   │   ├── core/            # Config, errors, logging
│   │   ├── database/        # Engine, session, schema creation
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic request/response models
│   │   ├── services/        # Dataset, analysis, AI, storage, CSV loading
│   │   └── main.py
│   ├── tests/{unit,integration}/
│   └── requirements.txt
├── frontend/
│   └── src/{components,pages,services,hooks,types,utils}/
├── data/sample/             # Ready-to-upload example CSVs
├── docs/
├── .env.example
└── README.md
```

---

## Setup

### Requirements

- Python 3.12 or newer
- Node.js 20 or newer
- PostgreSQL 14 or newer

### 1. Clone and configure

```bash
git clone <your-repo-url> insightai
cd insightai
cp .env.example .env
```

### 2. Database

```bash
createdb insightai
createuser insightai --pwprompt      # or reuse an existing role
```

Point `DATABASE_URL` in `.env` at it:

```
DATABASE_URL=postgresql+psycopg://insightai:insightai@localhost:5432/insightai
```

Tables are created automatically on first start. The project has a single schema
version and no production data to migrate, so it creates tables from SQLAlchemy
metadata rather than carrying a migration tool.

### 3. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

The API is at <http://localhost:8000>, interactive docs at
<http://localhost:8000/docs>.

### 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open <http://localhost:5173>. Vite proxies `/api` to the backend, so no CORS setup is
needed in development.

### 5. Try it

Upload `data/sample/customer_churn.csv`, press **Run analysis**, and read the
insights.

---

## Environment variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | local Postgres URL | SQLAlchemy connection string |
| `GEMINI_API_KEY` | *(empty)* | Enables the AI assistant. Empty disables it cleanly |
| `GEMINI_MODEL` | `gemini-2.0-flash` | Model used for assistant replies |
| `GEMINI_TIMEOUT_SECONDS` | `30` | Request timeout |
| `MAX_UPLOAD_BYTES` | `20971520` (20 MB) | Upload size limit |
| `PREVIEW_ROWS` | `20` | Default preview row count |
| `CORS_ORIGINS` | `http://localhost:5173` | Comma-separated allowed origins |
| `DEFAULT_USER_EMAIL` | `demo@insightai.local` | Identity used when no `X-User-Email` header is sent |
| `STORAGE_DIR` | `backend/storage` | Where uploaded CSVs are written |

Secrets live only in the environment. `.env` is git-ignored, and API keys are never
sent to the client or included in an error message.

---

## Gemini configuration

The assistant is optional and off by default.

1. Create an API key in Google AI Studio.
2. Put it in `.env`: `GEMINI_API_KEY=your_key_here`
3. Restart the backend.

With no key, `GET /api/ai/status` reports `enabled: false`, the assistant page explains
that AI is unavailable, and every other feature works normally. Failures during a call
— timeout, rate limit, bad credentials, empty response, network error — are translated
into a safe message and returned as `503 AI_UNAVAILABLE`. The underlying exception is
logged on the server and never returned to the client.

---

## Running the tests

```bash
cd backend
pytest                       # 100 tests
pytest --cov=app             # with coverage
```

The suite runs against SQLite and a temporary storage directory, so it needs neither
PostgreSQL nor network access. AI behaviour is tested through `MockAIProvider`,
covering a successful answer, a timeout, an empty response, a missing API key, and an
unexpected provider crash.

Frontend type checking and build:

```bash
cd frontend
npm run typecheck
npm run build
```

---

## Example datasets

| File | What it demonstrates |
| --- | --- |
| `data/sample/customer_churn.csv` | 603 rows. Missing values in `age` (20.9%) and `total_spend`, duplicate rows, an identifier-like column, a heavily imbalanced `churn` column, and strong correlations between tenure and spend |
| `data/sample/marketing_campaigns.csv` | 400 rows. A date column driving a time-series chart, a constant `currency` column, and several correlated numeric measures |
| `data/sample/product_reviews.csv` | 120 rows. A column with 32.5% missing values, a boolean column, and a dominant category |

---

## API overview

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/datasets` | Upload a CSV (multipart). `201`, or `400` / `413` on rejection |
| `GET` | `/api/datasets` | List the caller's datasets |
| `GET` | `/api/datasets/{id}` | Dataset metadata |
| `DELETE` | `/api/datasets/{id}` | Delete a dataset and its stored file. `204` |
| `GET` | `/api/datasets/{id}/preview?rows=20` | Columns, types and the first rows |
| `POST` | `/api/datasets/{id}/analyze?force=false` | Run (or reuse) the analysis. `201` |
| `GET` | `/api/datasets/{id}/analysis` | Latest analysis. `404 ANALYSIS_NOT_FOUND` if none |
| `GET` | `/api/datasets/{id}/analyses` | Analysis history |
| `GET` | `/api/datasets/{id}/insights` | Generated insights |
| `GET` | `/api/datasets/{id}/visualizations` | Chart specifications |
| `POST` | `/api/datasets/{id}/ai/chat` | Ask a question. `503` when AI is unavailable |
| `GET` | `/api/datasets/{id}/ai/messages` | Conversation history |
| `GET` | `/api/dashboard` | Counts and recent datasets |
| `GET` | `/api/ai/status` | Whether the assistant is configured |
| `GET` | `/api/health` | Liveness |

Errors always have the same shape:

```json
{
  "error": "INVALID_DATASET",
  "message": "The uploaded CSV does not contain enough valid data for analysis."
}
```

Full schema documentation is generated at `/docs`.

---

## Security

- Uploads are restricted to `.csv` by extension and declared content type, capped by
  size, and read with the limit enforced during the read rather than after it.
- Filenames from the client are sanitised and used for display only. Files are stored
  under a generated UUID key, and storage paths are resolved and checked to stay inside
  the storage directory.
- Uploaded files are parsed, never executed.
- Datasets are scoped to a user. A request for someone else's dataset returns `404`,
  not `403`, so the API does not confirm that the id exists.
- Request bodies are validated by Pydantic schemas; ORM models are never returned
  directly.
- Stack traces never reach the client. Unhandled exceptions are logged server-side and
  returned as a generic `INTERNAL_ERROR`.
- API keys are read from the environment only, and `.env` is git-ignored.

---

## Design decisions

**Identity is a header, not a login.** `X-User-Email` selects (or creates) a user and
defaults to a demo user. This project is about data analysis, and a real auth system
would be a large feature demonstrating something else. The ownership checks are genuine
and tested — only the credential step is absent, and it is absent on purpose rather
than faked.

**No task queue.** Analysis of a file within the upload limit completes in the request.
A queue would add a broker, a worker, and polling for a problem the upload limit already
prevents. If that limit ever rose, this is the first thing to change.

**No migration tool.** One schema version, no production data. Alembic would be
ceremony without a payoff today.

**Plain CSS, no UI framework.** The interface needs cards, tables and charts. A design
system would be more code and more dependency than the product needs.

**Charts are specified by the backend.** Choosing which chart answers a question is
analysis, so it belongs with the analysis. The frontend renders what it is handed, which
keeps chart selection testable in Python.

**Identifier-like columns are withheld from the AI context.** A near-unique text column
contributes raw row content and no information the model can reason about, so only its
cardinality is sent.

---

## Limitations

- Single-process, synchronous analysis; a large file occupies a worker while it computes.
- Files are held in memory during parsing, which is what the upload limit protects.
- CSV only. No Excel, JSON or Parquet.
- Correlation is Pearson, so it measures linear association only.
- No authentication, password handling or session management.
- The assistant has summary statistics only, so it cannot answer questions about
  individual rows — and it says so rather than guessing.
- Analyses are cached per dataset and recomputed only when `force=true` is passed.

---

## Future improvements

- Real authentication and per-user API keys.
- Background analysis with progress reporting, lifting the file-size ceiling.
- Column-level drill-down pages with filtering.
- More formats: Excel, JSON, Parquet.
- Spearman correlation and categorical association measures alongside Pearson.
- Exporting an analysis as a PDF or a shareable link.
