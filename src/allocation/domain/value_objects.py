"""
Whenever we have a business concept that has data but no identity, we often choose to represent it using the Value
Object pattern. A value object is any domain object that is uniquely identified by the data it holds; we usually make
them immutable.

"""
from dataclasses import dataclass
from functools import total_ordering
from collections import namedtuple
from typing import NamedTuple
from typing import Union


class Name(NamedTuple):
    first_name: str
    surname: str

Line = namedtuple('Line', ['sku', 'qty'])

"""
# Implementing Comparisons:
Python allows you to implement these comparisons individually, but the cleanest way is to use the total_ordering 
decorator from the functools module. It automatically fills in the rest of the comparison methods if you provide
 __eq__ and just one inequality method (like __lt__ for less-than).
"""
@ total_ordering
@dataclass(frozen=True)
class Money:
    """
    If your object requires custom mathematical operations, a frozen @dataclass is often cleaner because it does not
    inherit legacy tuple behaviors like concatenation or sequence indexing.

    To perform mathematical addition on Value Objects, you must explicitly define
    * __add__ method to handle the business logic and ensure you can only add matching currencies.
    * __sub__: Triggers when you use the - operator.
    * __mul__: Triggers when you multiply money by a number (fiver * 2).
    * __rmul__: Right-multiplication. Triggers when the number comes first (2 * fiver). Without this, Python wouldn't know how an integer adds to a custom object.
    * __truediv__: Triggers when you use the standard / division operator.

    Since Value Objects should be immutable, each operation checks business logic (e.g., preventing you from mixing
    currencies) and returns a brand new instance.
    """
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
        """Implements equality (==). Dataclasses do this automatically, but we override it to handle type safety safely.

        For both entity and value objects, it’s also worth thinking through how hash will work. It’s the magic method
        Python uses to control the behavior of objects when you add them to sets or use them as dict keys.

        For value objects, the hash should be based on all the value attributes, and we should ensure that the objects
        are immutable. We get this for free by specifying @frozen=True on the dataclass.
        """
        if not isinstance(other, Money):
            return NotImplemented
        return self.currency == other.currency and self.value == other.value
