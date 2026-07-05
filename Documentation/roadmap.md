# Confoundr Roadmap

## Phase 0: Foundations

- Lock name, register PyPI package and GitHub repo.
- Write the plugin interface contract (input/output schema).
- Implement Leakage Detector against a synthetic dataset with known leakage.
- Setup Unit tests and GitHub Actions CI.

## Phase 1: Core Library v0.1

- Implement Confounder Audit and Positivity Check.
- Build CLI tool (`confoundr check data.csv --config checks.yaml`).
- Curate 3-5 synthetic benchmark datasets with known issues.
- Publish to PyPI and document usage.

## Phase 2: Service MVP

- Develop FastAPI endpoint wrapping the library for synchronous, single-dataset uploads.
- Dockerize API and library.
- Deploy to Fly.io/Render.

## Phase 3: Async & Distributed Processing

- Add Redis-backed job queue.
- Setup separate worker processes for pulling jobs.
- Implement job status model (`queued → running → succeeded/failed`) with retry/backoff.
- Add webhook/polling endpoints for job completion.

## Phase 4: Persistence & Multi-tenancy

- Setup Postgres schema (users, datasets, check runs, results, history).
- Implement per-user data isolation.
- Add basic authentication (Supabase Auth / JWT).

## Phase 5: Observability

- Export Prometheus metrics (queue depth, job success/failure rate, latency).
- Setup Grafana dashboard.
- Configure alerting.

## Phase 6: Agent Explainer Layer

- Wire failed checks to an LLM (Groq/Ollama) to explain root causes and suggest fixes.
- Evaluate explanation quality against a hand-labeled failure set.

## Phase 7: Security Hardening

- Implement resource-limited, ephemeral execution for untrusted data.
- Document the threat model and mitigations.

## Phase 8: Dashboard

- Develop Next.js frontend (upload flow, run history, results view, basic alerts).

## Ongoing

- Expand check catalog (SUTVA, instrument validity).
- PySpark support for large datasets.
- Feast integration for feature store validation.
