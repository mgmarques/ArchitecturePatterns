# pylint: disable=redefined-outer-name
"""
You can define common dependencies for your tests as “fixtures” and pytest will inject them to the tests that need
them by looking at their function arguments. In this case, it’s a SQLAlchemy database session.
"""
import shutil
import subprocess
import time
from pathlib import Path

import pytest
import redis
import requests
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, clear_mappers
from tenacity import retry, stop_after_delay

from allocation.adapters import orm
from allocation.adapters.orm import metadata, start_mappers
from allocation import config

pytest.register_assert_rewrite("tests.e2e.api_client")


@pytest.fixture(scope="session", autouse=True)
def initialize_mappers():
    clear_mappers()
    start_mappers()
    yield
    clear_mappers()


@pytest.fixture
def in_memory_db():
    engine = create_engine("sqlite:///:memory:")
    metadata.create_all(engine)
    return engine


@pytest.fixture
def session(in_memory_db):
    _session = sessionmaker(bind=in_memory_db)()
    yield _session
    _session.close()


@pytest.fixture
def sqlite_session_factory(in_memory_db):
    yield sessionmaker(bind=in_memory_db)


@retry(stop=stop_after_delay(10))
def wait_for_postgres_to_come_up(engine):
    return engine.connect()


@retry(stop=stop_after_delay(10))
def wait_for_webapp_to_come_up():
    return requests.get(config.get_api_url())


@retry(stop=stop_after_delay(10))
def wait_for_redis_to_come_up():
    r = redis.Redis(**config.get_redis_host_and_port())
    return r.ping()


@pytest.fixture(scope="session")
def postgres_db():
    # Se os testes rodam localmente na máquina física, ajustamos a URI do Postgres
    # para usar a porta pública exposta pelo Docker Compose (54321)
    uri = config.get_postgres_uri()
    if "localhost" in uri and "54321" not in uri:
        uri = uri.replace("5432", "54321")

    engine = create_engine(uri, isolation_level="SERIALIZABLE")
    wait_for_postgres_to_come_up(engine)
    metadata.create_all(engine)
    return engine


@pytest.fixture
def postgres_session_factory(postgres_db):
    yield sessionmaker(bind=postgres_db)


@pytest.fixture
def postgres_session(postgres_db):
    _session = sessionmaker(bind=postgres_db)()
    yield _session
    _session.close()


@pytest.fixture
def restart_api():
    root_dir = Path(__file__).parent.parent
    flask_app_path = root_dir / "src" / "allocation" / "entrypoints" / "flask_app.py"

    # Atualiza o timestamp para o reloader do Flask perceber
    flask_app_path.touch()
    time.sleep(0.5)

    # Se a API demorar para reciclar no Mac, a checagem não quebra o teste imediatamente
    try:
        wait_for_webapp_to_come_up()
    except Exception:
        time.sleep(2)  # Dá um fôlego extra caso o macOS atrase a propagação do volume
        wait_for_webapp_to_come_up()


@pytest.fixture
def restart_redis_pubsub():
    wait_for_redis_to_come_up()

    # Verifica tanto 'docker-compose' quanto o moderno 'docker'
    if not shutil.which("docker-compose") and not shutil.which("docker"):
        print("skipping restart, assumes running in container")
        return

    # Usa o comando correto dependendo do que estiver instalado no seu Mac
    cmd = ["docker-compose"] if shutil.which("docker-compose") else ["docker", "compose"]
    cmd.extend(["restart", "-t", "0", "redis_pubsub"])

    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print("Falha ao reiniciar redis_pubsub via subprocess, pulando...")

@pytest.fixture
def add_stock(postgres_session):
    """ Helper fixture que oculta os detalhes de inserção manual de linhas usando SQL bruto. """
    batches_added = set()
    skus_added = set()

    def _add_stock(lines):
        for ref, sku, qty, eta in lines:
            # CORRETO: Envolvido em text() para conformidade com SQLAlchemy 1.4+
            postgres_session.execute(
                text("INSERT INTO batches (reference, sku, _purchased_quantity, eta)"
                     " VALUES (:ref, :sku, :qty, :eta)"),
                dict(ref=ref, sku=sku, qty=qty, eta=eta),
            )
            [[batch_id]] = postgres_session.execute(
                text("SELECT id FROM batches WHERE reference=:ref AND sku=:sku"),
                dict(ref=ref, sku=sku),
            )
            batches_added.add(batch_id)
            skus_added.add(sku)
        postgres_session.commit()

    yield _add_stock

    # Limpeza pós-teste (Teardown) também corrigida com text()
    for batch_id in batches_added:
        postgres_session.execute(
            text("DELETE FROM allocations WHERE batch_id=:batch_id"),
            dict(batch_id=batch_id),
        )
        postgres_session.execute(
            text("DELETE FROM batches WHERE id=:batch_id"),
            dict(batch_id=batch_id),
        )
    for sku in skus_added:
        postgres_session.execute(
            text("DELETE FROM order_lines WHERE sku=:sku"),
            dict(sku=sku),
        )
        postgres_session.commit()
