"""
# Introducing a Service Layer, and Using FakeRepository to Unit Test It
If we look at what our Flask app is doing, there’s quite a lot of what we might call orchestration—fetching stuff out
of our repository, validating our input against database state, handling errors, and committing in the happy path.
Most of these things don’t have anything to do with having a web API endpoint (you’d need them if you were building a
CLI, for example), and they’re not really things that need to be tested by end-to-end tests.

It often makes sense to split out a service layer, sometimes called an orchestration layer or a use-case layer.

We’ve successfully split our tests into two broad categories: tests about web stuff, which we implement end to end;
and tests about orchestration stuff, which we can test against the service layer in memory.
"""
import pytest
from src.allocation.domain  import model
from src.allocation.adapters import repository
from src.allocation.service_layer import services


class FakeRepository(repository.AbstractRepository):
    """ Our fake repository, an in-memory collection of batches """
    def __init__(self, batches):
        self._batches = set(batches)

    def add(self, batch):
        self._batches.add(batch)

    def get(self, reference):
        return next(b for b in self._batches if b.reference == reference)

    def list(self):
        return list(self._batches)


class FakeSession:
    """ We also need a FakeSession to fake out the database session """
    committed = False

    def commit(self):
        self.committed = True

"""
# Unit testing with fakes at the service layer:
Here’s where it will come in useful; it lets us test our service layer with nice, fast unit tests:
1. FakeRepository holds the Batch objects that will be used by our test.
2. Our services module (services.py) will define an allocate() service-layer function. It will sit between our 
   allocate_endpoint() function in the API layer and the allocate() domain service function from our domain model.   
"""
def test_returns_allocation():
    line = model.OrderLine("o1", "COMPLICATED-LAMP", 10)
    batch = model.Batch("b1", "COMPLICATED-LAMP", 100, eta=None)
    repo = FakeRepository([batch])      # 1

    result = services.allocate(line, repo, FakeSession())       # 2
    assert result == "b1"


def test_error_for_invalid_sku():
    line = model.OrderLine("o1", "NONEXISTENTSKU", 10)
    batch = model.Batch("b1", "AREALSKU", 100, eta=None)
    repo = FakeRepository([batch])      # 1

    with pytest.raises(services.InvalidSku, match="Invalid sku NONEXISTENTSKU"):
        services.allocate(line, repo, FakeSession())       # 2


def test_commits():
    line = model.OrderLine("o1", "OMINOUS-MIRROR", 10)
    batch = model.Batch("b1", "OMINOUS-MIRROR", 100, eta=None)
    repo = FakeRepository([batch])       # 1
    session = FakeSession()

    services.allocate(line, repo, session)       # 2
    assert session.committed is True

def test_deallocation():
    line1 = model.OrderLine("o1", "COMPLICATED-LAMP", 10)
    line2 = model.OrderLine("o2", "COMPLICATED-LAMP", 15)
    batch = model.Batch("b1", "COMPLICATED-LAMP", 100, eta=None)
    repo = FakeRepository([batch])      # 1

    services.allocate(line1, repo, FakeSession())       # 2
    services.allocate(line2, repo, FakeSession())       # 2
    assert batch.available_quantity == 75

    services.deallocate(line2, repo, FakeSession())
    assert batch.available_quantity == 90


def test_deallocation_one():
    line1 = model.OrderLine("o1", "COMPLICATED-LAMP", 25)
    line2 = model.OrderLine("o2", "COMPLICATED-LAMP", 25)
    batch = model.Batch("b1", "COMPLICATED-LAMP", 100, eta=None)
    repo = FakeRepository([batch])      # 1

    services.allocate(line1, repo, FakeSession())       # 2
    services.allocate(line2, repo, FakeSession())       # 2
    assert batch.available_quantity == 50
    assert len([b._allocations for b in repo.list()][0]) == 2

    services.deallocate_one(batch, FakeSession())
    assert batch.available_quantity == 75
    assert len([b._allocations for b in repo.list()][0]) == 1