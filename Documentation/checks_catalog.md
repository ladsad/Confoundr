# Confoundr Check Catalog

The core library consists of multiple checks to evaluate causal validity assumptions. Each check is a self-contained plugin.

## Current Checks (v0.1 Target)

| Check | What it catches | Method |
|---|---|---|
| **Leakage detector** | Feature computed after the outcome window closes | Timestamp/window comparison between feature and target |
| **Confounder audit** | Suspected omitted variables biasing the treatment effect | Correlation scan + user-supplied domain variable list |
| **Positivity check** | Treatment/control groups don't overlap in propensity | Propensity score estimation + overlap histogram |

## Planned Checks (v0.2+)

| Check | What it catches | Method | Target Version |
|---|---|---|---|
| **Selection bias diagnostics** | Non-representative training population | Standardized mean differences, balance tables | v0.2+ |
| **SUTVA violation flags** | Treatment spillover between units | Network/cluster structure heuristics | v0.3+ |
| **Instrument validity** | Weak or invalid instrumental variables | First-stage F-statistic, exclusion restriction heuristics | v0.3+ |

## Plugin Interface Requirements
Checks implement a standard interface to ensure modularity:
- **Input**: Dataframe and configuration YAML/dict.
- **Output**: Pass/Fail status, structured evidence, and human-readable explanation.
