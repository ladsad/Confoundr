# Confoundr Threat Model & Security Mitigations

## System Context
Confoundr is a causal validity platform that allows users to upload arbitrary datasets (CSV, Parquet, JSON) to be processed by a Python backend (Pandas, Scikit-learn, Statsmodels) inside an asynchronous background worker. 

Because we accept potentially untrusted, user-generated data and run CPU/Memory-intensive statistical models on it, the application has specific vulnerabilities that must be mitigated to prevent Denial of Service (DoS) and infrastructure collapse.

## Threat Analysis

### 1. "CSV Bomb" (Resource Exhaustion via Malicious Payload)
- **Threat:** An attacker uploads a relatively small, highly compressed file (or a file with millions of sparse columns) that expands to consume gigabytes of RAM when parsed into a Pandas DataFrame.
- **Impact:** The worker process allocates too much memory, causing the Linux Kernel OOM Killer to terminate the container. Because the worker shares the same container as the API (in free-tier deployments), the entire web application crashes.
- **Mitigation:** 
  - **Upload Size Hard Cap:** FastAPI intercepts the upload and drops the request if `UploadFile.size > 50MB` before reading it into memory.
  - **OS-Level Process Isolation (Linux `resource`):** Before executing the causal checks, the worker process invokes `resource.setrlimit(resource.RLIMIT_AS, 500MB)`. If Pandas attempts to allocate more than 500MB of RAM, the OS intercepts it, raising a `MemoryError` inside Python. The worker catches this, fails the specific job, but **keeps the web server alive**.

### 2. CPU Exhaustion (Algorithmic Complexity Attacks)
- **Threat:** An attacker uploads a dataset specifically crafted to maximize the computational complexity of the Positivity Check (Logistic Regression) or the Confounder Audit, causing the algorithm to hang in an infinite loop or take hours to converge.
- **Impact:** The worker thread is blocked indefinitely. The Redis queue fills up, preventing legitimate users from receiving their causal diagnostics.
- **Mitigation:**
  - **RQ Timeout Constraint:** `job_queue.enqueue` enforces a strict 300-second (5 minute) `job_timeout`. If the model fails to converge, the Redis worker aggressively kills the execution.
  - **OS-Level CPU Time Constraint:** The worker sets `resource.setrlimit(resource.RLIMIT_CPU, 300)`. This guarantees the process receives a `SIGXCPU` signal from the Linux kernel exactly at the 5-minute mark of pure execution time, ensuring a hung C-extension (like Scipy) is terminated even if it escapes RQ's timeout wrapper.

### 3. Data Privacy (Data Leakage)
- **Threat:** An attacker (or a subsequent vulnerability) gains read access to the database or Redis cache, exposing sensitive financial or healthcare data uploaded by users.
- **Impact:** Severe regulatory and compliance violation.
- **Mitigation:**
  - **Ephemeral Data Flow:** Raw data is NEVER written to the Postgres database. It is temporarily stored in Redis, processed in memory, and instantly discarded. The `JobHistory` table strictly serializes only the metadata (status, timestamp) and the aggregate statistical output (`CheckResult` JSON).

## Conclusion
By combining Application-layer checks (FastAPI size limits), Framework-layer checks (RQ Timeouts), and OS-layer sandboxing (Linux `setrlimit`), Confoundr safely executes untrusted statistical payloads without risking the stability or security of the core API.
