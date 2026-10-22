from flask import Flask, request, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from allocation import config
from allocation.domain import model
from allocation.adapters import orm
from allocation.adapters import repository
"""
# Before apply the service layer
```python
def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}
'''    
Without the service layer, the Flask app starting to get crufty. But our Flask app is starting to look a bit unwieldy. 
And our number of E2E tests is starting to get out of control, and soon we’ll end up with an inverted test pyramid

With the service layer, the responsibilities of the Flask app are just standard web stuff: per-request session 
management, parsing information out of POST parameters, response status codes, and JSON. All the orchestration logic  
is in the use case/service layer, and the domain logic stays in the domain.
"""
# Flask app delegating to service layer
from allocation.service_layer import services

# 1. Ensures the mapping of classes.
orm.start_mappers()

# 2. Create the tables in PostgreSQL: Instantiate the engine and force the creation of the structure.
engine = create_engine(config.get_postgres_uri())
orm.metadata.create_all(engine)

# 3. Links the session factory to the configured engine.
get_session = sessionmaker(bind=engine)
app = Flask(__name__)


@app.route("/allocate", methods=["POST"])
def allocate_endpoint():
    session = get_session()
    # batches = repository.SqlAlchemyRepository(session).list() # , with the service layer it changed to:
    # Instantiate a database session and some repository objects.
    repo = repository.SqlAlchemyRepository(session)
    # extract the user’s commands from the web request and pass them to a domain service.
    line = model.OrderLine(
        request.json["orderid"], request.json["sku"], request.json["qty"],
    )
    """
    # Before apply the service layer
    if not is_valid_sku(line.sku, batches):
        return jsonify({'message': f'Invalid sku {line.sku}'}), 400
    """
    try:
        batchref = services.allocate(line, repo, session)
    except (model.OutOfStock, services.InvalidSku) as e:
        # return some JSON responses with the appropriate status codes.
        return {"message": str(e)}, 400

    return {"batchref": batchref}, 201
