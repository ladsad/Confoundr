<div align="center">
  <h1>🔍 Confoundr</h1>
  <p><em>A causal validity linter for ML pipelines, plus a deployed platform that runs it as a service.</em></p>
  
  [![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
  [![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
  [![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](http://makeapullrequest.com)
</div>

<hr/>

## 📖 Overview

Data quality tools (like Great Expectations, Evidently AI, or Feast) check whether your data is *clean* (nulls, schema drift, distribution shift). They **do not** check whether your data is *causally valid* — whether the assumptions your causal or treatment-effect model depends on (no leakage, no unmeasured confounding, positivity, balanced treatment groups) actually hold.

**Confoundr** fills this gap. It is an open-source library that runs a battery of causal-validity checks against a dataframe, feature store, or pipeline stage, explains failures in plain language, and — as a hosted platform — lets a team plug in a dataset and get those diagnostics without writing any code, on a schedule, with alerts.

## ✨ Features

- **🛡️ Causal Linting:** Automated checks for target leakage, unmeasured confounding, and positivity violations.
- **🤖 AI-Powered Explanations:** Get plain-language explanations of complex causal failures.
- **🌐 Deployed Platform:** Plug-and-play multi-tenant service for continuous async dataset checks.
- **📊 Observability:** Production-ready metrics exposed natively for Prometheus and Grafana.

## 🚀 Quick Start

### Installation

Install via pip:

```bash
pip install confoundr
```

### 💻 CLI Usage

You can run Confoundr directly on a CSV dataset using the terminal:

```bash
confoundr check dataset.csv --target target_col --treatment treatment_col
```

**Output:**

```text
--- Confoundr Diagnostics ---
========================================
[FAIL] Target Leakage Detector
   Found 1 features with suspiciously high correlation (> 0.9) to the target 'target_col', which may indicate target leakage. Leaky features: target_proxy (0.9979)

[PASS] Confounder Audit
   No strong measured confounders found (threshold > 0.2).

[WARN] Positivity (Overlap) Check
   Severe positivity violation. The propensity score distributions for treated and control groups have virtually no overlap (overlap ratio: 1.20%).
```

### 🐍 Python API

Integrate Confoundr seamlessly into your existing pipelines:

```python
import pandas as pd
from confoundr import CheckContext
from confoundr.checks import TargetLeakageCheck, PositivityCheck

# 1. Load your data
df = pd.read_csv("dataset.csv")

# 2. Define the evaluation context
context = CheckContext(df=df, target_col="target", treatment_col="treatment")

# 3. Run individual checks
leakage_result = TargetLeakageCheck().run(context)

print(f"Status: {leakage_result.status}")
print(f"Details: {leakage_result.explanation}")
```

## 🏗️ Architecture

Confoundr is built as a two-layer system:

1. **Core Library (`confoundr`)**: Standalone, dependency-light, pip-installable package usable in any pipeline or CI environment.
2. **Deployed Platform**: A scalable service built with **FastAPI, Redis Queue, PostgreSQL, and Groq**.

### ☁️ Hosted Platform API

Confoundr includes an out-of-the-box cloud deployment wrapper:

- **Async Processing:** Submit datasets to `/api/v1/async-check`. The heavy statistical processing is handed off to a background Redis worker.
- **AI Explainer Layer:** If a causal check fails, the worker seamlessly triggers a Groq LLM (Llama 3.1) to generate a plain-language explanation and dataset fix.
- **Persistent History:** Every job and its corresponding AI insight is archived in PostgreSQL. View past runs at `/api/v1/history`.
- **Observability:** Metrics (queue depth, job outcomes, execution time) are natively exposed on `/metrics` for Prometheus/Grafana.

## 📚 Documentation

For more in-depth information, check out our detailed guides:

- 🏛️ **[Architecture Overview](Documentation/architecture.md)**
- 📋 **[Check Catalog](Documentation/checks_catalog.md)**

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
