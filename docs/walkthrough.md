# 3-minute walkthrough: Semantic-Layer AI Agent

A timed script for a Loom recording of about 3 minutes (screen plus camera bubble, 1080p). Say it in your own words; the lines are a guide, not a teleprompter.

**Open these tabs before you press record:** README, `metrics.yml`, `agent/query.py`, `agent/tools.py`, `evals/questions.yml`, `tests/`, GitHub Actions.

| Time | On screen | What to say |
|---|---|---|
| 0:00–0:20 | Portfolio card, then the README title | Ask an AI model a business question against raw tables and you get a fluent answer nobody can verify. This Claude agent answers only through governed metrics, and shows the SQL it ran. |
| 0:20–0:40 | README intro | It sits on my dbt SaaS Metrics project, on synthetic data. At McKinsey I worked on governed metrics for executive reporting; this applies the same rule to an AI agent: the definitions come from the semantic layer, not the model. |
| 0:40–1:05 | `metrics.yml` | The catalogue is the semantic layer: 8 metrics, each mapped to a tested mart, with a definition, grain and allowed filters. |
| 1:05–1:35 | `agent/query.py` | The model chooses, the code builds. Claude picks a metric name and parameters; table names come from the catalogue, and every value is a bound parameter, so SQL injection isn't possible. There's a test for it. |
| 1:35–2:05 | `agent/tools.py` | Strict tool schemas keep inputs valid. Bad inputs go back to Claude as errors it can correct. Every answer carries the SQL and parameters it ran, so it can be audited. |
| 2:05–2:30 | README: out-of-scope behaviour | Ask something outside the catalogue, like customer acquisition cost, and it gives a fixed refusal plus the list of metrics it can answer. It doesn't guess. |
| 2:30–2:45 | `evals/questions.yml` | 12 questions: 10 answerable, 2 out of scope. Expected values are computed from the marts with SQL, never from the agent. The loop is tested with a fake client; the live eval needs my API key and is next, so I'm not quoting an accuracy figure yet. |
| 2:45–3:00 | Back to the README top | For a data team, that's AI answers with the same definitions as the dashboards, and an audit trail for every number. Links are under the video. |

## Recording checklist
- Close email, chat and notifications. Zoom the browser to 125% so code is readable.
- Build dbt-saas-metrics first. If you have set an API key, run one question live (`python -m agent.agent "What was net new MRR in June 2026?"`); if not, show the tests and say the live eval is next.
- Keep to one take per section; Loom lets you trim. Aim for 2:45 to 3:10.
- Show real numbers on screen as you say them; never estimate on camera.
- Say "synthetic" out loud when you introduce the data. This is a skills demonstration, not a rebuild of client work.

## After recording
1. Copy the Loom share link.
2. In `README.md`, replace the walkthrough line with `- [x] [3-minute Loom walkthrough](<your Loom link>)` and add the link under the title.
3. Add the link to this project's card on saigwe.github.io.
