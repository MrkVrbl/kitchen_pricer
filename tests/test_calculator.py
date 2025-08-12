import pytest
import math
from pricing.config import PRICES
from pricing.models import LeadIn
from pricing.calculator import calculate_total

@pytest.mark.parametrize("length_spod,length_spod_vrch,length_full,shape,drawer_count,expected_min", [
    (3.0, 0.0, 0.0, "rovný", 0, 300),
    (2.0, 1.0, 0.0, "L", 2, 600),
    (0.0, 2.0, 1.0, "U", 1, 800),
])
def test_calculation_basic(length_spod, length_spod_vrch, length_full, shape, drawer_count, expected_min):
    p = LeadIn(
        customer_name="Test",
        address="TestCity",
        floors=1,
        distance_km=10,
        length_spod=length_spod,
        length_spod_vrch=length_spod_vrch,
        length_full=length_full,
        material_dvierok="laminát",
        material_pracovnej_dosky="drevodekor",
        has_island=False,
        length_island=0.0,
        led_pas=False,
        drawer_count=drawer_count,
        vrchne_otvaranie_typ=None,
        vrchne_doors_count=0,
        rohovy_typ=False,
        potravinova_skrina_typ=None,
        sortier=False,
        hidden_coffee=False,
        zastena=False,
        discount_pct=0.0,
        discount_abs=0.0,
        shape=shape,
    )
    assert isinstance(p, LeadIn)
    total, _ = calculate_total(p)
    assert total >= expected_min


def test_discount_percentage_applied():
    p = LeadIn(
        customer_name="Test",
        address="TestCity",
        floors=1,
        distance_km=10,
        length_spod=2.0,
        length_spod_vrch=0.0,
        length_full=0.0,
        material_dvierok="laminát",
        material_pracovnej_dosky="bez",
        has_island=False,
        length_island=0.0,
        led_pas=False,
        drawer_count=0,
        vrchne_otvaranie_typ=None,
        vrchne_doors_count=0,
        rohovy_typ=False,
        potravinova_skrina_typ=None,
        potravinove_sufle_typ=None,
        sortier=False,
        hidden_coffee=False,
        zastena=False,
        discount_pct=10.0,
        discount_abs=0.0,
    )
    total, breakdown = calculate_total(p)
    subtotal = breakdown["subtotal"]
    pct = p.discount_pct / 100
    subtotal_after_discount = subtotal * (1 - pct) - p.discount_abs
    expected_without_dph = math.ceil((subtotal_after_discount + breakdown["montaz"] + breakdown["doprava"] + breakdown["vynaska"]) / 20) * 20
    expected_with_dph = math.ceil(expected_without_dph * (1 + PRICES["dph"]) / 20) * 20
    assert total == expected_with_dph