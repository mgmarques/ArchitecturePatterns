"""
The ORM frameworks (object-relational mappers) exist to bridge the conceptual gap between the world of objects and
domain modeling and the world of databases and relational algebra.

The most important thing an ORM gives us is persistence ignorance: the idea that our fancy domain model doesn’t need to
know anything about how data is loaded or persisted. This keeps our domain clean of direct dependencies on specific
database technologies.

# Apply dependency inversion to your ORM
Our domain model should be free of infrastructure concerns, so our ORM should import our model, define our schema
separately and define an explicit mapper for how to convert between the schema and our domain model.

1. The ORM imports (or “depends on” or “knows about”) the domain model, and not the other way around.
2. We define our database tables and columns by using SQLAlchemy’s abstractions.
3. When we call the mapper function, SQLAlchemy does its magic to bind our domain model classes to the various
   tables we’ve defined.
"""
from allocation.domain import model     # 1
from sqlalchemy import Table, MetaData, Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import mapper, relationship

metadata = MetaData()

order_lines = Table(                        # 2
    "order_lines",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("sku", String(255)),
    Column("qty", Integer, nullable=False),
    Column("orderid", String(255)),
)

batches = Table(
    "batches",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("reference", String(255)),
    Column("sku", String(255)),
    Column("_purchased_quantity", Integer, nullable=False),
    Column("eta", Date, nullable=True),
)

allocations = Table(
    "allocations",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("orderline_id", ForeignKey("order_lines.id")),
    Column("batch_id", ForeignKey("batches.id")),
)


def start_mappers():
    """ We will be able to easily load and save domain model instances from and to the database. """
    lines_mapper = mapper(model.OrderLine, order_lines)     # 3
    mapper(
        model.Batch,
        batches,
        properties={
            "_allocations": relationship(
                lines_mapper, secondary=allocations, collection_class=set,
            )
        },
    )
