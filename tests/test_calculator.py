import pytest
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
        has_island=False,
        length_island=0.0,
        led_pas=False,
        drawer_count=drawer_count,
        vrchne_otvaranie_typ=None,
        vrchne_doors_count=0,
        rohovy_typ=False,
        potravinova_typ=None,
        sortier=False,
        hidden_coffee=False,
        zastena=False,
        discount_pct=0.0,
        discount_abs=0.0,
    )
    total, _ = calculate_total(p)
    assert total >= expected_min