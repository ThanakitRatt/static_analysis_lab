import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from invoice_service import InvoiceService, Invoice, LineItem


@pytest.fixture
def service():
    return InvoiceService()


class TestValidation:
    def test_missing_invoice_id(self, service):
        inv = Invoice("", "C-001", "TH", "none", None, [
            LineItem("A", "book", 100.0, 2)
        ])
        with pytest.raises(ValueError, match="Missing invoice_id"):
            service.compute_total(inv)

    def test_missing_customer_id(self, service):
        inv = Invoice("I-001", "", "TH", "none", None, [
            LineItem("A", "book", 100.0, 2)
        ])
        with pytest.raises(ValueError, match="Missing customer_id"):
            service.compute_total(inv)

    def test_missing_items(self, service):
        inv = Invoice("I-001", "C-001", "TH", "none", None, [])
        with pytest.raises(ValueError, match="Invoice must contain items"):
            service.compute_total(inv)

    def test_invalid_qty(self, service):
        inv = Invoice("I-001", "C-001", "TH", "none", None, [
            LineItem("A", "book", 100.0, 0)
        ])
        with pytest.raises(ValueError, match="Invalid qty"):
            service.compute_total(inv)

    def test_invalid_price(self, service):
        inv = Invoice("I-001", "C-001", "TH", "none", None, [
            LineItem("A", "book", -50.0, 1)
        ])
        with pytest.raises(ValueError, match="Invalid price"):
            service.compute_total(inv)

    def test_unknown_category(self, service):
        inv = Invoice("I-001", "C-001", "TH", "none", None, [
            LineItem("A", "invalid", 100.0, 1)
        ])
        with pytest.raises(ValueError, match="Unknown category"):
            service.compute_total(inv)


class TestShipping:
    def test_shipping_thailand_under_threshold(self, service):
        assert service._calculate_shipping("TH", 400) == 60

    def test_shipping_thailand_over_threshold(self, service):
        assert service._calculate_shipping("TH", 500) == 0.0

    def test_shipping_us_tier1(self, service):
        assert service._calculate_shipping("US", 50) == 15

    def test_shipping_us_tier2(self, service):
        assert service._calculate_shipping("US", 150) == 15

    def test_shipping_us_tier3(self, service):
        assert service._calculate_shipping("US", 250) == 8

    def test_shipping_us_free(self, service):
        assert service._calculate_shipping("US", 300) == 0.0

    def test_shipping_japan(self, service):
        assert service._calculate_shipping("JP", 3000) == 600

    def test_shipping_default_country(self, service):
        assert service._calculate_shipping("UK", 150) == 25


class TestDiscount:
    def test_gold_membership_discount(self, service):
        inv = Invoice("I-001", "C-001", "TH", "gold", None, [])
        discount = service._calculate_discount(inv, 1000, [])
        assert discount == 30.0

    def test_platinum_membership_discount(self, service):
        inv = Invoice("I-001", "C-001", "TH", "platinum", None, [])
        discount = service._calculate_discount(inv, 1000, [])
        assert discount == 50.0

    def test_high_subtotal_no_membership(self, service):
        inv = Invoice("I-001", "C-001", "TH", "none", None, [])
        discount = service._calculate_discount(inv, 4000, [])
        assert discount == 20.0

    def test_valid_coupon(self, service):
        inv = Invoice("I-001", "C-001", "TH", "none", "WELCOME10", [])
        discount = service._calculate_discount(inv, 1000, [])
        assert discount == 100.0

    def test_invalid_coupon_warning(self, service):
        warnings = []
        inv = Invoice("I-001", "C-001", "TH", "none", "INVALID", [])
        discount = service._calculate_discount(inv, 1000, warnings)
        assert discount == 0.0
        assert "Unknown coupon" in warnings

    def test_coupon_with_membership(self, service):
        inv = Invoice("I-001", "C-001", "TH", "gold", "WELCOME10", [])
        discount = service._calculate_discount(inv, 1000, [])
        assert discount == 130.0


class TestTax:
    def test_tax_thailand(self, service):
        assert service._calculate_tax("TH", 1000, 100) == 63.0

    def test_tax_japan(self, service):
        assert service._calculate_tax("JP", 1000, 100) == 90.0

    def test_tax_us(self, service):
        assert service._calculate_tax("US", 1000, 100) == 72.0

    def test_tax_default_rate(self, service):
        assert service._calculate_tax("UK", 1000, 100) == 45.0


class TestComputeTotal:
    def test_basic_invoice(self, service):
        inv = Invoice("I-001", "C-001", "TH", "none", None, [
            LineItem("A", "book", 100.0, 2)
        ])
        total, warnings = service.compute_total(inv)
        assert total > 0
        assert len(warnings) == 0

    def test_with_fragile_items(self, service):
        inv = Invoice("I-002", "C-002", "TH", "none", None, [
            LineItem("B", "electronics", 500.0, 1, fragile=True)
        ])
        total, warnings = service.compute_total(inv)
        assert total > 0

    def test_high_value_membership_warning(self, service):
        inv = Invoice("I-003", "C-003", "TH", "none", None, [
            LineItem("C", "electronics", 5000.0, 3)
        ])
        total, warnings = service.compute_total(inv)
        assert "Consider membership upgrade" in warnings

    def test_platinum_no_upgrade_warning(self, service):
        inv = Invoice("I-004", "C-004", "TH", "platinum", None, [
            LineItem("D", "electronics", 5000.0, 3)
        ])
        total, warnings = service.compute_total(inv)
        assert "Consider membership upgrade" not in warnings

    def test_negative_total_becomes_zero(self, service):
        inv = Invoice("I-005", "C-005", "TH", "platinum", "VIP20", [
            LineItem("E", "food", 10.0, 1)
        ])
        total, warnings = service.compute_total(inv)
        assert total >= 0.0

    def test_multiple_items(self, service):
        inv = Invoice("I-006", "C-006", "US", "gold", "WELCOME10", [
            LineItem("F", "book", 100.0, 2),
            LineItem("G", "electronics", 500.0, 1, fragile=True),
            LineItem("H", "food", 50.0, 3)
        ])
        total, warnings = service.compute_total(inv)
        assert total > 0
