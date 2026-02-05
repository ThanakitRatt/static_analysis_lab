import pytest
from invoice_service import InvoiceService, Invoice, LineItem

def test_compute_total_basic():
    service = InvoiceService()
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

def test_invalid_qty_raises():
    service = InvoiceService()
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

def test_compute_total_with_gold_membership():
    service = InvoiceService()
    inv = Invoice(
        invoice_id="I-003",
        customer_id="C-002",
        country="US",
        membership="gold",
        coupon=None,
        items=[LineItem(sku="B", category="electronics", unit_price=500.0, qty=1)]
    )
    total, warnings = service.compute_total(inv)
    assert total > 0

def test_compute_total_with_platinum_membership():
    service = InvoiceService()
    inv = Invoice(
        invoice_id="I-004",
        customer_id="C-003",
        country="JP",
        membership="platinum",
        coupon=None,
        items=[LineItem(sku="C", category="food", unit_price=200.0, qty=2)]
    )
    total, warnings = service.compute_total(inv)
    assert total > 0

def test_compute_total_with_valid_coupon():
    service = InvoiceService()
    inv = Invoice(
        invoice_id="I-005",
        customer_id="C-004",
        country="TH",
        membership="none",
        coupon="WELCOME10",
        items=[LineItem(sku="D", category="book", unit_price=1000.0, qty=1)]
    )
    total, warnings = service.compute_total(inv)
    assert total > 0

def test_compute_total_with_invalid_coupon():
    service = InvoiceService()
    inv = Invoice(
        invoice_id="I-006",
        customer_id="C-005",
        country="TH",
        membership="none",
        coupon="INVALID99",
        items=[LineItem(sku="E", category="electronics", unit_price=500.0, qty=1)]
    )
    total, warnings = service.compute_total(inv)
    assert "Unknown coupon" in warnings

def test_compute_total_with_fragile_items():
    service = InvoiceService()
    inv = Invoice(
        invoice_id="I-007",
        customer_id="C-006",
        country="TH",
        membership="none",
        coupon=None,
        items=[LineItem(sku="F", category="other", unit_price=150.0, qty=3, fragile=True)]
    )
    total, warnings = service.compute_total(inv)
    assert total > 0

def test_compute_total_high_value_warning():
    service = InvoiceService()
    inv = Invoice(
        invoice_id="I-008",
        customer_id="C-007",
        country="TH",
        membership="none",
        coupon=None,
        items=[LineItem(sku="G", category="electronics", unit_price=5000.0, qty=3)]
    )
    total, warnings = service.compute_total(inv)
    assert "Consider membership upgrade" in warnings

def test_compute_total_negative_total_becomes_zero():
    service = InvoiceService()
    inv = Invoice(
        invoice_id="I-009",
        customer_id="C-008",
        country="TH",
        membership="platinum",
        coupon="VIP20",
        items=[LineItem(sku="H", category="food", unit_price=10.0, qty=1)]
    )
    total, warnings = service.compute_total(inv)
    assert total >= 0

def test_large_subtotal_discount():
    service = InvoiceService()
    inv = Invoice(
        invoice_id="I-010",
        customer_id="C-009",
        country="US",
        membership="none",
        coupon=None,
        items=[LineItem(sku="I", category="electronics", unit_price=1000.0, qty=4)]
    )
    total, warnings = service.compute_total(inv)
    assert total > 0

def test_calculate_shipping_various_countries():
    service = InvoiceService()
    assert service._calculate_shipping("TH", 400) == 60
    assert service._calculate_shipping("US", 150) == 15
    assert service._calculate_shipping("JP", 3000) == 600

def test_calculate_tax():
    service = InvoiceService()
    assert service._calculate_tax("TH", 1000, 100) == 63.0
    assert service._calculate_tax("JP", 1000, 100) == 90.0

def test_validate_missing_invoice_id():
    service = InvoiceService()
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