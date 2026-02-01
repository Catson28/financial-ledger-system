#!/usr/bin/env python3
"""
Ledger System - Test Suite
===========================
Comprehensive test suite for the Ledger / Accounting Engine.

Run tests:
    pytest test_ledger.py -v
    pytest test_ledger.py -v --cov=.
"""

import pytest
from datetime import datetime, timezone
from decimal import Decimal
import os
import tempfile
from pathlib import Path

from src.ledger_engine import (
    LedgerEngine, AccountDefinition, AccountType,
    TransactionInput, JournalEntryInput, EntryType
)
from src.ledger_reporting import LedgerReportEngine


@pytest.fixture(scope="function")
def ledger():
    """Create ledger instance for testing.
    
    Uses function scope with a unique temporary SQLite file for each test.
    This ensures complete isolation between tests.
    """
    # Save original URI
    original_uri = os.environ.get('LEDGER_DB_URI')
    
    # Create a temporary file for this test's database
    temp_db = tempfile.NamedTemporaryFile(mode='w', suffix='.db', delete=False)
    temp_db_path = temp_db.name
    temp_db.close()
    
    # Set up the test database URI
    test_db_uri = f'sqlite:///{temp_db_path}'
    os.environ['LEDGER_DB_URI'] = test_db_uri
    
    # Create new engine instance
    engine = LedgerEngine()
    
    # Yield the engine for the test
    yield engine
    
    # Cleanup: Close connections and delete temporary database
    try:
        engine.engine.dispose()
    except:
        pass
    
    # Remove temporary database file
    try:
        Path(temp_db_path).unlink()
    except:
        pass
    
    # Restore original URI
    if original_uri:
        os.environ['LEDGER_DB_URI'] = original_uri
    else:
        os.environ.pop('LEDGER_DB_URI', None)


@pytest.fixture(scope="function")
def ledger_with_accounts(ledger):
    """Create ledger with sample accounts."""
    # Create sample accounts
    accounts = [
        AccountDefinition("1000", "Assets", AccountType.ASSET),
        AccountDefinition("1100", "Cash", AccountType.ASSET, "1000"),
        AccountDefinition("1200", "Accounts Receivable", AccountType.ASSET, "1000"),
        AccountDefinition("2000", "Liabilities", AccountType.LIABILITY),
        AccountDefinition("2100", "Accounts Payable", AccountType.LIABILITY, "2000"),
        AccountDefinition("3000", "Equity", AccountType.EQUITY),
        AccountDefinition("4000", "Revenue", AccountType.REVENUE),
        AccountDefinition("4100", "Sales Revenue", AccountType.REVENUE, "4000"),
        AccountDefinition("5000", "Expenses", AccountType.EXPENSE),
        AccountDefinition("5100", "Cost of Sales", AccountType.EXPENSE, "5000"),
    ]
    
    for account_def in accounts:
        ledger.create_account(account_def, created_by="test_user")
    
    return ledger


class TestChartOfAccounts:
    """Test Chart of Accounts functionality."""
    
    def test_create_account(self, ledger):
        """Test account creation."""
        account_def = AccountDefinition(
            account_code="1100",
            account_name="Cash",
            account_type=AccountType.ASSET,
            description="Main cash account"
        )
        
        account_id = ledger.create_account(account_def, created_by="test_user")
        
        assert account_id is not None
        assert len(account_id) == 36  # UUID length
    
    def test_create_duplicate_account(self, ledger):
        """Test that duplicate account codes are rejected."""
        account_def = AccountDefinition(
            account_code="1100",
            account_name="Cash",
            account_type=AccountType.ASSET
        )
        
        ledger.create_account(account_def, created_by="test_user")
        
        with pytest.raises(ValueError, match="already exists"):
            ledger.create_account(account_def, created_by="test_user")
    
    def test_create_account_with_parent(self, ledger):
        """Test hierarchical account creation."""
        # Create parent
        parent_def = AccountDefinition(
            account_code="1000",
            account_name="Assets",
            account_type=AccountType.ASSET
        )
        ledger.create_account(parent_def, created_by="test_user")
        
        # Create child
        child_def = AccountDefinition(
            account_code="1100",
            account_name="Cash",
            account_type=AccountType.ASSET,
            parent_account_code="1000"
        )
        child_id = ledger.create_account(child_def, created_by="test_user")
        
        assert child_id is not None
    
    def test_get_account(self, ledger_with_accounts):
        """Test account retrieval."""
        account = ledger_with_accounts.get_account("1100")
        
        assert account is not None
        assert account['account_code'] == "1100"
        assert account['account_name'] == "Cash"
        assert account['account_type'] == "ASSET"


class TestTransactions:
    """Test transaction posting and management."""
    
    def test_post_simple_transaction(self, ledger_with_accounts):
        """Test posting a simple transaction."""
        entries = [
            JournalEntryInput(
                account_code="1100",
                entry_type=EntryType.DEBIT,
                amount=Decimal("1000.00")
            ),
            JournalEntryInput(
                account_code="4100",
                entry_type=EntryType.CREDIT,
                amount=Decimal("1000.00")
            )
        ]
        
        transaction = TransactionInput(
            business_event_type="SALE",
            description="Test sale",
            transaction_date=datetime.now(timezone.utc),
            entries=entries
        )
        
        txn_id = ledger_with_accounts.post_transaction(
            transaction,
            created_by="test_user",
            source_system="TEST"
        )
        
        assert txn_id is not None
    
    def test_post_unbalanced_transaction(self, ledger_with_accounts):
        """Test that unbalanced transactions are rejected."""
        entries = [
            JournalEntryInput(
                account_code="1100",
                entry_type=EntryType.DEBIT,
                amount=Decimal("1000.00")
            ),
            JournalEntryInput(
                account_code="4100",
                entry_type=EntryType.CREDIT,
                amount=Decimal("500.00")  # Unbalanced!
            )
        ]
        
        transaction = TransactionInput(
            business_event_type="SALE",
            description="Test sale",
            transaction_date=datetime.now(timezone.utc),
            entries=entries
        )
        
        with pytest.raises(ValueError, match="Double-entry violation"):
            ledger_with_accounts.post_transaction(
                transaction,
                created_by="test_user",
                source_system="TEST"
            )
    
    def test_post_transaction_with_invalid_account(self, ledger_with_accounts):
        """Test that transactions with invalid accounts are rejected."""
        entries = [
            JournalEntryInput(
                account_code="9999",  # Invalid account
                entry_type=EntryType.DEBIT,
                amount=Decimal("1000.00")
            ),
            JournalEntryInput(
                account_code="4100",
                entry_type=EntryType.CREDIT,
                amount=Decimal("1000.00")
            )
        ]
        
        transaction = TransactionInput(
            business_event_type="SALE",
            description="Test sale",
            transaction_date=datetime.now(timezone.utc),
            entries=entries
        )
        
        with pytest.raises(ValueError, match="not found"):
            ledger_with_accounts.post_transaction(
                transaction,
                created_by="test_user",
                source_system="TEST"
            )
    
    def test_reverse_transaction(self, ledger_with_accounts):
        """Test transaction reversal."""
        # Post original transaction
        entries = [
            JournalEntryInput(
                account_code="1100",
                entry_type=EntryType.DEBIT,
                amount=Decimal("1000.00")
            ),
            JournalEntryInput(
                account_code="4100",
                entry_type=EntryType.CREDIT,
                amount=Decimal("1000.00")
            )
        ]
        
        transaction = TransactionInput(
            business_event_type="SALE",
            description="Test sale",
            transaction_date=datetime.now(timezone.utc),
            entries=entries
        )
        
        original_txn_id = ledger_with_accounts.post_transaction(
            transaction,
            created_by="test_user",
            source_system="TEST"
        )
        
        # Reverse
        reversal_txn_id = ledger_with_accounts.reverse_transaction(
            original_transaction_id=original_txn_id,
            reversal_reason="Test reversal",
            created_by="test_user",
            source_system="TEST"
        )
        
        assert reversal_txn_id is not None
        assert reversal_txn_id != original_txn_id


class TestBalances:
    """Test balance calculations."""
    
    def test_account_balance_after_transaction(self, ledger_with_accounts):
        """Test account balance calculation."""
        # Post transaction
        entries = [
            JournalEntryInput(
                account_code="1100",
                entry_type=EntryType.DEBIT,
                amount=Decimal("1000.00")
            ),
            JournalEntryInput(
                account_code="4100",
                entry_type=EntryType.CREDIT,
                amount=Decimal("1000.00")
            )
        ]
        
        transaction = TransactionInput(
            business_event_type="SALE",
            description="Test sale",
            transaction_date=datetime.now(timezone.utc),
            entries=entries
        )
        
        ledger_with_accounts.post_transaction(
            transaction,
            created_by="test_user",
            source_system="TEST"
        )
        
        # Check balances
        cash_balance = ledger_with_accounts.get_account_balance("1100")
        revenue_balance = ledger_with_accounts.get_account_balance("4100")
        
        # For ASSET accounts, debit increases balance (positive)
        assert cash_balance == Decimal("1000.00")
        # For REVENUE accounts, credit increases balance (positive)
        assert revenue_balance == Decimal("1000.00")
    
    def test_balance_after_reversal(self, ledger_with_accounts):
        """Test that balances return to zero after reversal."""
        # Post transaction
        entries = [
            JournalEntryInput(
                account_code="1100",
                entry_type=EntryType.DEBIT,
                amount=Decimal("1000.00")
            ),
            JournalEntryInput(
                account_code="4100",
                entry_type=EntryType.CREDIT,
                amount=Decimal("1000.00")
            )
        ]
        
        transaction = TransactionInput(
            business_event_type="SALE",
            description="Test sale",
            transaction_date=datetime.now(timezone.utc),
            entries=entries
        )
        
        original_txn_id = ledger_with_accounts.post_transaction(
            transaction,
            created_by="test_user",
            source_system="TEST"
        )
        
        # Reverse
        ledger_with_accounts.reverse_transaction(
            original_transaction_id=original_txn_id,
            reversal_reason="Test",
            created_by="test_user",
            source_system="TEST"
        )
        
        # Check balances are zero
        cash_balance = ledger_with_accounts.get_account_balance("1100")
        revenue_balance = ledger_with_accounts.get_account_balance("4100")
        
        assert cash_balance == Decimal("0.00")
        assert revenue_balance == Decimal("0.00")


class TestIntegrity:
    """Test data integrity and validation."""
    
    def test_verify_integrity_valid(self, ledger_with_accounts):
        """Test integrity verification on valid ledger."""
        # Post balanced transaction
        entries = [
            JournalEntryInput(
                account_code="1100",
                entry_type=EntryType.DEBIT,
                amount=Decimal("1000.00")
            ),
            JournalEntryInput(
                account_code="4100",
                entry_type=EntryType.CREDIT,
                amount=Decimal("1000.00")
            )
        ]
        
        transaction = TransactionInput(
            business_event_type="SALE",
            description="Test sale",
            transaction_date=datetime.now(timezone.utc),
            entries=entries
        )
        
        ledger_with_accounts.post_transaction(
            transaction,
            created_by="test_user",
            source_system="TEST"
        )
        
        # Verify
        is_valid, errors = ledger_with_accounts.verify_double_entry_integrity()
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_trial_balance(self, ledger_with_accounts):
        """Test trial balance generation."""
        # Post some transactions
        transactions = [
            (Decimal("1000.00"), "1100", "4100", "Sale 1"),
            (Decimal("500.00"), "1100", "4100", "Sale 2"),
            (Decimal("300.00"), "5100", "1100", "Expense 1"),
        ]
        
        for amount, debit_acc, credit_acc, desc in transactions:
            entries = [
                JournalEntryInput(
                    account_code=debit_acc,
                    entry_type=EntryType.DEBIT,
                    amount=amount
                ),
                JournalEntryInput(
                    account_code=credit_acc,
                    entry_type=EntryType.CREDIT,
                    amount=amount
                )
            ]
            
            transaction = TransactionInput(
                business_event_type="TEST",
                description=desc,
                transaction_date=datetime.now(timezone.utc),
                entries=entries
            )
            
            ledger_with_accounts.post_transaction(
                transaction,
                created_by="test_user",
                source_system="TEST"
            )
        
        # Get trial balance
        trial_balance = ledger_with_accounts.get_trial_balance()
        
        assert len(trial_balance) > 0


class TestReporting:
    """Test reporting functionality."""
    
    def test_generate_balance_sheet(self, ledger_with_accounts):
        """Test balance sheet generation."""
        # Post transaction
        entries = [
            JournalEntryInput(
                account_code="1100",
                entry_type=EntryType.DEBIT,
                amount=Decimal("1000.00")
            ),
            JournalEntryInput(
                account_code="4100",
                entry_type=EntryType.CREDIT,
                amount=Decimal("1000.00")
            )
        ]
        
        transaction = TransactionInput(
            business_event_type="SALE",
            description="Test sale",
            transaction_date=datetime.now(timezone.utc),
            entries=entries
        )
        
        ledger_with_accounts.post_transaction(
            transaction,
            created_by="test_user",
            source_system="TEST"
        )
        
        # Generate report
        report_engine = LedgerReportEngine(ledger_with_accounts)
        report = report_engine.generate_balance_sheet(
            as_of_date=datetime.now(timezone.utc),
            generated_by="test_user"
        )
        
        assert report['report_type'] == 'BALANCE_SHEET'
        assert 'assets' in report
        assert 'report_hash' in report
    
    def test_report_integrity_verification(self, ledger_with_accounts):
        """Test report integrity verification."""
        report_engine = LedgerReportEngine(ledger_with_accounts)
        
        report = report_engine.generate_trial_balance(
            as_of_date=datetime.now(timezone.utc),
            generated_by="test_user"
        )
        
        # Verify integrity
        is_valid = report_engine.verify_report_integrity(report)
        assert is_valid is True
        
        # Tamper with report
        report['accounts'] = []
        is_valid = report_engine.verify_report_integrity(report)
        assert is_valid is False


def test_full_workflow(ledger_with_accounts):
    """Test complete workflow from account creation to reporting."""
    # 1. Post multiple transactions
    transactions = [
        # Sale
        ([
            JournalEntryInput("1100", EntryType.DEBIT, Decimal("1000.00")),
            JournalEntryInput("4100", EntryType.CREDIT, Decimal("1000.00"))
        ], "SALE", "Sale transaction"),
        
        # Expense
        ([
            JournalEntryInput("5100", EntryType.DEBIT, Decimal("300.00")),
            JournalEntryInput("1100", EntryType.CREDIT, Decimal("300.00"))
        ], "EXPENSE", "Expense transaction"),
    ]
    
    for entries, event_type, desc in transactions:
        transaction = TransactionInput(
            business_event_type=event_type,
            description=desc,
            transaction_date=datetime.now(timezone.utc),
            entries=entries
        )
        
        ledger_with_accounts.post_transaction(
            transaction,
            created_by="test_user",
            source_system="TEST"
        )
    
    # 2. Verify integrity
    is_valid, errors = ledger_with_accounts.verify_double_entry_integrity()
    assert is_valid is True
    
    # 3. Check balances
    cash_balance = ledger_with_accounts.get_account_balance("1100")
    assert cash_balance == Decimal("700.00")  # 1000 - 300
    
    # 4. Generate reports
    report_engine = LedgerReportEngine(ledger_with_accounts)
    
    balance_sheet = report_engine.generate_balance_sheet(
        as_of_date=datetime.now(timezone.utc),
        generated_by="test_user"
    )
    
    income_statement = report_engine.generate_income_statement(
        start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
        end_date=datetime.now(timezone.utc),
        generated_by="test_user"
    )
    
    assert balance_sheet['report_type'] == 'BALANCE_SHEET'
    assert income_statement['report_type'] == 'INCOME_STATEMENT'
    
    # 5. Verify report integrity
    assert report_engine.verify_report_integrity(balance_sheet) is True
    assert report_engine.verify_report_integrity(income_statement) is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=."])