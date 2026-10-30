# Semantic-Layer AI Agent (scaffold)

> **Status: scaffold.** Structure and interfaces are in place; the steps in the checklist below are still to do.

**Gap it closes:** building AI agents over trusted, governed data, and AI evaluation. Asked for by Xelix,
1Password, Meta, PlayStation, Zendesk and Ashby.

## Goal

Let business users ask plain-English questions ("What was net new MRR in Q2?", "Which segment churns
most?") and get answers computed from the governed metrics in
[dbt-saas-metrics](https://github.com/Saigwe/dbt-saas-metrics), not from free-form SQL written by the model.

The agent can only call a small set of tools over an allow-listed metric catalogue (`metrics.yml`), so
every number traces back to a tested dbt model. An evaluation set measures accuracy.

```mermaid
flowchart LR
    U[Question] --> A[Claude agent]
    A -->|tool: list_metrics| M[metrics.yml catalogue]
    A -->|tool: query_metric(name, filters, grain)| Q[safe SQL builder]
    Q --> D[(dbt-saas-metrics DuckDB)]
    D --> A --> R[Answer + metric definition + SQL used]
    E[evals/questions.yml] --> X[eval runner: accuracy %]
```

## Checklist

- [ ] Build the dbt project and point `AGENT_DB_PATH` at its `target/saas.duckdb`
- [ ] `agent/catalogue.py`: load `metrics.yml`, validate metric names, grains and allowed filters
- [ ] `agent/query.py`: build parameterised SQL only from catalogue entries (no model-written SQL)
- [ ] `agent/agent.py`: Claude tool-use loop (`claude-opus-5-5`) with the two tools; return answer, metric definition and SQL
- [ ] `evals/questions.yml`: 20+ questions with expected answers computed directly from the marts
- [ ] `evals/run_evals.py`: score exact-match accuracy and refusal on out-of-scope questions
- [ ] Tests for the catalogue and SQL builder (no API calls)
- [ ] README: eval results, failure analysis and design trade-offs

## Why tool-restricted

Letting a model write SQL against raw tables gives fluent but unverifiable answers. Restricting it to
catalogue metrics keeps definitions consistent with finance's MRR bridge and makes answers auditable.
