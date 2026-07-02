from app.analytics.tracker import estimate_cost_usd, summarize_llm_calls, token_totals


def test_summarize_llm_calls_sums_every_call():
    calls = [
        {"task": "query_planning", "provider": "groq", "model": "x", "prompt_tokens": 120, "completion_tokens": 30},
        {"task": "synthesis", "provider": "anthropic", "model": "y", "prompt_tokens": 800, "completion_tokens": 220},
        {"task": "verification", "provider": "groq", "model": "x", "prompt_tokens": 400, "completion_tokens": 12},
    ]
    prompt, completion, cost = summarize_llm_calls(calls)
    assert prompt == 1320
    assert completion == 262
    assert cost > 0


def test_summarize_llm_calls_ignores_invalid_values():
    calls = [{"task": "x", "provider": "openai", "prompt_tokens": -5, "completion_tokens": None}]
    prompt, completion, _ = summarize_llm_calls(calls)
    assert prompt == 0
    assert completion == 0


def test_token_totals_returns_total():
    calls = [{"task": "x", "provider": "openai", "prompt_tokens": 10, "completion_tokens": 5}]
    assert token_totals(calls) == (10, 5, 15)


def test_estimate_cost_usd_unknown_provider_is_zero():
    assert estimate_cost_usd("unknown", 1000, 1000) == 0.0
