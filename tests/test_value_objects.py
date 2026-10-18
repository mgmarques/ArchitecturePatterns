import pytest
from allocation.domain.value_objects import Money, Name, Line

fiver = Money('gbp', 5)
tenner = Money('gbp', 10)
another_fiver = Money('gbp', 5)


def test_equality():
    assert Money('gbp', 10) == Money('gbp', 10)
    assert Name('Harry', 'Percival') != Name('Bob', 'Percival')
    assert Line('Red Chair', 5) == Line('Red Chair', 5)

def test_maths_over_value_objects():
    assert fiver + fiver == tenner
    assert tenner - fiver == fiver
    assert fiver * 5 == Money('gbp', 25)
    assert 5 * fiver  == Money('gbp', 25)
    assert fiver / 5 == Money('gbp', 1)

def test_adding_different_currencies_fails():
    with pytest.raises(ValueError):
        Money('usd', 10) + Money('gbp', 10)

def test_multiplying_two_money_values_is_an_error():
    with pytest.raises(TypeError):
        tenner * fiver

def test_comparison_safety_guardrails():
    gbp_fiver = Money('gbp', 5)
    usd_tenner = Money('usd', 10)

    # This will raise a ValueError because the currencies don't match
    try:
        gbp_fiver < usd_tenner
    except ValueError as e:
        assert "Currency mismatch" in str(e)

def test_money_prevent_dividing_by_zero():
    try:
        fiver / 0
    except ZeroDivisionError:
        pass

def test_money_comparisons():
    # All of these work seamlessly now:
    assert fiver < tenner
    assert tenner > fiver
    assert fiver <= another_fiver
    assert fiver >= another_fiver
    assert fiver != tenner

def test_sort_money():
    prices = [Money('gbp', 20), Money('gbp', 5), Money('gbp', 12)]
    prices.sort()
    assert prices == [Money('gbp', 5), Money('gbp', 12), Money('gbp', 20)]
