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
- [Project Plan](Documentation/confoundr_project_plan.md)
