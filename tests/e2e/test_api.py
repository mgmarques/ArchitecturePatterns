import pytest
import uuid
import requests
from allocation import config

#  Little helper functions that generate randomized characters by using the uuid module
def random_suffix():
    return uuid.uuid4().hex[:6]


def random_sku(name=""):
    return f"sku-{name}-{random_suffix()}"


def random_batchref(name=""):
    return f"batch-{name}-{random_suffix()}"


def random_orderid(name=""):
    return f"order-{name}-{random_suffix()}"


@pytest.mark.usefixtures("restart_api")
def test_allocations_are_persisted(add_stock):
    """ Test allocations are persisted """
    sku = random_sku()
    batch1, batch2 = random_batchref(1), random_batchref(2)
    order1, order2 = random_orderid(1), random_orderid(2)
    add_stock([
            (batch1, sku, 10, "2011-01-01"),
            (batch2, sku, 10, "2011-01-02")
    ])
    line1 = {"orderid": order1, "sku": sku, "qty": 10}
    line2 = {"orderid": order2, "sku": sku, "qty": 10}
    url = config.get_api_url()

    # first order uses up all stock in batch 1
    r = requests.post(f"{url}/allocate", json=line1)
    assert r.status_code == 201
    assert r.json()["batchref"] == batch1

    # second order should go to batch 2
    r = requests.post(f"{url}/allocate", json=line2)
    assert r.status_code == 201
    assert r.json()["batchref"] == batch2


@pytest.mark.usefixtures("restart_api")
def test_400_message_for_invalid_sku():
    """
    the SKU just doesn’t exist (because we never called add_stock), so it’s invalid as far as our app is concerned.
    """
    unknown_sku, orderid = random_sku(), random_orderid()
    data = {"orderid": orderid, "sku": unknown_sku, "qty": 20}
    url = config.get_api_url()
    r = requests.post(f"{url}/allocate", json=data)
    assert r.status_code == 400
    assert r.json()["message"] == f"Invalid sku {unknown_sku}"

@pytest.mark.usefixtures('restart_api')
def test_api_returns_allocation(add_stock):
    sku, othersku = random_sku(), random_sku('other')
    earlybatch = random_batchref(1)
    laterbatch = random_batchref(2)
    otherbatch = random_batchref(3)

    add_stock([
        (laterbatch, sku, 100, '2011-01-02'),
        (earlybatch, sku, 100, '2011-01-01'),
        (otherbatch, othersku, 100, None)
    ])
    data = {'orderid': random_orderid(), 'sku': sku, 'qty': 3}
    url = config.get_api_url()
    r = requests.post(f'{url}/allocate', json=data)
    assert r.status_code == 201
    assert r.json()['batchref'] == earlybatch

"""
After apply the service layer, we can confidently strip down our E2E tests to just two, one
for the happy path and one for the unhappy path:
"""
@pytest.mark.usefixtures("restart_api")
def test_happy_path_returns_201_and_allocated_batch(add_stock):
    sku, othersku = random_sku(), random_sku("other")
    earlybatch = random_batchref(1)
    laterbatch = random_batchref(2)
    otherbatch = random_batchref(3)
    add_stock(
        [
            (laterbatch, sku, 100, "2011-01-02"),
            (earlybatch, sku, 100, "2011-01-01"),
            (otherbatch, othersku, 100, None),
        ]
    )
    data = {"orderid": random_orderid(), "sku": sku, "qty": 3}
    url = config.get_api_url()

    r = requests.post(f"{url}/allocate", json=data)

    assert r.status_code == 201
    assert r.json()["batchref"] == earlybatch


@pytest.mark.usefixtures("restart_api")
def test_unhappy_path_returns_400_and_error_message():
    unknown_sku, orderid = random_sku(), random_orderid()
    data = {"orderid": orderid, "sku": unknown_sku, "qty": 20}
    url = config.get_api_url()
    r = requests.post(f"{url}/allocate", json=data)
    assert r.status_code == 400
    assert r.json()["message"] == f"Invalid sku {unknown_sku}"
"""
We’ve successfully split our tests into two broad categories: tests about web stuff, which we implement end to end; 
and tests about orchestration stuff, which we can test against the service layer in memory.
"""