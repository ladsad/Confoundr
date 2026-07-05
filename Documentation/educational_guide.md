# Educational Guide: Causal Validity & Confoundr Architecture

## 1. What is Causal Validity?

In machine learning, we often train models to minimize prediction error. However, when a model's output is used to make a *decision* (e.g., "should we offer this customer a discount to prevent churn?"), we are assuming the model has learned the *causal* relationship between the intervention (discount) and the outcome (churn).

Standard data quality tools (like Great Expectations) check if the data schema is correct or if there are missing values. **Confoundr** checks if the data violates assumptions required for valid causal inference.

### Example: Target Leakage

Target leakage occurs when a feature in the training data would not be available at the time of prediction in the real world, and it perfectly proxies the target variable.

* *Real-world consequence:* The model looks incredibly accurate during training and testing, but fails entirely in production.
* *How Confoundr detects it:* By identifying features with suspiciously high correlations to the target variable (e.g., Pearson correlation > 0.90) and alerting the user before the model is deployed.

## 2. Why the Two-Layer Architecture?

The project plan explicitly separates the **Core Library** (the `confoundr` Python package) from the **Deployed Platform** (the SaaS wrapper).

* **Portability:** By keeping the library dependency-light, anyone can `pip install confoundr` and run it locally in a Jupyter Notebook or as part of a CI/CD pipeline (like GitHub Actions) without needing our cloud infrastructure.
* **Separation of Concerns:** Data science logic (statistical checks) lives purely in the library. Infrastructure logic (job queues, webhooks, multi-tenancy) lives purely in the platform layer. This makes both significantly easier to test.

## 3. The Plugin Interface Design Pattern

To make this project "PR-friendly" (easy for other developers to contribute to), we used the **Plugin Pattern** via an Abstract Base Class (`BaseCheck`).

Instead of writing one massive Python script with hundreds of `if/else` statements for different checks, we defined a strict contract:

1. **Input:** Every check takes a `CheckContext` (which guarantees they all receive the DataFrame and configuration in the exact same format).
2. **Output:** Every check must return a `CheckResult` (which guarantees they all return a Pass/Fail status, an explanation, and evidence).

If a community member wants to add a new check (e.g., "Instrument Validity"), they don't need to understand the entire codebase. They simply create a new class that inherits from `BaseCheck` and implements the `run()` method.

## 4. Key Learnings from Phase 0

* **Packaging:** Modern Python packaging favors `pyproject.toml` with `setuptools.build_meta` over the older `setup.py`. It provides a cleaner, declarative way to specify dependencies.
* **Virtual Environments on Windows:** PowerShell's default execution policies often block `.ps1` scripts like `Activate.ps1`. A reliable workaround in automation is to use the fully qualified path to the Python executable inside the virtual environment (`.\venv\Scripts\python.exe`) rather than relying on the shell state.
* **Setuptools Auto-Discovery:** Be careful when mixing code packages (like `confoundr/`) and non-code folders (like `Documentation/`) at the root level. `setuptools` might confuse them, so explicitly defining `packages.find` in `pyproject.toml` is a best practice.

## 5. Testing Causal Validity Checks

Unlike standard unit tests that check if a function returns `2` when given `1 + 1`, testing causal validity requires **synthetic datasets**.

Because causal properties are inherent to the data generating process, we cannot just use any random real-world dataset. We must deliberately construct datasets with known flaws:

* **Testing a Pass:** We generate completely random, independent noise for features and the target variable. Since they are independent, a Target Leakage check *must* pass.
* **Testing a Fail:** We generate a target variable, and then deliberately create a `feature_leaky` column by adding slight noise directly to the target. Since the feature is artificially derived from the target, the check *must* fail.

This "known-bad" synthetic data approach is the standard evaluation methodology for MLOps and data quality tools.

## 6. Understanding Positivity & Propensity Scores

In causal inference, the **Positivity Assumption** (also known as the overlap assumption) requires that all subjects have a non-zero probability of receiving either the treatment or the control, regardless of their features.

* *Real-world consequence:* If doctors *only* ever give a new drug to patients under 30, and *only* give the old drug to patients over 30, we have zero overlap. We mathematically cannot determine if the drug works better, because the treatment is perfectly confounded by age.
* *How Confoundr detects it:* Confoundr fits a **Logistic Regression** model predicting the treatment based on the features to calculate a **Propensity Score** (the probability of receiving treatment). It then plots the distribution of these scores for both the treated and control groups. If the groups are completely separated (i.e., an overlap ratio near 0%), the positivity assumption is violated, and a causal model will fail to generalize.

## 7. Key Learnings from Phase 2 (Service MVP)

* **Optional Dependencies in Packaging:** By defining `[project.optional-dependencies]` (like `api = ["fastapi", "uvicorn"]`) in `pyproject.toml`, we prevent forcing heavy API frameworks onto users who only want to use the core data science library. Users run `pip install confoundr` for the library, and we run `pip install confoundr[api]` inside our Docker container.
* **Separation of Concerns in API Design:** The FastAPI endpoints do not contain any statistical logic. They simply parse the HTTP request, instantiate the `CheckContext`, and pass it to the exact same core library used by the CLI.
* **Why `multipart/form-data`?** Rather than forcing the client to serialize a large dataset into JSON arrays (which balloons the payload size), we accept raw `.csv` files as binary uploads via `UploadFile`. This is parsed in-memory using `io.BytesIO` and Pandas, avoiding disk I/O bottlenecks on the server.
* **Dockerizing Python Apps:** We used `python:3.11-slim` rather than `alpine`. Alpine Linux uses `musl` libc instead of `glibc`, which causes standard Python data science wheels (like `numpy` and `pandas`) to compile from scratch instead of downloading pre-compiled binaries, increasing build times massively. The `slim` image provides out-of-the-box wheel compatibility while keeping the image size small.
* **Zero-Downtime PaaS Deployment:** Using a `render.yaml` Blueprint file allows for Infrastructure-as-Code (IaC) deployment. Render automatically provisions the environment, builds the Dockerfile, and maps the exposed port to the public internet, completing the transition from a local library to a deployed platform service.

## 8. Key Learnings from Phase 3 (Async & Distributed Processing)

* **Handling Heavy Computations:** Causal validity checks (like fitting a Logistic Regression model for the Positivity Check) are CPU-bound and can take seconds or minutes on large datasets. If these were executed synchronously in the API, the HTTP connection would time out, and the web server would block other users.
* **The Redis Queue Architecture:** We solved this by implementing `rq` (Redis Queue). The API endpoint (`POST /async-check`) instantly returns an HTTP 202 (Accepted) and a `job_id`. In the background, the actual dataset and parameters are pickled and pushed into a Redis memory store.
* **Bypassing PaaS Limitations via Subprocessing:** Free-tier platforms often restrict multi-service architectures (like running a dedicated Background Worker service). We cleanly bypassed this by utilizing FastAPI's `@asynccontextmanager lifespan` event. When the API container boots up, it programmatically spawns the RQ worker in the background using Python's `subprocess.Popen` before binding to the web port. This allows both the Web Server and the Worker process to co-exist in the exact same Docker container, dramatically simplifying free-tier deployments while maintaining a production-grade async architecture.

## 9. Key Learnings from Phase 4 (Data Store & Results History)

* **Data Privacy & Schema Design:** Causal inference is heavily used in healthcare and finance. For security and compliance, the database schema (`JobHistory`) explicitly **does not store the raw datasets**. It only stores metadata (job IDs, execution times) and the final serialized JSON `CheckResult` outputs.
* **SQLAlchemy ORM & Database Agnosticism:** By using SQLAlchemy (`Base.metadata.create_all()`), the application is completely decoupled from the database dialect. During local development, it defaults to `sqlite:///./confoundr.db`, but automatically switches to `postgresql://` when deployed to Render without changing a single line of business logic.
* **Writing Job Results from the Worker:** Rather than the API polling the worker and writing to the database, the Worker process itself is responsible for committing the `JobHistory` record to Postgres immediately after processing finishes. This guarantees that results are permanently archived even if the user never calls the `GET /api/v1/job/{job_id}` polling endpoint.
