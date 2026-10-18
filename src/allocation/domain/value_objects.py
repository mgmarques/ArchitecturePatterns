from dataclasses import dataclass
from functools import total_ordering
from collections import namedtuple
from typing import NamedTuple
from typing import Union


class Name(NamedTuple):
    first_name: str
    surname: str

Line = namedtuple('Line', ['sku', 'qty'])


@ total_ordering
@dataclass(frozen=True)
class Money:
    currency: str
    value: float  # Changed to float to support division safely

    def __add__(self, other: "Money") -> "Money":
        """Adds two Money objects of the same currency."""
        if not isinstance(other, Money):
            return NotImplemented
        self._ensure_same_currency(other)
        return Money(self.currency, self.value + other.value)

    def __sub__(self, other: "Money") -> "Money":
        """Subtracts a Money object from another of the same currency."""
        if not isinstance(other, Money):
            return NotImplemented
        self._ensure_same_currency(other)
        return Money(self.currency, self.value - other.value)

    def __mul__(self, other: Union[int, float]) -> "Money":
        """Multiplies Money by a scalar number (e.g., doubling a price)."""
        if not isinstance(other, (int, float)):
            return NotImplemented
        return Money(self.currency, self.value * other)

    def __rmul__(self, other: Union[int, float]) -> "Money":
        """Supports reverse multiplication (e.g., 2 * fiver)."""
        return self.__mul__(other)

    def __truediv__(self, other: Union[int, float]) -> "Money":
        """Divides Money by a scalar number (e.g., splitting a bill)."""
        if not isinstance(other, (int, float)):
            return NotImplemented
        if other == 0:
            raise ZeroDivisionError("Cannot divide money by zero.")
        return Money(self.currency, self.value / other)

    def _ensure_same_currency(self, other: "Money"):
        """Helper to enforce Domain-Driven Design rules."""
        if not isinstance(other, Money):
            return NotImplemented
        if self.currency != other.currency:
            raise ValueError(
                f"Currency mismatch: Cannot compare {self.currency} and {other.currency}"
            )

    def __lt__(self, other: "Money") -> bool:
        """Implements the less-than (<) operator."""
        self._ensure_same_currency(other)
        return self.value < other.value

    def __eq__(self, other: object) -> bool:
        """Implements equality (==). Dataclasses do this automatically,

        but we override it to handle type safety safely."""
        if not isinstance(other, Money):
            return NotImplemented
        return self.currency == other.currency and self.value == other.value
