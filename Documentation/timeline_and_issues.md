# Confoundr Project Timeline & Issue Log

## Phase 0: Foundations

**Objective:** Set up the core Python package for `confoundr`, define the plugin interface, and implement the first causal validity check (Target Leakage).

### Work Completed

1. **Package Initialization**

   - Created `pyproject.toml` using `setuptools.build_meta` to handle dependency management without bulky tools like Poetry.
   - Defined core dependencies: `pandas`, `numpy`, `scikit-learn`, `statsmodels`.
   - Setup optional `[dev]` dependencies for local testing (`pytest`, `black`, `isort`, `flake8`).
   - *Design Choice:* Kept dependencies zero-cost and standard for data science to ensure the package remains lightweight and easily deployable in CI/CD pipelines.
2. **Core Architecture & Schemas (`confoundr/schemas.py`, `confoundr/base.py`)**

   - Designed the `CheckContext` dataclass to standardize how datasets and metadata (e.g., target column, feature list) are passed into checks.
   - Created the `CheckResult` dataclass and Enums (`CheckStatus`, `Severity`) to guarantee every check outputs a uniform, parsable result (Pass/Fail, human-readable explanation, and statistical evidence).
   - Abstracted the check logic into `BaseCheck` (an Abstract Base Class). This ensures any future check (written by us or the community) must adhere to a strict `run(context)` contract.
3. **Target Leakage Detector (`confoundr/checks/leakage.py`)**

   - Implemented a check that calculates the Pearson correlation between numeric features and the target variable.
   - Flags features that exhibit a suspiciously high correlation (default > 0.90), as this typically indicates data from the future leaking into the training set.
   - Outputs the exact correlation values as part of the `evidence` dictionary to aid debugging.
4. **Unit Testing (`tests/test_leakage.py`)**

   - Built a synthetic dataset containing completely independent random noise to test the "Pass" state.
   - Built a synthetic dataset where one feature (`feature_leaky`) is heavily derived from the target variable to test the "Fail" state.
   - Confirmed tests pass successfully using `pytest`.

---

## Phase 1: Core Library v0.1

**Objective:** Expand the check catalog (Confounder Audit, Positivity Check), build a Command Line Interface (CLI), create benchmark datasets, and automate publishing.

### Work Completed

1. **Confounder Audit Check (`confoundr/checks/confounder.py`)**
   - Implemented a check that scans all features for suspiciously high correlations with *both* the treatment variable and the target variable, flagging them as potential measured confounders.
2. **Positivity Check (`confoundr/checks/positivity.py`)**
   - Implemented logistic regression to calculate propensity scores (the probability of receiving treatment given the features).
   - Validates the positivity assumption by calculating the overlap ratio between the propensity score distributions of the treated and control groups.
3. **Command Line Interface (`confoundr/cli.py`)**
   - Built an `argparse`-based CLI allowing users to run `confoundr check dataset.csv --target ...`.
   - Registered the CLI in `pyproject.toml` using `[project.scripts]`.
4. **Synthetic Benchmark Datasets (`scripts/generate_synthetic_data.py`)**
   - Curated a script to generate 4 distinct datasets: Clean, Leaky, Confounded, and Positivity Violation.
5. **Documentation & Automation**
   - Updated `README.MD` with before/after CLI and Python examples.
   - Configured PyPI Trusted Publishing (OIDC) via a GitHub Actions workflow (`publish.yml`).

---

## Phase 2: Service MVP

**Objective:** Wrap the core library in a FastAPI service, containerize the application, and prepare it for deployment on a PaaS.

### Work Completed

1. **FastAPI Wrapper (`api/main.py`)**
   - Built a synchronous `/api/v1/check` endpoint that accepts a CSV file upload (`multipart/form-data`) and runs the Confoundr checks.
   - Handled column validation and graceful error fallback (returning HTTP 400 or catching internal check errors).
2. **Dockerization (`Dockerfile`)**
   - Containerized the API using `python:3.11-slim`.
   - Used `pip install -e .[api]` leveraging the newly added `[project.optional-dependencies]` in `pyproject.toml` to install FastAPI and Uvicorn.
3. **Deployment Configuration (`render.yaml`)**
   - Created a Render Blueprint (`render.yaml`) to enable one-click zero-downtime deployment for the free tier web service.

---

## Phase 3: Async + Distributed Processing

**Objective:** Add a Redis-backed job queue to process datasets asynchronously in the background.

### Work Completed

1. **Job Queue & Dependencies**
   - Integrated `rq` (Redis Queue) and `redis` into the core library's `[api]` optional dependencies.
2. **Background Worker (`api/worker.py`, `api/jobs.py`)**
   - Refactored the statistical logic into an isolated function (`run_causal_checks`) that can safely execute inside an RQ worker process.
   - Created a dedicated worker script to listen for jobs on the Redis queue.
3. **Async API Endpoints (`api/main.py`)**
   - Added `POST /api/v1/async-check`: Accepts file uploads, enqueues them into Redis, and instantly returns an HTTP 202 with a `job_id`.
   - Added `GET /api/v1/job/{job_id}`: Allows clients to poll for the status (queued, started, finished, failed) and retrieve the results once completed.
4. **Infrastructure Updates (`render.yaml`)**
   - Updated the Render Blueprint to automatically provision a free Managed Redis instance, the main Web API, and a Background Worker service interconnected via the `REDIS_URL` environment variable.

---

## Phase 4: Data Store + Results History

**Objective:** Add persistent storage using PostgreSQL to record job executions, performance metrics, and causal validity results.

### Work Completed

1. **Database Integration & ORM**
   - Added `sqlalchemy` and `psycopg2-binary` to the project's API dependencies.
   - Set up `api/database.py` with dynamic fallback (SQLite for local dev, PostgreSQL for production on Render).
2. **Data Models (`api/models.py`)**
   - Designed the `JobHistory` table to store metadata (`job_id`, `filename`, `execution_time_seconds`) and serialize complex validation outputs into a flexible `JSON` column. Crucially avoided storing raw data to maintain strict privacy/compliance.
3. **Worker Persistence (`api/jobs.py`)**
   - Updated the background worker logic to open a DB session, measure execution time, and commit the final diagnostic results into Postgres immediately upon completion.
4. **History API (`api/main.py`)**
   - Implemented `GET /api/v1/history` endpoint to allow users/dashboards to retrieve past runs and compare historical validity outcomes.
   - Leveraged FastAPI's `lifespan` context manager to safely execute `Base.metadata.create_all()` on application startup to ensure tables always exist before requests hit the server.

---

## Phase 5: Observability

**Objective:** Instrument the application with Prometheus metrics to track queue health, job success/failure rates, and execution latencies, enabling external monitoring via Grafana.

### Work Completed

1. **Metrics Instrumentation (`api/main.py`)**
   - Added `prometheus-client` dependency.
   - Built a `/metrics` endpoint that queries Redis for real-time queue depth and Postgres for historical job statistics.
   - Deployed seamlessly to Render, making metrics available for scraping by external cloud providers (e.g., Grafana Cloud).
2. **Local Observability Stack (`docker-compose.yml`)**
   - Expanded the local development environment to spin up Prometheus and Grafana instances alongside the core services for instantaneous local testing and dashboard prototyping.

---

## Phase 6: Agent Explainer Layer

**Objective:** Wire failed causal checks into a Large Language Model to generate plain-language explanations and dataset fix suggestions for users.

### Work Completed

1. **LLM Integration (`api/llm.py`)**
   - Added the `groq` SDK and configured it to securely authenticate using `GROQ_API_KEY`.
   - Wrote a zero-shot prompt template for `llama-3.1-8b-instant` that positions the AI as an expert causal inference statistician, instructing it to provide concise, actionable insights based on the technical failure explanation and statistical evidence.
2. **Worker Interception (`api/jobs.py`)**
   - Intercepted any causal check resulting in a `"fail"` status inside the background worker.
   - Piped the failure details synchronously to the Groq API and attached the generated `ai_insight` to the final `CheckResult` JSON payload stored in Postgres.

---

## Issue Log

### Issue 1: PowerShell Execution Policy Restrictions

- **Problem:** Attempting to activate the Python virtual environment (`.\venv\Scripts\Activate.ps1`) failed due to Windows Execution Policies blocking unsigned scripts.
- **Resolution:** Bypassed the need for the activation script by invoking the fully qualified Python executable directly from the virtual environment folder (`.\venv\Scripts\python.exe -m pip install ...` and `.\venv\Scripts\pytest.exe`).

### Issue 2: Setuptools Package Discovery Conflict

- **Problem:** `pip install -e .` failed because `setuptools` automatically scans for top-level folders. It found both `confoundr` and the pre-existing `Documentation` folder, and refused to build since it wasn't sure which one was the actual Python package.
- **Resolution:** Explicitly defined package discovery in `pyproject.toml` by adding a `[tool.setuptools.packages.find]` block with `include = ["confoundr*"]`. This forces the build system to ignore the `Documentation` folder.

### Issue 3: CLI Unicode Errors on Windows

- **Problem:** Running the CLI generated a `UnicodeEncodeError: 'charmap' codec can't encode character` when attempting to print emojis (like 🔍 or ✅) because the default Windows console (cp1252) does not fully support modern Unicode.
- **Resolution:** Replaced emojis in `cli.py` with standard text brackets (e.g., `[PASS]`, `[FAIL]`, `[WARN]`) to ensure flawless cross-platform terminal compatibility without forcing users to reconfigure their terminal encodings.

### Issue 4: Render Blueprint Sync & Env Var Injection Delays

- **Problem:** After adding `confoundr-redis` to the `render.yaml` Blueprint, the async endpoint instantly threw a `ConnectionRefusedError: Error 111 connecting to localhost:6379`. The web service had failed to pick up the newly provisioned `REDIS_URL` environment variable.
- **Resolution:** Manually forced a **"Clear build cache & deploy"** on the Web Service in the Render Dashboard. This forced the container to restart and successfully ingest the new environment variables from the Blueprint infrastructure manager.

### Issue 5: Render Free Tier Worker Restrictions & Port Binding Timeouts

- **Problem:** Render rejected the `type: worker` service because background workers are not supported on the free tier. When we attempted to bypass this by running `python -m api.worker & uvicorn ...` in a single Web Service container via bash, the worker hijacked PID 1. This prevented Uvicorn from starting, which caused Render's health checks to fail (`Port scan timeout reached, no open ports detected`).
- **Resolution:** Abandoned the shell hack and adopted a programmatic approach. Used FastAPI's `@asynccontextmanager lifespan` event to spawn the worker via `subprocess.Popen` precisely when the application starts, allowing both Uvicorn (on port 10000) and the RQ Worker to run perfectly inside a single free-tier container.

### Issue 6: Render Database `ipAllowList` Validation

- **Problem:** Blueprint syncing failed with the error `services[2] must specify IP allow list`. Render's updated security protocols now strictly require an explicit IP allow list for all Data Stores, even if they are only accessed internally.
- **Resolution:** Appended `ipAllowList: - source: 0.0.0.0/0` to both the Redis and PostgreSQL service definitions in `render.yaml`.

### Issue 7: RQ (Redis Queue) `Connection` Import Error

- **Problem:** The background worker crashed on startup with `ImportError: cannot import name 'Connection' from 'rq'`. Recent `rq` releases (v2.x) entirely removed the legacy `Connection` context manager.
- **Resolution:** Refactored `api/worker.py` to remove the context manager and explicitly pass the Redis connection string directly to the Worker constructor (`Worker(['default'], connection=conn)`).

### Issue 8: Groq Model Deprecation & 400 Errors

- **Problem:** When testing the Phase 6 Agent Explainer, the Groq API returned a 400 Bad Request error stating that the `llama3-8b-8192` model had been decommissioned and was no longer supported.
- **Resolution:** Updated `api/llm.py` to target Groq's newer, actively supported `llama-3.1-8b-instant` model, restoring AI insight generation.
