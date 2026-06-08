# Agent Evaluation Framework (MVP)

A lightweight Python-based evaluation framework for gating model deployments in CI/CD. It compares a production baseline agent against a candidate branch using a fixed JSONL evaluation dataset, deterministic judgment, and configurable deploy rules.

## Repository structure

- `app/`
  - `agent.py` — common agent interface definition.
  - `baseline_agent.py` — mock baseline agent implementation.
  - `candidate_agent.py` — mock candidate agent implementation.
  - `main.py` — minimal FastAPI app stub.
- `evals/`
  - `cases.jsonl` — evaluation dataset with 30 grouped cases.
  - `schemas.py` — Pydantic models for cases, agent outputs, scoring, and compare configuration.
  - `judge.py` — heuristic judge logic with optional LLM judge placeholder.
  - `compare.py` — deployment gating rules and score comparison logic.
  - `report.py` — HTML report generator.
  - `run_eval.py` — main runner that executes baseline and candidate evaluations, judges outputs, compares results, and writes artifacts.
- `tests/`
  - `test_eval_runner.py` — runner and case loading tests.
  - `test_compare.py` — comparison and gating tests.
- `.github/workflows/eval-gate.yml` — GitHub Actions workflow for CI and eval gating.
- `requirements.txt` — Python dependencies.
- `README.md` — project documentation.

## Methodology

This framework is designed for pre-deployment gating using the following methodology:

1. **Fixed evaluation dataset**
   - Evaluations are defined in `evals/cases.jsonl`.
   - The dataset covers multiple categories: `rag`, `tool`, `multi_step`, `safety`, and `format`.
   - Cases are grouped in sets of three with increasing prompt detail: L1 (high level), L2 (medium), and L3 (detailed bullet-pointed).

2. **Agent interface and execution**
   - Agents implement `run_agent(query: str, case: dict) -> dict`.
   - Outputs include answer text, tool traces, retrieved context, latency, token usage, and error fields.
   - Baseline and candidate agents are currently mock implementations, making the framework easy to extend to real service calls.

3. **Judging**
   - `evals/judge.py` applies deterministic rules by default:
     - non-empty answer
     - valid JSON for format cases
     - expected tool calls are present
     - expected sources appear in retrieved context
   - Optional LLM-based judgment can be enabled later with `ENABLE_LLM_JUDGE=true`.

4. **Comparison and gating**
   - `evals/compare.py` computes overall scores, latency regression, error rates, and critical case checks.
   - Deployment passes only if:
     - candidate score exceeds baseline by a configurable threshold.
     - no critical case failures occur.
     - candidate latency regression is within allowed percentage.
     - candidate error rate does not exceed baseline.
     - critical cases meet a minimum faithfulness threshold.

5. **Reporting**
   - Results are written to `evals/output/`.
   - Artifacts include:
     - `eval_results.json`
     - `eval_summary.json`
     - `regression_cases.csv`
     - `eval_report.html`

## Getting started

1. Install dependencies

```bash
pip install -r requirements.txt
```

2. Run tests

```bash
pytest
```

3. Run the evaluation

```bash
python evals/run_eval.py
```

## CI/CD integration

The workflow in `.github/workflows/eval-gate.yml` runs on `pull_request` and `push` to `main`. It installs dependencies, runs tests, executes the eval runner, and uploads eval artifacts.

## Extending the framework

- Replace `app/baseline_agent.py` and `app/candidate_agent.py` with real agent service calls.
- Enhance `evals/judge.py` with a real LLM judge or stronger deterministic scoring.
- Add Postgres metadata persistence and S3 artifact storage.
- Expand the eval dataset to cover additional categories and edge cases.
