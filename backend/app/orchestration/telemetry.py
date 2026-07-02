from dataclasses import dataclass


@dataclass
class LLMCallRecord:
    task: str
    provider: str | None
    model: str | None
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


def record_llm_call(
    calls: list[dict],
    task: str,
    provider: str | None,
    model: str | None,
    prompt_tokens: int,
    completion_tokens: int,
) -> list[dict]:
    prompt = max(0, int(prompt_tokens or 0))
    completion = max(0, int(completion_tokens or 0))
    entry = LLMCallRecord(
        task=task,
        provider=provider,
        model=model,
        prompt_tokens=prompt,
        completion_tokens=completion,
        total_tokens=prompt + completion,
    )
    return [*calls, entry.__dict__]
