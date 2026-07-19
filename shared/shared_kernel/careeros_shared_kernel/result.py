"""A minimal ``Result``/``Either`` type for explicit success/failure values.

Domain and application code returns a ``Result`` instead of raising for expected
failures, keeping control flow explicit and typed. ``Ok`` carries a success
value; ``Err`` carries an error value. Combinators (``map`` etc.) are
intentionally omitted until a real use case needs them (no premature
abstraction).
"""

from dataclasses import dataclass
from typing import Never


class UnwrapError(Exception):
    """Raised when a ``Result`` is unwrapped on the wrong variant."""


@dataclass(frozen=True, slots=True)
class Ok[T]:
    value: T

    def is_ok(self) -> bool:
        return True

    def is_err(self) -> bool:
        return False

    def unwrap(self) -> T:
        return self.value

    def unwrap_err(self) -> Never:
        raise UnwrapError("Called unwrap_err on an Ok value")

    def unwrap_or[U](self, default: U) -> T:
        return self.value


@dataclass(frozen=True, slots=True)
class Err[E]:
    error: E

    def is_ok(self) -> bool:
        return False

    def is_err(self) -> bool:
        return True

    def unwrap(self) -> Never:
        raise UnwrapError("Called unwrap on an Err value")

    def unwrap_err(self) -> E:
        return self.error

    def unwrap_or[U](self, default: U) -> U:
        return default


type Result[T, E] = Ok[T] | Err[E]
