"""Claude agent that answers business questions only through governed metrics.

Usage: python -m agent.agent "What was net new MRR in June 2026?"
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field

import anthropic

from .tools import execute, tool_definitions

MODEL = "claude-opus-5-5"
OUT_OF_SCOPE = "I can't answer that from the governed metrics."
MAX_TURNS = 8

SYSTEM_PROMPT = f"""You answer questions about a B2B SaaS company's revenue and customers for business \
stakeholders.

You can only use the list_metrics and query_metric tools. Every number in your answer must come from a tool \
result in this conversation; never estimate or calculate figures the tools did not return, except simple \
arithmetic on returned values (sums, differences, averages), which you must say you did.

If no governed metric covers the question, reply exactly: "{OUT_OF_SCOPE}" and then name the metrics that are \
available.

Answer in two or three sentences. Name the metric you used and its definition, and give the month or filter the \
figure applies to."""


@dataclass
class AgentAnswer:
    text: str
    queries: list[dict] = field(default_factory=list)
    turns: int = 0


def ask(question: str, client: anthropic.Anthropic | None = None, db_path=None) -> AgentAnswer:
    client = client or anthropic.Anthropic()
    tools = tool_definitions()
    messages: list[dict] = [{"role": "user", "content": question}]
    audit: list[dict] = []

    for turn in range(1, MAX_TURNS + 1):
        response = client.beta.messages.create(
            model=MODEL,
            max_tokens=16000,
            output_config={"effort": "medium"},
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            system=SYSTEM_PROMPT,
            tools=tools,
            messages=messages,
        )
        if response.stop_reason == "refusal":
            return AgentAnswer("The model declined to answer this question.", audit, turn)
        # Keep the full content (thinking, fallback and tool_use blocks) so the history stays valid.
        messages.append({"role": "assistant", "content": response.content})

        tool_calls = [b for b in response.content if b.type == "tool_use"]
        if response.stop_reason != "tool_use" or not tool_calls:
            text = "".join(b.text for b in response.content if b.type == "text").strip()
            return AgentAnswer(text, audit, turn)

        results = []
        for call in tool_calls:
            content, is_error = execute(call.name, call.input, audit, db_path)
            results.append({"type": "tool_result", "tool_use_id": call.id, "content": content, "is_error": is_error})
        messages.append({"role": "user", "content": results})  # all results in one message

    return AgentAnswer("Stopped: too many tool calls without an answer.", audit, MAX_TURNS)


def main() -> int:
    if len(sys.argv) < 2:
        print('Usage: python -m agent.agent "your question"')
        return 2
    answer = ask(" ".join(sys.argv[1:]))
    print(answer.text)
    for q in answer.queries:
        print(f"\n[{q['metric']}] {q['sql']}  params={q['params']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
