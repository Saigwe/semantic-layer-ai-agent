import json
from types import SimpleNamespace

import duckdb
import pytest

from agent.agent import OUT_OF_SCOPE, ask
from agent.query import build_sql, run_metric
from agent.tools import execute, tool_definitions
from evals.run_evals import is_correct


@pytest.fixture
def db(tmp_path):
    path = tmp_path / "saas.duckdb"
    with duckdb.connect(str(path)) as con:
        con.execute("""create table mrr_summary_monthly as select * from (values
            (date '2026-08-01', 1000.0, 50.0, 0.0, 20.0, -10.0, -30.0, 1030.0, 9, 1, 10.0),
            (date '2026-09-01', 1030.0, 0.0, 0.0, 10.0, 0.0, -100.0, 940.0, 8, 1, 11.1)
        ) t(month, opening_mrr, new_mrr, reactivation_mrr, expansion_mrr, contraction_mrr, churned_mrr,
            closing_mrr, paying_accounts, churned_accounts, logo_churn_rate_pct)""")
        con.execute("""create table dim_accounts as select * from (values
            (1, 'enterprise', 'PT', 900.0, true), (2, 'smb', 'PT', 40.0, true), (3, 'smb', 'UK', 0.0, false)
        ) t(account_id, segment, country, current_mrr, is_active)""")
    return path


def test_monthly_metric_with_range(db):
    result = run_metric("closing_mrr", "2026-09", "2026-09", None, db)
    assert result.rows == [{"month": "2026-09-01", "value": 940.0}]
    assert result.params == ["2026-09-01", "2026-09-01"]


def test_expression_metric_and_filters(db):
    assert run_metric("net_new_mrr", "2026-08", "2026-08", None, db).rows[0]["value"] == 30.0
    assert run_metric("active_accounts", None, None, {"segment": "SMB", "country": None}, db).rows[0]["value"] == 1.0
    assert run_metric("current_mrr_by_account_total", None, None, {"segment": None, "country": "pt"},
                      db).rows[0]["value"] == 940.0


def test_values_are_bound_not_interpolated():
    sql, params = build_sql("active_accounts", filters={"segment": "smb'; drop table x; --", "country": None})
    assert "drop table" not in sql
    assert params == ["smb'; drop table x; --"]


def test_bad_inputs_become_tool_errors(db):
    audit = []
    assert execute("query_metric", {"metric": "made_up"}, audit, db)[1] is True
    text, is_error = execute("query_metric", {"metric": "closing_mrr", "start_month": "Sept", "end_month": None,
                                              "filters": None}, audit, db)
    assert is_error and "YYYY-MM" in text
    assert execute("query_metric", {"metric": "active_accounts", "start_month": None, "end_month": None,
                                    "filters": {"plan": "growth"}}, audit, db)[1] is True


def test_tool_schemas_are_strict():
    for tool in tool_definitions():
        assert tool["strict"] is True
        assert tool["input_schema"]["additionalProperties"] is False


def test_agent_loop_runs_tools_and_returns_answer(db):
    responses = [
        SimpleNamespace(stop_reason="tool_use", content=[
            SimpleNamespace(type="tool_use", id="t1", name="query_metric",
                            input={"metric": "closing_mrr", "start_month": "2026-09", "end_month": "2026-09",
                                   "filters": {"segment": None, "country": None}})]),
        SimpleNamespace(stop_reason="end_turn", content=[
            SimpleNamespace(type="text", text="Closing MRR in September 2026 was 940.")]),
    ]
    sent = []

    def create(**kwargs):
        sent.append(kwargs["messages"][-1])
        return responses.pop(0)

    fake = SimpleNamespace(beta=SimpleNamespace(messages=SimpleNamespace(create=create)))
    answer = ask("What was closing MRR in September 2026?", client=fake, db_path=db)

    assert answer.text == "Closing MRR in September 2026 was 940."
    assert answer.queries[0]["metric"] == "closing_mrr"
    tool_result = sent[1]["content"][0]
    assert tool_result["tool_use_id"] == "t1" and json.loads(tool_result["content"])["rows"][0]["value"] == 940.0


def test_eval_grading():
    assert is_correct("Closing MRR was 380,979.00 in September.", {}, 380979.0)
    assert is_correct("Churn removed -18,807 of MRR.", {}, -18807.0)
    assert not is_correct("It was about 400,000.", {}, 380979.0)
    assert is_correct(f"{OUT_OF_SCOPE} Available metrics: ...", {"answerable": False}, None)
