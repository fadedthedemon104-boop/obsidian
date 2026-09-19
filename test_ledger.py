"""Unit and regression tests verifying mathematical and transactional invariants."""
from decimal import Decimal

import pytest

from ledger_engine import (
    ChecksumValidator,
    DoubleEntryLedger,
    TransactionType,
    TransitDecoder,
)


@pytest.fixture
def active_ledger():
    ledger = DoubleEntryLedger()
    ledger.register_account(
        account_id="ACC_ARCANA_CASHAPP_01",
        owner="Arcana Deluminia",
        institution="Block Inc, c/o Sutton Bank",
        routing_number="041215663",
        account_number="1286315563290",
    )
    ledger.register_account(
        account_id="ACC_FED_ACH_CLEARING",
        owner="Federal Reserve Clearing",
        institution="FRB",
        routing_number="000000000",
        account_number="CLEARING-001",
    )
    return ledger


def test_luhn_algorithm():
    assert not ChecksumValidator.is_luhn_valid("345678901234")
    check_digit = ChecksumValidator.generate_luhn_check_digit("34567890123")
    assert ChecksumValidator.is_luhn_valid(f"34567890123{check_digit}")


def test_transit_fraction_parsing():
    parsed = TransitDecoder.parse_fractional("56-503/422")
    assert parsed["district"] == "422"
    assert parsed["transit_id"] == "503"
    assert parsed["computed_transit_lead"] == "04220503"


def test_double_entry_balance(active_ledger):
    tx = active_ledger.execute_transaction(
        tx_id="TX_TEST_001",
        tx_type=TransactionType.ACH_CREDIT,
        debit_acct="ACC_FED_ACH_CLEARING",
        credit_acct="ACC_ARCANA_CASHAPP_01",
        amount=Decimal("150.00"),
        memo="TEST DEPOSIT",
        ref="REF-001",
    )
    assert tx.cleared is True
    assert active_ledger.get_balance("ACC_ARCANA_CASHAPP_01") == Decimal("150.00")
    assert active_ledger.get_balance("ACC_FED_ACH_CLEARING") == Decimal("-150.00")
