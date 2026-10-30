"""Build and run parameterised SQL from catalogue entries only.

The model chooses a metric name and parameter values. Table names and expressions come from metrics.yml, and every
value is bound as a parameter, so the model cannot inject SQL.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

import duckdb

from .catalogue import get_metric, load_catalogue

DEFAULT_DB = Path(__file__).resolve().parents[2] / "03-dbt-saas-metrics" / "target" / "saas.duckdb"
MONTH = re.compile(r"^\d{4}-\d{2}(-01)?$")


@dataclass(frozen=True)
class QueryResult:
    metric: str
    definition: str
    sql: str
    params: list
    rows: list[dict]


def _month(value: str | None) -> str | None:
    if value is None:
        return None
    if not MONTH.match(value):
        raise ValueError(f"Month must look like YYYY-MM, got '{value}'")
    return value if len(value) == 10 else f"{value}-01"


def build_sql(metric_name: str, start_month: str | None = None, end_month: str | None = None,
              filters: dict | None = None, catalogue: dict | None = None) -> tuple[str, list]:
    m = get_metric(metric_name, catalogue)
    params: list = []
    if m["grain"] == "month":
        where = []
        if (start := _month(start_month)):
            where.append("month >= cast(? as date)")
            params.append(start)
        if (end := _month(end_month)):
            where.append("month <= cast(? as date)")
            params.append(end)
        sql = f"select month, {m['expression']} as value from {m['model']}"
        sql += (" where " + " and ".join(where)) if where else ""
        return sql + " order by month", params

    allowed = set(m.get("filters", []))
    where = []
    for key, value in sorted((filters or {}).items()):
        if value is None:
            continue
        if key not in allowed:
            raise ValueError(f"Filter '{key}' is not allowed for {metric_name}. Allowed: {sorted(allowed)}")
        where.append(f"{key} = ?")
        params.append(value.lower() if key == "segment" else value.upper())
    sql = f"select {m['expression']} as value from {m['model']}"
    return sql + ((" where " + " and ".join(where)) if where else ""), params


def run_metric(metric_name: str, start_month=None, end_month=None, filters=None,
               db_path: str | Path | None = None) -> QueryResult:
    catalogue = load_catalogue()
    sql, params = build_sql(metric_name, start_month, end_month, filters, catalogue)
    path = Path(db_path or os.environ.get("AGENT_DB_PATH", DEFAULT_DB))
    with duckdb.connect(str(path), read_only=True) as con:
        rel = con.execute(sql, params)
        cols = [d[0] for d in rel.description]
        rows = [{c: (str(v) if c == "month" else float(v) if v is not None else None) for c, v in zip(cols, r)}
                for r in rel.fetchall()]
    return QueryResult(metric_name, catalogue[metric_name]["description"], sql, params, rows)
