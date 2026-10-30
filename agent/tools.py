"""Tool definitions exposed to Claude, and their execution."""
from __future__ import annotations

import json

from .catalogue import load_catalogue
from .query import run_metric


def tool_definitions() -> list[dict]:
    names = sorted(load_catalogue())
    nullable = {"type": ["string", "null"]}
    return [
        {
            "name": "list_metrics",
            "description": "List the governed metrics you can query, with their definitions, grain and allowed filters.",
            "strict": True,
            "input_schema": {"type": "object", "properties": {}, "required": [], "additionalProperties": False},
        },
        {
            "name": "query_metric",
            "description": (
                "Return values for one governed metric. Monthly metrics return one row per month; use start_month "
                "and end_month (YYYY-MM) to limit the range, or null for all months. Total metrics return one value "
                "and accept segment (smb, mid_market, enterprise) and country (PT, ES, UK, DE, PL) filters, or null."
            ),
            "strict": True,
            "input_schema": {
                "type": "object",
                "properties": {
                    "metric": {"type": "string", "enum": names},
                    "start_month": nullable,
                    "end_month": nullable,
                    "filters": {
                        "type": "object",
                        "properties": {"segment": nullable, "country": nullable},
                        "required": ["segment", "country"],
                        "additionalProperties": False,
                    },
                },
                "required": ["metric", "start_month", "end_month", "filters"],
                "additionalProperties": False,
            },
        },
    ]


def execute(name: str, tool_input: dict, audit: list[dict], db_path=None) -> tuple[str, bool]:
    """Run a tool call. Returns (result text, is_error). Every query is appended to `audit`."""
    try:
        if name == "list_metrics":
            catalogue = load_catalogue()
            return json.dumps({k: {"description": v["description"], "grain": v["grain"],
                                   "filters": v.get("filters", [])} for k, v in catalogue.items()}), False
        if name == "query_metric":
            result = run_metric(tool_input["metric"], tool_input.get("start_month"), tool_input.get("end_month"),
                                tool_input.get("filters"), db_path)
            audit.append({"metric": result.metric, "sql": result.sql, "params": result.params})
            return json.dumps({"metric": result.metric, "definition": result.definition, "rows": result.rows}), False
        return f"Unknown tool '{name}'", True
    except (KeyError, ValueError) as exc:
        return f"Error: {exc}", True
