from typing import Optional, Set, List
from dataclasses import dataclass
from datetime import date


class OutOfStock(Exception):
    """ Raising a domain exception """
    pass


@dataclass(unsafe_hash=True)
class OrderLine:
    """
    OrderLine is a value object.
    
    One of the nice things that dataclasses (or namedtuples) give us is value equality, which is the fancy way of
    saying, “Two lines with the same orderid, sku, and qty are equal.”
    """
    orderid: str
    sku: str
    qty: int


class Batch:
    """
    We use the term entity to describe a domain object that has a long-lived identity.
    Entities, unlike values, have identity equality. We can change their values, and
    they are still recognizably the same thing.
    """
    def __init__(self, ref: str, sku: str, qty: int, eta: Optional[date]):
        self.reference: str = ref
        self.sku: str = sku
        self.eta: date = eta
        self._purchased_quantity: int = qty
        self._allocations: Set[OrderLine] = set()

    def __repr__(self):
        return f"<Batch {self.reference}>"

    def __eq__(self, other):
        """ We usually make this explicit in code by implementing equality operators on entities: """
        if not isinstance(other, Batch):
            return False
        return other.reference == self.reference

    def __hash__(self):
        """
        For both entity and value objects, it’s also worth thinking through how hash will work. It’s the magic method
        Python uses to control the behavior of objects when you add them to sets or use them as dict keys;

        For entities, the simplest option is to say that the hash is None, meaning that the object is not hashable and
        cannot, for example, be used in a set. If for some reason you decide you really do want to use set or dict
        operations with entities, the hash should be based on the attribute(s), such as .reference, that define the
        entity’s unique identity over time.
        """
        return hash(self.reference)

    def __gt__(self, other):
        if self.eta is None:
            return False
        if other.eta is None:
            return True
        return self.eta > other.eta

    def allocate(self, line: OrderLine):
        if self.can_allocate(line):
            self._allocations.add(line)

    def deallocate(self, line: OrderLine):
        if line in self._allocations:
            self._allocations.remove(line)

    def deallocate_one(self) -> OrderLine:
        return self._allocations.pop()

    @property
    def allocated_quantity(self) -> int:
        return sum(line.qty for line in self._allocations)

    @property
    def available_quantity(self) -> int:
        return self._purchased_quantity - self.allocated_quantity

    def can_allocate(self, line: OrderLine) -> bool:
        return self.sku == line.sku and self.available_quantity >= line.qty

def allocate(line: OrderLine, batches: List[Batch]) -> str:
    """ A standalone function for our domain service """
    try:
        batch = next(b for b in sorted(batches) if b.can_allocate(line))
        batch.allocate(line)
    except StopIteration:
        raise OutOfStock(f'Out of stock for sku {line.sku}')
    return batch.reference
