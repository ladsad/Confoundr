# Confoundr — Project Plan
*A causal validity linter for ML pipelines, plus a deployed platform that runs it as a service*

> Working name: **Confoundr**. Swap for `causalcheck`, `assumptr`, or anything else before you register the PyPI package / domain — do this early so the name is locked before you build outward-facing docs around it.

---

## 1. Elevator pitch

Data quality tools (Great Expectations, Evidently AI, Feast validations) check whether your data is *clean* — nulls, schema drift, distribution shift. None of them check whether your data is *causally valid* — whether the assumptions your causal or treatment-effect model depends on (no leakage, no unmeasured confounding, positivity, balanced treatment groups) actually hold. Teams find this out the hard way, in production, after a causal model has already driven a bad business decision.

Confoundr is an open-source library that runs a battery of causal-validity checks against a dataframe, feature store, or pipeline stage, explains failures in plain language, and — as a hosted platform — lets a team plug in a dataset and get those diagnostics without writing any code, on a schedule, with alerts.

---

## 2. Goals and non-goals

**Goals**
- Fill a real, nameable gap in the OSS data/ML tooling ecosystem (causal validity, not data quality)
- Be genuinely adoptable: pip-installable, plugin-based, PR-friendly
- Demonstrate depth across the full stack: distributed job processing, multi-tenant service design, observability, security — not just a model or a notebook
- Produce artifacts you can point to independently: the library, the platform, a benchmark/eval writeup, and (optionally) a working paper
- Stay ongoing — designed so v2, v3, v4 are obvious extensions rather than a finished, closed thing

**Non-goals (at least for v1)**
- Not trying to replace Great Expectations or Feast — integrates alongside them, doesn't compete on general data quality
- Not building a general-purpose ML platform — scope is specifically causal/treatment-effect validity
- Not optimizing for enterprise-grade auth/billing on day one — multi-tenancy needs to exist, but "real SaaS business" polish is not the goal

---

## 3. Two-layer architecture

**Layer 1 — Core library** (`confoundr` pip package)
Standalone, dependency-light, usable in anyone's pipeline or CI without touching your platform at all. This is the part that earns stars and pull requests.

**Layer 2 — Deployed platform**
A service that wraps Layer 1: upload or connect a dataset, run checks asynchronously, see results on a dashboard, get alerted on regressions. This is the part that proves systems engineering, not just Python.

Keeping these separate is itself a design decision worth stating explicitly in your README and in interviews — it means the core logic is portable and testable independently of the service layer.

---

## 4. Core library — check catalog (v0.1 target: 3 checks, expand later)

| Check | What it catches | Method |
|---|---|---|
| Leakage detector | Feature computed after the outcome window closes | Timestamp/window comparison between feature and target |
| Confounder audit | Suspected omitted variables biasing the treatment effect | Correlation scan + user-supplied domain variable list |
| Positivity check | Treatment/control groups don't overlap in propensity | Propensity score estimation + overlap histogram |
| *(v0.2+)* Selection bias diagnostics | Non-representative training population | Standardized mean differences, balance tables |
| *(v0.3+)* SUTVA violation flags | Treatment spillover between units | Network/cluster structure heuristics |
| *(v0.3+)* Instrument validity | Weak or invalid instrumental variables | First-stage F-statistic, exclusion restriction heuristics |

Each check implements a common plugin interface (input: dataframe + config, output: pass/fail + evidence + human-readable explanation) so new checks are a self-contained, low-effort contribution — this is what makes the project PR-friendly.

---

## 5. Platform architecture

```
Upload / connect source → API layer (auth, job submission)
                              → Job queue (Redis)
                                  → Worker pool (runs core library checks)
                                      → Storage (Postgres metadata + object storage for datasets/reports)
                                          → Dashboard (insights, history, alerts)
```

Cross-cutting concerns layered on top once the core flow works: observability (queue depth, job success rate, per-check latency), multi-tenant data isolation, and sandboxed execution for untrusted uploaded data.

---

## 6. Zero-budget tech stack

| Component | Choice | Why |
|---|---|---|
| Core library | Python, pandas, statsmodels/scikit-learn | No cost, matches your existing stack |
| API | FastAPI | You already know it (Koch, NatWest framing) |
| Job queue | Redis via Upstash free tier | Managed, no server to babysit |
| Worker | Python worker process(es) in Docker, `arq` or `rq` for the queue client | Simple async job pattern, no need for full Celery complexity at v1 |
| Metadata DB | Postgres via Supabase free tier | Free, includes auth if you want it later |
| Object storage | Supabase storage free tier | Free tier, integrates with the same project as the DB |
| Frontend | Next.js on Vercel | You already know this from Pitwall |
| LLM (explainer layer) | Groq free tier or local Ollama | No per-token billing |
| Observability | Prometheus + Grafana, self-hosted in Docker Compose, or Grafana Cloud free tier | Free, and genuinely differentiating — most portfolios skip this |
| CI/CD | GitHub Actions free tier | You already use this on CodeWhisper and Pitwall |
| Hosting (API + workers) | Fly.io or Render free tier | Both support multi-service deploys without a card commitment issue for hobby tiers |

---

## 7. Roadmap

### Phase 0 — Foundations (weeks 1–2)
- [ ] Lock the name, register PyPI package name and GitHub repo
- [ ] Write the plugin interface contract (input/output schema for a check)
- [ ] Implement leakage detector against a synthetic dataset with known leakage
- [ ] Unit tests + GitHub Actions CI running on every push

### Phase 1 — Core library v0.1 (weeks 3–5)
- [ ] Confounder audit + positivity check implemented
- [ ] CLI (`confoundr check data.csv --config checks.yaml`)
- [ ] Curate 3–5 synthetic "known-bad" datasets (deliberate leakage, deliberate confounding) as a first benchmark
- [ ] Publish to PyPI, write a README with a clear before/after example
- [ ] Post to r/MachineLearning or the causal inference community once it runs cleanly on someone else's machine

### Phase 2 — Service MVP (weeks 6–8)
- [ ] FastAPI endpoint wrapping the library, synchronous, single dataset upload
- [ ] Dockerize API + library
- [ ] Deploy to Fly.io/Render free tier — get a real URL working end to end

### Phase 3 — Async + distributed processing (weeks 9–12)
- [ ] Add Redis-backed job queue
- [ ] Separate worker process(es) pulling jobs
- [ ] Job status model: `queued → running → succeeded/failed`, retry with backoff, dead-letter handling for jobs that fail repeatedly
- [ ] Webhook or polling endpoint for job completion

### Phase 4 — Persistence + multi-tenancy (weeks 13–15)
- [ ] Postgres schema: users, datasets, check runs, results, history
- [ ] Per-user data isolation (object storage paths scoped per user, row-level access checks)
- [ ] Basic auth (Supabase Auth or a simple JWT flow)

### Phase 5 — Observability (weeks 16–17)
- [ ] Prometheus metrics: queue depth, job success/failure rate, per-check latency
- [ ] Grafana dashboard for the above
- [ ] Alerting on stuck queues or elevated failure rates

### Phase 6 — Agent explainer layer (weeks 18–20)
- [ ] Wire failed checks into an LLM call (Groq/Ollama) that explains root cause + suggests a fix in plain language
- [ ] Evaluate explanation quality against a hand-labeled set of failure cases (reuse your CodeWhisper A/B evaluation habits)

### Phase 7 — Security hardening (weeks 21–23)
- [ ] Resource-limited, ephemeral execution for checks running on uploaded (untrusted) data — CPU/memory/time caps at minimum, sandboxed containers if you want to go further
- [ ] Document the threat model and the mitigation explicitly — this write-up is itself a portfolio artifact

### Phase 8 — Dashboard (weeks 24–26)
- [ ] Next.js frontend: upload flow, run history, results view, basic alert configuration
- [ ] Deliberately last — least differentiating part of the system, most people expect it, so it should not be where your time goes first

### Ongoing (no end date)
- [ ] Expand check catalog (SUTVA, instrument validity, more domain-specific checks)
- [ ] PySpark support for large datasets processed by workers
- [ ] Feast integration (validate features directly inside an existing feature store)
- [ ] Accept community PRs for new checks
- [ ] Working paper on the benchmark methodology, published the same way as your ArtResGAN and RHN papers

---

## 8. Success metrics

| Metric | Target |
|---|---|
| Core library detection rate on synthetic benchmark | Report precision/recall explicitly, don't just claim "it works" |
| GitHub stars / forks (library repo) | Track monthly, don't obsess early — first external contributor matters more than star count |
| End-to-end platform uptime on free-tier hosting | Document honestly; free tiers sleep/cold-start, that's a real constraint worth writing about |
| Job queue behavior under load | Load-test with a synthetic burst of uploads, report p95 latency and failure rate |
| First external pull request | This is the real adoption signal — treat it as a milestone |

---

## 9. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Scope creep — platform work crowds out the library that's actually the differentiator | Keep Phase 0–1 (library) shippable and public before touching the service layer at all |
| Free-tier hosting limitations (cold starts, sleep, storage caps) | Document these constraints openly in the README rather than hiding them — shows engineering maturity |
| Nobody notices the OSS release | Post to the right niche communities (causal inference, MLOps) rather than broad ones; a clear before/after example matters more than marketing |
| Untrusted user data execution becomes a real security hole | Treat Phase 7 as non-optional before accepting real external uploads, even in a demo |
| Long-term motivation dips on an "ongoing" project with no deadline | Time-box each phase (as above) so there's always a near-term shippable milestone, not just an open-ended backlog |

---

## 10. How this maps back to your resume

- **Distributed systems / backend depth** → job queue design, retry/backoff, worker scaling, multi-tenant isolation (a gap your current resume doesn't cover — everything else leans on managed cloud services)
- **Data engineering** → benchmark dataset curation, large-dataset processing path (PySpark integration), same rigor as Mustard Archives
- **ML / causal inference** → directly extends Churn HTE into a generalized, reusable tool instead of a one-off project
- **Agentic AI** → the explainer layer, self-built rather than framework-integrated, unlike your internship framing which always says "integrated LangChain/Bedrock"
- **Evaluation rigor** → benchmark precision/recall, explanation quality evaluation, same discipline as CodeWhisper's A/B testing
- **Production/observability** → Prometheus/Grafana, a genuinely new category for your portfolio
- **Open source leadership** → maintaining a plugin ecosystem, reviewing external PRs, is a very different signal than solo project ownership

---

## 11. Immediate next steps (this week)

1. Pick the final name, register the GitHub repo and PyPI package name
2. Write the plugin interface as a Python `Protocol` or abstract base class — get this contract right before writing a single check, since every check and every future contributor depends on it
3. Build one synthetic dataset with deliberate, known leakage
4. Implement the leakage detector against it, with a passing test
5. Push it, get CI green, and you have a real v0.0 to iterate on
