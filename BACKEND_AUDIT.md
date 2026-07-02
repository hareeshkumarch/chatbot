# Backend Audit — Enterprise AI Platform

A grounded review of the core request path, the ways it can break, what it already handles well, and what to improve. Every point below is based on the actual code, not assumptions.

## 1. How the core works (request lifecycle)

A chat turn flows through `ChatOrchestrator.run_turn` (an async generator that yields SSE events):

1. **Conversation + history** — gets or creates the conversation, loads recent history, records the user message, emits a `start` event.
2. **Active connectors** — `build_active_connectors` loads the tenant's connected sources and instantiates them (SQL connector separated from the rest).
3. **Retrieval graph** (`retrieval_graph.ainvoke`) — a LangGraph pipeline:
   - **plan** — an LLM classifies the query into 1–3 capability steps using a lightweight delimited format (`capability:parameter;capability:parameter`).
   - **execute_plan** — runs all plan steps **concurrently** via `asyncio.gather`, dispatching each capability (`document_qa`, `sql_data`, `connector_action`, `web_search`, `news`, `places`, `trends`, `finance`, `demographics`) to its step function.
   - **synthesize** — composes an answer from the step results.
4. **Streaming synthesis** — `stream_with_fallback` streams tokens from the first healthy provider, accumulating full text, provider/model, and token counts.
5. **Grounding check** — `check_grounding` compares the answer against the retrieved context via a verification LLM call and returns a `verified` flag.
6. **Persistence + telemetry** — records the assistant message, logs the query (plan, strategy, chunk count, confidence, cost, latency), emits a `done` event with the full trace.

The routing intelligence lives in `ModelRouter`: a per-task fallback chain (`TASK_ROUTING_TABLE`) picks providers in preference order, skipping any whose circuit breaker is open, with per-task default temperatures.

## 2. What is already handled well

- **Graceful step degradation.** Every step function in `steps.py` wraps its work in try/except and returns a `StepResult` with an `error` string instead of throwing. One failing source never takes down the whole turn — the synthesizer just works with whatever succeeded.
- **Provider fallback + circuit breakers.** `complete_with_fallback` walks the whole chain, catching both `CircuitBreakerOpenError` and generic exceptions, only raising `ProviderUnavailableError` if *every* provider fails. Circuit breakers are correctly wired into the providers (`openai_compatible.py`, `anthropic_provider.py` both call `self.breaker.call`).
- **Streaming fallback correctness.** `stream_with_fallback` only falls back if a provider fails **before the first chunk** (`if started: raise`). This is the right call — you cannot silently swap providers mid-stream without producing garbled output.
- **Plan parsing robustness.** The planner uses a delimited string format, not JSON. Malformed or partial LLM output degrades cleanly: unknown capabilities are dropped, and an empty parse falls back to `document_qa`. `plan_node` also wraps the whole call in try/except with a `document_qa` default. This avoids the classic "LLM returned invalid JSON → 500" failure entirely.
- **SQL read-only guard.** `run_readonly_query` enforces `SELECT`-only, blocks a forbidden-keyword list (`insert|update|delete|drop|alter|truncate|grant|revoke|create|attach|exec`), auto-appends a `LIMIT`, and sets a Postgres `statement_timeout`. Backed by 15 tests in `test_sql_connector_guard.py`.
- **Verification fails open, safely.** If the verification LLM call itself fails, `check_grounding` logs and passes the answer through as unverified rather than blocking the response — the right tradeoff for a non-critical quality signal.
- **Request validation layer.** Declarative Pydantic constraints on chat/connector/report bodies (length caps, non-empty/trimmed, field-count limits, enum formats), centralized in `core/limits.py`, with 24 tests.
- **Query efficiency.** The N+1 in `build_active_connectors` was eliminated with a batched credential fetch; the analytics aggregator merged its two JSON-column scans into one; analytics endpoints bound `days` (1–90) and `limit` (1–200).
- **Encryption at rest.** Connector credentials are Fernet-encrypted (`encrypt_payload`/`decrypt_payload`) before storage.
- **Concurrency is race-free.** `record_llm_call` returns a new list (`[*calls, entry]`) rather than mutating, so the shared `base_calls` passed into concurrent `gather` branches is only ever read. The `updated_calls[len(base_calls):]` reconciliation correctly extracts appended entries. (Verified — this is *not* a bug despite looking like a shared-mutable-state risk at first glance.)

## 3. Where it can break — and severity

### High severity

- **Insecure secret defaults with no production guard.** `config.py` ships `jwt_secret = "change-me"` and `encryption_key = "0" * 44` as defaults, and there is no startup check that these are overridden when `environment != "development"`. If deployed without setting them, JWTs are forgeable and encrypted credentials are trivially decryptable. **This is the most important finding.**
- **SQL guard is keyword/prefix based, not a parser.** The guard blocks obvious mutations, but it is regex-and-prefix logic, not a SQL parser. It does not defend against multi-statement payloads on drivers that allow them, comment-based evasion, or read-side abuse (e.g. a cartesian-join query that scans huge tables within the row limit). The `statement_timeout` and `LIMIT` mitigate impact, but the guard should not be treated as a hard security boundary. A read-only DB role at the connection level is the real defense.

### Medium severity

- **`fetch_content` interpolates the table name directly** — `SELECT * FROM {resource_id}` in `sql_connector.fetch_content`. `resource_id` comes from reflected table names, so it is not user-injected today, but it is an unparameterized identifier interpolation that would become an injection vector the moment the source of `resource_id` changes. Should be quoted/validated against the known table list.
- **SSE disconnect does not cancel upstream work.** If the client drops mid-stream, the generator keeps running (planning, synthesis, verification, DB writes) to completion. Wasted tokens and cost, and no cancellation propagates to the provider calls. Consider honoring request-cancellation to abort the turn.
- **Every connector operation creates and disposes its own engine.** `SQLConnector._engine()` builds a fresh `create_async_engine` per call and disposes it in a `finally`. No pooling reuse across a turn or across turns — under load this is a connection-churn bottleneck. A per-connector cached engine would help.
- **Unbounded fan-out on step parameters.** `plan` caps at `MAX_PLAN_STEPS = 3`, which is good, but each step can trigger external API calls (search, finance, trends) with no per-turn timeout budget. A slow provider on one step delays the whole `gather`. Consider `asyncio.wait_for` per step.

### Lower severity / edge cases

- **History role filtering is silent.** `load_recent_history` keeps only `user`/`assistant` roles; any `system` or tool rows are dropped without note. Fine today, but worth being explicit if roles expand.
- **Verification is a coarse binary.** `check_grounding` returns `True` only if the response starts with `SUPPORTED`. Any other phrasing from the model reads as unverified. This is safe (fails toward "unverified") but can under-report verification on capable models that phrase differently.
- **Confidence can be `None` → coerced to `0.0` in the query log.** A missing confidence is logged as `0.0`, which is indistinguishable from a genuine zero-confidence answer in analytics. Consider logging null distinctly.
- **`_parse_plan` lowercases and matches against a fixed capability set** — if the planner prompt and `CAPABILITIES` set ever drift, valid steps are silently dropped. Keep them in sync (ideally generate the prompt's capability list from the same constant).

## 4. Recommended improvements (priority order)

1. **Add a startup guard** in `config.py` (a Pydantic `model_validator`) that raises if `environment != "development"` and `jwt_secret`/`encryption_key` still hold their defaults. Highest-value, lowest-effort hardening.
2. **Provision SQL connectors with a read-only DB role** and document it, so the application-layer keyword guard is defense-in-depth rather than the sole control. Quote/validate `resource_id` in `fetch_content`.
3. **Honor client cancellation** in `run_turn` so a dropped SSE connection aborts planning/synthesis and stops burning tokens.
4. **Cache the SQLAlchemy engine per connector** instead of building/disposing per query, to remove connection churn under load.
5. **Add per-step timeouts** (`asyncio.wait_for`) inside `execute_plan` so one slow external provider cannot stall the whole parallel batch.
6. **Distinguish null vs zero confidence** in `log_query`, and consider a richer verification signal than a binary prefix match (e.g. SUPPORTED / PARTIAL / UNSUPPORTED).

## 5. What is genuinely solid and should not be "fixed"

The graph-based orchestration with graceful per-step degradation, the provider fallback + circuit-breaker layer, the stream-fallback-before-first-chunk rule, the delimited (non-JSON) plan format, and the fail-open verification are all sound, deliberate designs. The recent validation layer and query-efficiency work close the most common input-abuse and N+1 gaps. The core is in good shape; the priority items above are about hardening secrets and the SQL boundary, plus operational efficiency under load — not about reworking the architecture.
