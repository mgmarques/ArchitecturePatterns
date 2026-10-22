"""
We’ve defined a clear API for our domain, a set of use cases or entrypoints that can be used by any adapter without
needing to know anything about our domain model classes—whether that’s an API, a CLI, or the tests! They’re an adapter
for our domain too.

We can write tests in “high gear” by using the service layer, leaving us free to refactor the domain model in any way
we see fit. As long as we can still deliver the same use cases, we can experiment with new designs without needing to
rewrite a load of tests.
"""
from allocation.domain import model
from allocation.domain.model import OrderLine
from allocation.adapters.repository import AbstractRepository


class InvalidSku(Exception):
    pass


def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}


def allocate(line: OrderLine, repo: AbstractRepository, session) -> str:
    """ Fetch some objects from the repository.
    It depends on a repository . We’ve chosen to make the dependency explicit, and we’ve used the
    type hint to say that we depend on AbstractRepository. This means it’ll work both when the tests
    give it a FakeRepository and when the Flask app gives it a SqlAlchemyRepository.

    If you remember “The Dependency Inversion Principle”, this is what we mean when we say we should
    “depend on abstractions.” Our high-level module, the service layer, depends on the repository abstraction.
    And the details of the implementation for our specific choice of persistent storage also depend on that
    same abstraction.
    """
    batches = repo.list()

    # Make some checks or assertions about the request against the current state of the world.
    if not is_valid_sku(line.sku, batches):
        raise InvalidSku(f"Invalid sku {line.sku}")

    # Call a domain service.
    batchref = model.allocate(line, batches)

    # If all is well, save/update any state we’ve changed.
    session.commit()

    return batchref