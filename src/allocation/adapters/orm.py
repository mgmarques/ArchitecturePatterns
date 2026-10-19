"""
# Apply dependency inversion to your ORM
Our domain model should be free of infrastructure concerns, so our ORM should import our model,
and not the other way around.
"""
from allocation.domain import model
from sqlalchemy.orm import mapper, relationship
from sqlalchemy import Table, MetaData, Column, Integer, String, Date, ForeignKey


metadata = MetaData()

order_lines = Table(
    "order_lines",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("sku", String(255)),
    Column("qty", Integer, nullable=False),
    Column("orderid", String(255)),
)

def start_mappers():
    lines_mapper = mapper(model.OrderLine, order_lines)