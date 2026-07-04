# Confoundr Architecture

Confoundr consists of a two-layer architecture, separating the core validity logic from the deployed platform.

## 1. Core Library (`confoundr` pip package)
The core library is standalone and dependency-light. It can be used in anyone's pipeline or CI/CD without touching the hosted platform.

**Tech Stack**: Python, pandas, statsmodels, scikit-learn.

### Plugin Interface
Each check in the library implements a common plugin interface:
- **Input**: Dataframe + configuration
- **Output**: Pass/fail status + evidence + human-readable explanation

This makes contributing new checks a self-contained, low-effort process.

## 2. Deployed Platform
A service that wraps the core library to provide asynchronous, multi-tenant checks on uploaded datasets.

**Architecture Flow**:
```text
Upload / connect source → API layer (auth, job submission)
                              → Job queue (Redis)
                                  → Worker pool (runs core library checks)
                                      → Storage (Postgres metadata + object storage for datasets/reports)
                                          → Dashboard (insights, history, alerts)
```

**Tech Stack**:
- **API**: FastAPI (Python)
- **Job Queue**: Redis (via Upstash)
- **Worker**: Python worker process(es) in Docker, using `arq` or `rq`.
- **Metadata DB**: Postgres (via Supabase)
- **Object Storage**: Supabase storage
- **Frontend Dashboard**: Next.js on Vercel
- **LLM Explainer Layer**: Groq free tier or local Ollama
- **Observability**: Prometheus + Grafana
- **CI/CD**: GitHub Actions
- **Hosting**: Fly.io or Render

## Security & Execution
- Multi-tenant data isolation using Postgres row-level access checks and scoped object storage paths.
- Sandboxed, resource-limited ephemeral execution for checks running on untrusted uploaded user data (CPU/memory/time caps).
