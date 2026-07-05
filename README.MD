# Confoundr

*A causal validity linter for ML pipelines, plus a deployed platform that runs it as a service*

## Overview

Data quality tools (Great Expectations, Evidently AI, Feast validations) check whether your data is *clean* (nulls, schema drift, distribution shift). They do not check whether your data is *causally valid* — whether the assumptions your causal or treatment-effect model depends on (no leakage, no unmeasured confounding, positivity, balanced treatment groups) actually hold.

Confoundr is an open-source library that runs a battery of causal-validity checks against a dataframe, feature store, or pipeline stage, explains failures in plain language, and — as a hosted platform — lets a team plug in a dataset and get those diagnostics without writing any code, on a schedule, with alerts.

## Architecture Highlights

Confoundr is built as a two-layer system:

- **Core Library (`confoundr` pip package)**: Standalone, dependency-light, usable in anyone's pipeline or CI.
- **Deployed Platform**: A multi-tenant service wrapping the core library that runs asynchronous checks on uploaded datasets, with observability and an AI explainer layer.

## Quick Links

- [Architecture](Documentation/architecture.md)
- [Check Catalog](Documentation/checks_catalog.md)

## Quick Start

### Installation
```bash
pip install confoundr
```

### Example Usage (CLI)
You can run Confoundr directly on a CSV dataset using the CLI:

```bash
$ confoundr check dataset.csv --target target_col --treatment treatment_col

--- Confoundr Diagnostics ---
========================================
[FAIL] Target Leakage Detector
   Found 1 features with suspiciously high correlation (> 0.9) to the target 'target_col', which may indicate target leakage. Leaky features: target_proxy (0.9979)

[PASS] Confounder Audit
   No strong measured confounders found (threshold > 0.2).

[WARN] Positivity (Overlap) Check
   Severe positivity violation. The propensity score distributions for treated and control groups have virtually no overlap (overlap ratio: 1.20%).
```

### Example Usage (Python)
```python
import pandas as pd
from confoundr import CheckContext
from confoundr.checks import TargetLeakageCheck, PositivityCheck

df = pd.read_csv("dataset.csv")
context = CheckContext(df=df, target_col="target", treatment_col="treatment")

# Run individual checks
leakage_result = TargetLeakageCheck().run(context)
print(leakage_result.status, leakage_result.explanation)
```

## Hosted Platform API

Confoundr includes an out-of-the-box cloud deployment wrapper (via FastAPI, Redis Queue, PostgreSQL, and Groq).

- **Async Processing:** Submit datasets to `/api/v1/async-check`. The heavy statistical processing is handed off to a background Redis worker.
- **AI Explainer Layer:** If a causal check fails, the worker seamlessly triggers a Groq LLM (Llama 3.1) to generate a plain-language explanation and dataset fix.
- **Persistent History:** Every job and its corresponding AI insight is archived in PostgreSQL. View past runs at `/api/v1/history`.
- **Observability:** Production-ready metrics (queue depth, job outcomes, execution time) are natively exposed on the `/metrics` endpoint for Prometheus and Grafana.
