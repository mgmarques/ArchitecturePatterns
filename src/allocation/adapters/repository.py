"""
Let's use the dependency inversion principle as a way of decoupling our core logic from infrastructural concerns.

This simplifying abstraction makes our system more testable by hiding the complexities of the database.

Ports and adapters came out of the OO world, and the definition we hold onto is that the port is the interface between
our application and whatever it is we wish to abstract away, and the adapter is the implementation behind that
interface or abstraction.

Now Python doesn’t have interfaces per se, so although it’s usually easy to identify an adapter, defining the port can
be harder. If you’re using an abstract base class, that’s the port. If not, the port is just the duck type that your
adapters conform to and that your core application expects—the function and method names in use, and their argument
names and types.

Concretely, here, AbstractRepository is the port, and SqlAlchemyRepository and FakeRepository are the adapters.

1. Python tip: @abc.abstractmethod is one of the only things that makes ABCs actually "work" in Python.
   Python will refuse to let you instantiate a class that does not implement all the abstractmethods defined
   in its parent class.

2. raise NotImplementedError is nice, but it’s neither necessary nor sufficient.
   In fact, your abstract methods can have real behavior that subclasses can call out to, if you really want.
"""
import abc
from allocation.domain import model


class AbstractRepository(abc.ABC):
    """
    # The Repository pattern is a simple abstraction around permanent storage
    The repository gives you the illusion of a collection of in-memory objects.

    The simplest repository has just two methods:
     * add() to put a new item in the repository, and
     * get() to return a previously added item.
    We stick rigidly to using these methods for data access in our domain and our service layer.
    This self-imposed simplicity stops us from coupling our domain model to the database.
    """
    @abc.abstractmethod                 # 1
    def add(self, batch: model.Batch):
        raise NotImplementedError       # 2

    @abc.abstractmethod
    def get(self, reference) -> model.Batch:
        raise NotImplementedError


class SqlAlchemyRepository(AbstractRepository):
    """
    The Repository pattern makes it easy to swap fundamental details of your
    infrastructure without disrupting your core application.
    """
    def __init__(self, session):
        self.session = session

    def add(self, batch):
        self.session.add(batch)

    def get(self, reference):
        return self.session.query(model.Batch).filter_by(reference=reference).one()

    def list(self):
        return self.session.query(model.Batch).all()


class FakeRepository(AbstractRepository):
    """ The Repository pattern makes it easy to create a FakeRepository for testing """
    def __init__(self, batches):
        self._batches = set(batches)

    def add(self, batch):
        self._batches.add(batch)

    def get(self, reference):
        return next(b for b in self._batches if b.reference == reference)

    def list(self):
        return list(self._batches)