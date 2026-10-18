# ArchitecturePatterns
Example Python code for several classic architectural patterns, demonstrating how they support TDD, DDD, and event-driven services.

## Setup your environment
### Creating a local virtualenv
```sh
python3.8 -m venv .venv && source .venv/bin/activate # or however you like to create virtualenvs
pip install pytest 
pip install pytest sqlalchemy
pip install -e src/
```

### Building the containers
```sh
make build
make up
# or
make all # builds, brings containers up, runs tests
```

## Running the tests

```sh
make test
# or, to run individual test types
make unit-tests
make integration-tests
make e2e-tests
# or, if you have a local virtualenv
make up
pytest tests/unit
pytest tests/integration
pytest tests/e2e
```

### Tests with dockers images

**Note**: these will speed up builds, for docker-compose >= 1.25
```sh
export COMPOSE_DOCKER_CLI_BUILD=1
export DOCKER_BUILDKIT=1
```

all: down build up test

build:
```sh
	docker-compose build
```

up:
```sh
	docker-compose up -d
```

down:
```sh
	docker-compose down --remove-orphans
```

test: up
```sh
	docker-compose run --rm --no-deps --entrypoint=pytest api /tests/unit /tests/integration /tests/e2e
```

unit-tests:
```sh
	docker-compose run --rm --no-deps --entrypoint=pytest api /tests/unit
```

integration-tests: up
```sh
	docker-compose run --rm --no-deps --entrypoint=pytest api /tests/integration
```

e2e-tests: up
```sh
	docker-compose run --rm --no-deps --entrypoint=pytest api /tests/e2e
```

logs:
```sh
	docker-compose logs --tail=25 api redis_pubsub
```

black:
```sh
	black -l 86 $$(find * -name '*.py')
```