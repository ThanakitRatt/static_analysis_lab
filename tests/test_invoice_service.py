import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from invoice_service import InvoiceService, Invoice, LineItem

@pytest.fixture
def service():
    return InvoiceService()

def test_compute_total_basic(service):
    inv = Invoice(
        invoice_id="I-001",
        customer_id="C-001",
        country="TH",
        membership="none",
        coupon=None,
        items=[LineItem(sku="A", category="book", unit_price=100.0, qty=2)]
    )
    total, warnings = service.compute_total(inv)
    assert total > 0
    assert isinstance(warnings, list)

def test_invalid_qty_raises(service):
    inv = Invoice(
        invoice_id="I-002",
        customer_id="C-001",
        country="TH",
        membership="none",
        coupon=None,
        items=[LineItem(sku="A", category="book", unit_price=100.0, qty=0)]
    )
    with pytest.raises(ValueError):
        service.compute_total(inv)

def test_compute_total_with_gold_membership(service):
    inv = Invoice(
        invoice_id="I-003",
        customer_id="C-002",
        country="US",
        membership="gold",
        coupon=None,
        items=[LineItem(sku="B", category="electronics", unit_price=500.0, qty=1)]
    )
    total, _ = service.compute_total(inv)
    assert total > 0

def test_compute_total_with_platinum_membership(service):
    inv = Invoice(
        invoice_id="I-004",
        customer_id="C-003",
        country="JP",
        membership="platinum",
        coupon=None,
        items=[LineItem(sku="C", category="food", unit_price=200.0, qty=2)]
    )
    total, _ = service.compute_total(inv)
    assert total > 0

def test_compute_total_with_valid_coupon(service):
    inv = Invoice(
        invoice_id="I-005",
        customer_id="C-004",
        country="TH",
        membership="none",
        coupon="WELCOME10",
        items=[LineItem(sku="D", category="book", unit_price=1000.0, qty=1)]
    )
    total, _ = service.compute_total(inv)
    assert total > 0

def test_compute_total_with_invalid_coupon(service):
    inv = Invoice(
        invoice_id="I-006",
        customer_id="C-005",
        country="TH",
        membership="none",
        coupon="INVALID99",
        items=[LineItem(sku="E", category="electronics", unit_price=500.0, qty=1)]
    )
    _, warnings = service.compute_total(inv)
    assert "Unknown coupon" in warnings

def test_compute_total_with_fragile_items(service):
    inv = Invoice(
        invoice_id="I-007",
        customer_id="C-006",
        country="TH",
        membership="none",
        coupon=None,
        items=[LineItem(sku="F", category="other", unit_price=150.0, qty=3, fragile=True)]
    )
    total, _ = service.compute_total(inv)
    assert total > 0

def test_compute_total_high_value_warning(service):
    inv = Invoice(
        invoice_id="I-008",
        customer_id="C-007",
        country="TH",
        membership="none",
        coupon=None,
        items=[LineItem(sku="G", category="electronics", unit_price=5000.0, qty=3)]
    )
    _, warnings = service.compute_total(inv)
    assert "Consider membership upgrade" in warnings

def test_compute_total_negative_total_becomes_zero(service):
    inv = Invoice(
        invoice_id="I-009",
        customer_id="C-008",
        country="TH",
        membership="platinum",
        coupon="VIP20",
        items=[LineItem(sku="H", category="food", unit_price=10.0, qty=1)]
    )
    total, _ = service.compute_total(inv)
    assert total >= 0

def test_large_subtotal_discount(service):
    inv = Invoice(
        invoice_id="I-010",
        customer_id="C-009",
        country="US",
        membership="none",
        coupon=None,
        items=[LineItem(sku="I", category="electronics", unit_price=1000.0, qty=4)]
    )
    total, _ = service.compute_total(inv)
    assert total > 0

def test_calculate_shipping_various_countries(service):
    assert service._calculate_shipping("TH", 400) == 60
    assert service._calculate_shipping("US", 150) == 15
    assert service._calculate_shipping("JP", 3000) == 600

def test_calculate_tax(service):
    assert service._calculate_tax("TH", 1000, 100) == pytest.approx(63.0)
    assert service._calculate_tax("JP", 1000, 100) == pytest.approx(90.0)

def test_validate_missing_invoice_id(service):
    inv = Invoice(
        invoice_id="",
        customer_id="C-010",
        country="TH",
        membership="none",
        coupon=None,
        items=[LineItem(sku="J", category="book", unit_price=100.0, qty=1)]
    )
    with pytest.raises(ValueError):
        service.compute_total(inv)

def test_missing_customer_id(service):
    inv = Invoice(
        invoice_id="I-011",
        customer_id="",
        country="TH",
        membership="none",
        coupon=None,
        items=[LineItem(sku="K", category="book", unit_price=100.0, qty=1)]
    )
    with pytest.raises(ValueError):
        service.compute_total(inv)

def test_missing_sku(service):
    inv = Invoice(
        invoice_id="I-012",
        customer_id="C-011",
        country="TH",
        membership="none",
        coupon=None,
        items=[LineItem(sku="", category="book", unit_price=100.0, qty=1)]
    )
    with pytest.raises(ValueError):
        service.compute_total(inv)

def test_invalid_price(service):
    inv = Invoice(
        invoice_id="I-013",
        customer_id="C-012",
        country="TH",
        membership="none",
        coupon=None,
        items=[LineItem(sku="L", category="book", unit_price=-50.0, qty=1)]
    )
    with pytest.raises(ValueError):
        service.compute_total(inv)

def test_unknown_category(service):
    inv = Invoice(
        invoice_id="I-014",
        customer_id="C-013",
        country="TH",
        membership="none",
        coupon=None,
        items=[LineItem(sku="M", category="invalid", unit_price=100.0, qty=1)]
    )
    with pytest.raises(ValueError):
        service.compute_total(inv)

def test_shipping_free_over_threshold(service):
    assert service._calculate_shipping("TH", 500) == pytest.approx(0.0)

def test_shipping_default_country(service):
    assert service._calculate_shipping("UK", 150) == pytest.approx(25)
    assert service._calculate_shipping("UK", 250) == pytest.approx(0.0)

def test_discount_subtotal_over_3000(service):
    inv = Invoice(
        invoice_id="I-015",
        customer_id="C-014",
        country="TH",
        membership="none",
        coupon=None,
        items=[]
    )
    warnings = []
    discount = service._calculate_discount(inv, 4000, warnings)
    assert discount == 20