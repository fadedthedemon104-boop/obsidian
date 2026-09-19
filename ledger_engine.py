"""
Ledger Engine Core: high-precision double-entry transaction processor,
checksum validation, and clearing pipeline.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
import re
from typing import Dict, List


class TransactionType(str, Enum):
    ACH_CREDIT = "ACH_CREDIT"
    CHECK_DEPOSIT = "CHECK_DEPOSIT"
    INTERNAL_TRANSFER = "INTERNAL_TRANSFER"
    FEE = "FEE"


class AccountStatus(str, Enum):
    ACTIVE = "ACTIVE"
    RESTRICTED = "RESTRICTED"
    PENDING_VERIFICATION = "PENDING_VERIFICATION"


class ChecksumValidator:
    """Mod-10 (Luhn) check and validation algorithm."""

    @staticmethod
    def is_luhn_valid(number_str: str) -> bool:
        clean = re.sub(r"\D", "", number_str)
        if len(clean) < 2:
            return False

        digits = [int(d) for d in clean]
        checksum = 0
        for idx, digit in enumerate(reversed(digits)):
            if idx % 2 == 1:
                doubled = digit * 2
                checksum += (doubled - 9) if doubled > 9 else doubled
            else:
                checksum += digit

        return checksum % 10 == 0

    @staticmethod
    def generate_luhn_check_digit(payload_str: str) -> int:
        clean = re.sub(r"\D", "", payload_str)
        if not clean:
            raise ValueError("Payload must contain at least one digit.")

        checksum = 0
        for idx, digit in enumerate(reversed([int(d) for d in clean])):
            if idx % 2 == 0:
                doubled = digit * 2
                checksum += (doubled - 9) if doubled > 9 else doubled
            else:
                checksum += digit

        return (10 - checksum % 10) % 10


class TransitDecoder:
    """Parses US check fractional routing strings and raw MICR lines."""

    @staticmethod
    def parse_fractional(fraction: str) -> Dict[str, str]:
        pattern = r"^(\d{1,2})-(\d{1,4})/(\d{3,4})$"
        match = re.match(pattern, fraction.strip())
        if not match:
            raise ValueError(f"Invalid fractional transit string: {fraction}")

        prefix, transit, routing_district = match.groups()
        standard_transit = f"{routing_district.zfill(4)}{transit.zfill(4)}"
        return {
            "prefix": prefix,
            "transit_id": transit,
            "district": routing_district,
            "computed_transit_lead": standard_transit,
        }

    @staticmethod
    def parse_micr(raw_stream: str) -> Dict[str, str]:
        tokens = raw_stream.strip().split()
        if len(tokens) != 2:
            raise ValueError("Expected two-token MICR payload (serial + transit/on-us).")

        serial_or_account, data_line = tokens
        return {
            "serial_number": serial_or_account,
            "routing_prefix": data_line[:8],
            "auxiliary_on_us": data_line[8:],
            "raw": raw_stream,
        }


@dataclass(frozen=True)
class JournalEntry:
    account_id: str
    amount: Decimal  # Debit = negative, Credit = positive
    timestamp: datetime
    memo: str


@dataclass
class Transaction:
    tx_id: str
    tx_type: TransactionType
    entries: List[JournalEntry]
    reference_id: str
    cleared: bool = False
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class DoubleEntryLedger:
    def __init__(self):
        self.accounts: Dict[str, Dict] = {}
        self.transactions: List[Transaction] = []

    def register_account(
        self,
        account_id: str,
        owner: str,
        institution: str,
        routing_number: str,
        account_number: str,
    ) -> None:
        self.accounts[account_id] = {
            "owner": owner,
            "institution": institution,
            "routing": routing_number,
            "account_number": account_number,
            "balance": Decimal("0.00"),
            "status": AccountStatus.ACTIVE,
        }

    def get_balance(self, account_id: str) -> Decimal:
        if account_id not in self.accounts:
            raise KeyError(f"Account {account_id} not registered.")
        return self.accounts[account_id]["balance"]

    def execute_transaction(
        self,
        tx_id: str,
        tx_type: TransactionType,
        debit_acct: str,
        credit_acct: str,
        amount: Decimal,
        memo: str,
        ref: str,
    ) -> Transaction:
        """Enforces strictly balanced double-entry accounting."""
        if amount <= Decimal("0.00"):
            raise ValueError("Transaction amount must be strictly positive.")
        if debit_acct not in self.accounts or credit_acct not in self.accounts:
            raise KeyError("Both debit and credit accounts must be registered.")
        if debit_acct == credit_acct:
            raise ValueError("Debit and credit accounts must be different.")
        if any(tx.tx_id == tx_id for tx in self.transactions):
            raise ValueError(f"Transaction {tx_id} already exists.")

        quantized_amount = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if quantized_amount <= Decimal("0.00"):
            raise ValueError("Transaction amount must round to at least $0.01.")

        now = datetime.now(timezone.utc)
        entries = [
            JournalEntry(debit_acct, -quantized_amount, now, memo),
            JournalEntry(credit_acct, quantized_amount, now, memo),
        ]
        if sum((entry.amount for entry in entries), Decimal("0.00")) != Decimal("0.00"):
            raise ValueError("Transaction entries must be balanced.")

        self.accounts[debit_acct]["balance"] -= quantized_amount
        self.accounts[credit_acct]["balance"] += quantized_amount
        tx = Transaction(tx_id, tx_type, entries, ref, cleared=True, timestamp=now)
        self.transactions.append(tx)
        return tx
