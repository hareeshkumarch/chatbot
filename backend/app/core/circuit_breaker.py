import time
from collections.abc import Awaitable, Callable
from enum import Enum
from typing import TypeVar

T = TypeVar("T")


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreakerOpenError(Exception):
    pass


class CircuitBreaker:
    def __init__(self, name: str, failure_threshold: int = 5, reset_timeout: float = 30.0, half_open_max_calls: int = 1):
        self.name = name
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.half_open_max_calls = half_open_max_calls
        self.failure_count = 0
        self.state = CircuitState.CLOSED
        self.opened_at: float | None = None
        self.half_open_calls = 0

    def _maybe_half_open(self) -> None:
        if self.state == CircuitState.OPEN and self.opened_at is not None and time.monotonic() - self.opened_at >= self.reset_timeout:
            self.state = CircuitState.HALF_OPEN
            self.half_open_calls = 0

    def check(self) -> None:
        self._maybe_half_open()
        if self.state == CircuitState.OPEN:
            raise CircuitBreakerOpenError(f"{self.name} circuit open")
        if self.state == CircuitState.HALF_OPEN and self.half_open_calls >= self.half_open_max_calls:
            raise CircuitBreakerOpenError(f"{self.name} circuit half-open limit reached")
        if self.state == CircuitState.HALF_OPEN:
            self.half_open_calls += 1

    def record_success(self) -> None:
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def record_failure(self) -> None:
        self.failure_count += 1
        if self.state == CircuitState.HALF_OPEN or self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            self.opened_at = time.monotonic()

    async def call(self, func: Callable[..., Awaitable[T]], *args, **kwargs) -> T:
        self.check()
        try:
            result = await func(*args, **kwargs)
        except Exception:
            self.record_failure()
            raise
        else:
            self.record_success()
            return result


_registry: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(name: str) -> CircuitBreaker:
    if name not in _registry:
        _registry[name] = CircuitBreaker(name=name)
    return _registry[name]
