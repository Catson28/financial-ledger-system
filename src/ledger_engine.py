#!/usr/bin/env python3
"""
Ledger Engine - Core Accounting System
=======================================
Motor de contabilidade imutável com dupla entrada.

Este módulo implementa o núcleo do sistema de ledger,
garantindo imutabilidade, auditabilidade e conformidade contábil.

Princípios:
- Imutabilidade: Nada é apagado ou atualizado
- Dupla entrada: Débitos = Créditos sempre
- Auditabilidade: Trilha completa de eventos
- Atomicidade: Transações são atômicas
- Correção por estorno: Erros são corrigidos, não removidos

Version: 1.0.0
"""

import os
import uuid
import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from dataclasses import dataclass, asdict
from sqlalchemy import (
    create_engine, Column, String, DateTime, Numeric, 
    Boolean, Text, Index, CheckConstraint, ForeignKey
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()


class AccountType(Enum):
    """Account types in double-entry accounting."""
    ASSET = "ASSET"              # Ativo
    LIABILITY = "LIABILITY"      # Passivo
    EQUITY = "EQUITY"            # Patrimônio Líquido
    REVENUE = "REVENUE"          # Receita
    EXPENSE = "EXPENSE"          # Despesa


class EntryType(Enum):
    """Entry type in double-entry accounting."""
    DEBIT = "DEBIT"      # Débito
    CREDIT = "CREDIT"    # Crédito


class TransactionStatus(Enum):
    """Transaction status."""
    PENDING = "PENDING"
    POSTED = "POSTED"
    REVERSED = "REVERSED"
    CANCELLED = "CANCELLED"


class SeverityLevel(Enum):
    """Severity level for events."""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


# ========================
# DATABASE MODELS
# ========================

class ChartOfAccounts(Base):
    """Chart of Accounts - Plano de Contas."""
    __tablename__ = 'chart_of_accounts'
    
    account_id = Column(String(36), primary_key=True)
    account_code = Column(String(50), unique=True, nullable=False, index=True)
    account_name = Column(String(200), nullable=False)
    account_type = Column(String(20), nullable=False)  # AccountType
    parent_account_id = Column(String(36), ForeignKey('chart_of_accounts.account_id'), nullable=True)
    level = Column(Numeric(2, 0), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    description = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), nullable=False)
    created_by = Column(String(200), nullable=False)
    version = Column(Numeric(10, 0), default=1, nullable=False)
    
    __table_args__ = (
        Index('idx_account_code', 'account_code'),
        Index('idx_account_type', 'account_type'),
        Index('idx_parent_account', 'parent_account_id'),
    )


class Transaction(Base):
    """Transaction header - immutable."""
    __tablename__ = 'transactions'
    
    transaction_id = Column(String(36), primary_key=True)
    transaction_number = Column(String(50), unique=True, nullable=False, index=True)
    transaction_date = Column(DateTime(timezone=True), nullable=False, index=True)
    posting_date = Column(DateTime(timezone=True), nullable=True)
    
    # Business context
    business_event_type = Column(String(100), nullable=False)
    business_key = Column(String(200), nullable=True, index=True)
    reference_number = Column(String(100), nullable=True)
    description = Column(Text, nullable=False)
    
    # Status
    status = Column(String(20), nullable=False, default='PENDING')  # TransactionStatus
    
    # Reversal tracking
    is_reversal = Column(Boolean, default=False, nullable=False)
    reverses_transaction_id = Column(String(36), ForeignKey('transactions.transaction_id'), nullable=True)
    reversed_by_transaction_id = Column(String(36), nullable=True)
    reversal_reason = Column(Text, nullable=True)
    
    # Audit
    created_at = Column(DateTime(timezone=True), nullable=False)
    created_by = Column(String(200), nullable=False)
    source_system = Column(String(100), nullable=False)
    source_ip = Column(String(45), nullable=True)
    
    # Hash for integrity
    transaction_hash = Column(String(64), nullable=False)
    
    __table_args__ = (
        Index('idx_transaction_number', 'transaction_number'),
        Index('idx_transaction_date', 'transaction_date'),
        Index('idx_business_key', 'business_key'),
        Index('idx_status', 'status'),
        Index('idx_reversal', 'is_reversal', 'reverses_transaction_id'),
    )


class JournalEntry(Base):
    """Journal Entry (Ledger Entry) - immutable."""
    __tablename__ = 'journal_entries'
    
    entry_id = Column(String(36), primary_key=True)
    transaction_id = Column(String(36), ForeignKey('transactions.transaction_id'), nullable=False, index=True)
    entry_number = Column(Numeric(5, 0), nullable=False)  # Line number within transaction
    
    # Account
    account_id = Column(String(36), ForeignKey('chart_of_accounts.account_id'), nullable=False, index=True)
    account_code = Column(String(50), nullable=False, index=True)
    
    # Entry details
    entry_type = Column(String(10), nullable=False)  # DEBIT or CREDIT
    amount = Column(Numeric(20, 2), nullable=False)
    currency = Column(String(3), default='AOA', nullable=False)
    
    # Additional context
    cost_center = Column(String(50), nullable=True)
    business_unit = Column(String(50), nullable=True)
    project_code = Column(String(50), nullable=True)
    memo = Column(Text, nullable=True)
    
    # Audit
    created_at = Column(DateTime(timezone=True), nullable=False)
    
    __table_args__ = (
        CheckConstraint('amount > 0', name='check_amount_positive'),
        Index('idx_transaction_entry', 'transaction_id', 'entry_number'),
        Index('idx_account_code', 'account_code'),
        Index('idx_entry_type', 'entry_type'),
    )


class ClosingPeriod(Base):
    """Closing periods for accounting."""
    __tablename__ = 'closing_periods'
    
    closing_id = Column(String(36), primary_key=True)
    period_type = Column(String(20), nullable=False)  # DAILY, MONTHLY, QUARTERLY, ANNUAL
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    
    # Status
    is_closed = Column(Boolean, default=False, nullable=False)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    closed_by = Column(String(200), nullable=True)
    
    # Balances snapshot
    total_debits = Column(Numeric(20, 2), nullable=True)
    total_credits = Column(Numeric(20, 2), nullable=True)
    balance_check = Column(Boolean, nullable=True)
    
    # Audit
    created_at = Column(DateTime(timezone=True), nullable=False)
    
    __table_args__ = (
        Index('idx_period_type', 'period_type'),
        Index('idx_period_dates', 'period_start', 'period_end'),
        Index('idx_is_closed', 'is_closed'),
    )


class AuditLog(Base):
    """Comprehensive audit log."""
    __tablename__ = 'audit_log'
    
    audit_id = Column(String(36), primary_key=True)
    event_timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    event_type = Column(String(100), nullable=False)
    severity = Column(String(20), nullable=False)  # SeverityLevel
    
    # Related entities
    transaction_id = Column(String(36), nullable=True, index=True)
    user_id = Column(String(200), nullable=False)
    source_system = Column(String(100), nullable=False)
    source_ip = Column(String(45), nullable=True)
    
    # Event details
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50), nullable=True)
    entity_id = Column(String(36), nullable=True)
    
    # Context
    description = Column(Text, nullable=False)
    event_metadata = Column(Text, nullable=True)  # JSON
    
    __table_args__ = (
        Index('idx_event_timestamp', 'event_timestamp'),
        Index('idx_transaction_id', 'transaction_id'),
        Index('idx_user_id', 'user_id'),
        Index('idx_severity', 'severity'),
    )


# ========================
# DATA CLASSES
# ========================

@dataclass
class AccountDefinition:
    """Account definition."""
    account_code: str
    account_name: str
    account_type: AccountType
    parent_account_code: Optional[str] = None
    description: Optional[str] = None


@dataclass
class JournalEntryInput:
    """Input for creating journal entry."""
    account_code: str
    entry_type: EntryType
    amount: Decimal
    cost_center: Optional[str] = None
    business_unit: Optional[str] = None
    project_code: Optional[str] = None
    memo: Optional[str] = None


@dataclass
class TransactionInput:
    """Input for creating transaction."""
    business_event_type: str
    description: str
    transaction_date: datetime
    entries: List[JournalEntryInput]
    business_key: Optional[str] = None
    reference_number: Optional[str] = None


# ========================
# LEDGER ENGINE
# ========================

class LedgerEngine:
    """
    Core Ledger Engine with Double-Entry Accounting.
    
    This engine ensures:
    - Immutability: Nothing is deleted or updated
    - Double-entry: Debits always equal credits
    - Auditability: Complete audit trail
    - Atomicity: All or nothing transactions
    """
    
    def __init__(self, db_uri: Optional[str] = None):
        """Initialize ledger engine."""
        self.db_uri = db_uri or os.getenv('LEDGER_DB_URI')
        if not self.db_uri:
            raise ValueError("Database URI not configured")
        
        self.engine = create_engine(self.db_uri, pool_pre_ping=True)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # Create tables
        Base.metadata.create_all(self.engine)
    
    def _generate_id(self) -> str:
        """Generate UUID."""
        return str(uuid.uuid4())
    
    def _generate_transaction_number(self, session: Session) -> str:
        """Generate sequential transaction number."""
        # Get current date for prefix
        prefix = datetime.now(timezone.utc).strftime("%Y%m%d")
        
        # Get count of transactions today
        from sqlalchemy import func
        count = session.query(func.count(Transaction.transaction_id))\
            .filter(Transaction.transaction_number.like(f"{prefix}%"))\
            .scalar() or 0
        
        return f"{prefix}-{count + 1:06d}"
    
    def _calculate_hash(self, data: Dict[str, Any]) -> str:
        """Calculate SHA-256 hash of data."""
        json_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    def _log_audit(
        self,
        session: Session,
        event_type: str,
        action: str,
        description: str,
        user_id: str,
        source_system: str,
        severity: SeverityLevel = SeverityLevel.INFO,
        transaction_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
        source_ip: Optional[str] = None
    ):
        """Log audit event."""
        audit = AuditLog(
            audit_id=self._generate_id(),
            event_timestamp=datetime.now(timezone.utc),
            event_type=event_type,
            severity=severity.value,
            transaction_id=transaction_id,
            user_id=user_id,
            source_system=source_system,
            source_ip=source_ip,
            action=action,
            description=description,
            event_metadata=json.dumps(metadata) if metadata else None
        )
        session.add(audit)
    
    # ========================
    # Chart of Accounts
    # ========================
    
    def create_account(
        self,
        account_def: AccountDefinition,
        created_by: str,
        source_system: str = "LEDGER_SYSTEM"
    ) -> str:
        """
        Create account in chart of accounts.
        
        Returns:
            account_id
        """
        with self.SessionLocal() as session:
            try:
                # Check if account code already exists
                existing = session.query(ChartOfAccounts)\
                    .filter(ChartOfAccounts.account_code == account_def.account_code)\
                    .first()
                
                if existing:
                    raise ValueError(f"Account code {account_def.account_code} already exists")
                
                # Get parent if specified
                parent_id = None
                level = 1
                
                if account_def.parent_account_code:
                    parent = session.query(ChartOfAccounts)\
                        .filter(ChartOfAccounts.account_code == account_def.parent_account_code)\
                        .first()
                    
                    if not parent:
                        raise ValueError(f"Parent account {account_def.parent_account_code} not found")
                    
                    parent_id = parent.account_id
                    level = parent.level + 1
                
                # Create account
                account_id = self._generate_id()
                
                account = ChartOfAccounts(
                    account_id=account_id,
                    account_code=account_def.account_code,
                    account_name=account_def.account_name,
                    account_type=account_def.account_type.value,
                    parent_account_id=parent_id,
                    level=level,
                    description=account_def.description,
                    created_at=datetime.now(timezone.utc),
                    created_by=created_by
                )
                
                session.add(account)
                
                # Log audit
                self._log_audit(
                    session=session,
                    event_type="ACCOUNT_CREATED",
                    action="CREATE_ACCOUNT",
                    description=f"Account {account_def.account_code} created",
                    user_id=created_by,
                    source_system=source_system,
                    metadata=asdict(account_def)
                )
                
                session.commit()
                return account_id
            
            except Exception as e:
                session.rollback()
                raise
    
    def get_account(self, account_code: str) -> Optional[Dict]:
        """Get account by code."""
        with self.SessionLocal() as session:
            account = session.query(ChartOfAccounts)\
                .filter(ChartOfAccounts.account_code == account_code)\
                .first()
            
            if not account:
                return None
            
            return {
                'account_id': account.account_id,
                'account_code': account.account_code,
                'account_name': account.account_name,
                'account_type': account.account_type,
                'level': int(account.level),
                'is_active': account.is_active
            }
    
    # ========================
    # Transactions
    # ========================
    
    def post_transaction(
        self,
        transaction_input: TransactionInput,
        created_by: str,
        source_system: str,
        source_ip: Optional[str] = None
    ) -> str:
        """
        Post transaction with double-entry validation.
        
        This is the core method that ensures double-entry integrity.
        
        Returns:
            transaction_id
        """
        with self.SessionLocal() as session:
            try:
                # Validate double-entry balance
                total_debits = Decimal('0')
                total_credits = Decimal('0')
                
                for entry in transaction_input.entries:
                    if entry.entry_type == EntryType.DEBIT:
                        total_debits += entry.amount
                    else:
                        total_credits += entry.amount
                
                # CRITICAL: Debits must equal credits
                if total_debits != total_credits:
                    raise ValueError(
                        f"Double-entry violation: Debits ({total_debits}) != Credits ({total_credits})"
                    )
                
                # Generate transaction ID and number
                transaction_id = self._generate_id()
                transaction_number = self._generate_transaction_number(session)
                
                # Calculate transaction hash
                hash_data = {
                    'transaction_number': transaction_number,
                    'business_event_type': transaction_input.business_event_type,
                    'description': transaction_input.description,
                    'total_debits': str(total_debits),
                    'total_credits': str(total_credits),
                    'created_by': created_by
                }
                transaction_hash = self._calculate_hash(hash_data)
                
                # Create transaction
                transaction = Transaction(
                    transaction_id=transaction_id,
                    transaction_number=transaction_number,
                    transaction_date=transaction_input.transaction_date,
                    posting_date=datetime.now(timezone.utc),
                    business_event_type=transaction_input.business_event_type,
                    business_key=transaction_input.business_key,
                    reference_number=transaction_input.reference_number,
                    description=transaction_input.description,
                    status=TransactionStatus.POSTED.value,
                    created_at=datetime.now(timezone.utc),
                    created_by=created_by,
                    source_system=source_system,
                    source_ip=source_ip,
                    transaction_hash=transaction_hash
                )
                
                session.add(transaction)
                
                # Create journal entries
                for idx, entry_input in enumerate(transaction_input.entries, 1):
                    # Validate account exists
                    account = session.query(ChartOfAccounts)\
                        .filter(ChartOfAccounts.account_code == entry_input.account_code)\
                        .first()
                    
                    if not account:
                        raise ValueError(f"Account {entry_input.account_code} not found")
                    
                    if not account.is_active:
                        raise ValueError(f"Account {entry_input.account_code} is inactive")
                    
                    # Create entry
                    entry = JournalEntry(
                        entry_id=self._generate_id(),
                        transaction_id=transaction_id,
                        entry_number=idx,
                        account_id=account.account_id,
                        account_code=account.account_code,
                        entry_type=entry_input.entry_type.value,
                        amount=entry_input.amount,
                        cost_center=entry_input.cost_center,
                        business_unit=entry_input.business_unit,
                        project_code=entry_input.project_code,
                        memo=entry_input.memo,
                        created_at=datetime.now(timezone.utc)
                    )
                    
                    session.add(entry)
                
                # Log audit
                self._log_audit(
                    session=session,
                    event_type="TRANSACTION_POSTED",
                    action="POST_TRANSACTION",
                    description=f"Transaction {transaction_number} posted",
                    user_id=created_by,
                    source_system=source_system,
                    source_ip=source_ip,
                    transaction_id=transaction_id,
                    metadata={
                        'business_event_type': transaction_input.business_event_type,
                        'total_debits': str(total_debits),
                        'total_credits': str(total_credits),
                        'entry_count': len(transaction_input.entries)
                    }
                )
                
                session.commit()
                return transaction_id
            
            except Exception as e:
                session.rollback()
                self._log_audit(
                    session=session,
                    event_type="TRANSACTION_FAILED",
                    action="POST_TRANSACTION",
                    description=f"Transaction posting failed: {str(e)}",
                    user_id=created_by,
                    source_system=source_system,
                    severity=SeverityLevel.ERROR,
                    metadata={'error': str(e)}
                )
                session.commit()
                raise
    
    def reverse_transaction(
        self,
        original_transaction_id: str,
        reversal_reason: str,
        created_by: str,
        source_system: str,
        source_ip: Optional[str] = None
    ) -> str:
        """
        Reverse a transaction by creating compensating entries.
        
        This follows the immutability principle: we don't delete,
        we create offsetting entries.
        
        Returns:
            reversal_transaction_id
        """
        with self.SessionLocal() as session:
            try:
                # Get original transaction
                original = session.query(Transaction)\
                    .filter(Transaction.transaction_id == original_transaction_id)\
                    .first()
                
                if not original:
                    raise ValueError(f"Transaction {original_transaction_id} not found")
                
                if original.status == TransactionStatus.REVERSED.value:
                    raise ValueError(f"Transaction already reversed")
                
                # Get original entries
                original_entries = session.query(JournalEntry)\
                    .filter(JournalEntry.transaction_id == original_transaction_id)\
                    .order_by(JournalEntry.entry_number)\
                    .all()
                
                # Create reversal entries (flip debit/credit)
                reversal_entries = []
                for entry in original_entries:
                    # Flip entry type
                    reversed_type = EntryType.CREDIT if entry.entry_type == 'DEBIT' else EntryType.DEBIT
                    
                    reversal_entry = JournalEntryInput(
                        account_code=entry.account_code,
                        entry_type=reversed_type,
                        amount=entry.amount,
                        cost_center=entry.cost_center,
                        business_unit=entry.business_unit,
                        project_code=entry.project_code,
                        memo=f"Reversal: {entry.memo or ''}"
                    )
                    reversal_entries.append(reversal_entry)
                
                # Create reversal transaction
                reversal_input = TransactionInput(
                    business_event_type=f"REVERSAL_{original.business_event_type}",
                    description=f"Reversal of {original.transaction_number}: {reversal_reason}",
                    transaction_date=datetime.now(timezone.utc),
                    entries=reversal_entries,
                    business_key=original.business_key,
                    reference_number=original.transaction_number
                )
                
                reversal_id = self.post_transaction(
                    reversal_input,
                    created_by,
                    source_system,
                    source_ip
                )
                
                # Update original transaction status
                original.status = TransactionStatus.REVERSED.value
                original.reversed_by_transaction_id = reversal_id
                
                # Update reversal transaction
                reversal = session.query(Transaction)\
                    .filter(Transaction.transaction_id == reversal_id)\
                    .first()
                
                reversal.is_reversal = True
                reversal.reverses_transaction_id = original_transaction_id
                reversal.reversal_reason = reversal_reason
                
                # Log audit
                self._log_audit(
                    session=session,
                    event_type="TRANSACTION_REVERSED",
                    action="REVERSE_TRANSACTION",
                    description=f"Transaction {original.transaction_number} reversed",
                    user_id=created_by,
                    source_system=source_system,
                    source_ip=source_ip,
                    transaction_id=original_transaction_id,
                    metadata={
                        'reversal_transaction_id': reversal_id,
                        'reversal_reason': reversal_reason
                    },
                    severity=SeverityLevel.WARNING
                )
                
                session.commit()
                return reversal_id
            
            except Exception as e:
                session.rollback()
                raise
    
    # ========================
    # Balances and Reports
    # ========================
    
    def get_account_balance(
        self,
        account_code: str,
        as_of_date: Optional[datetime] = None
    ) -> Decimal:
        """
        Get account balance as of a specific date.
        
        Balance calculation respects account type:
        - Assets & Expenses: Debit increases, Credit decreases
        - Liabilities, Equity & Revenue: Credit increases, Debit decreases
        """
        with self.SessionLocal() as session:
            # Get account
            account = session.query(ChartOfAccounts)\
                .filter(ChartOfAccounts.account_code == account_code)\
                .first()
            
            if not account:
                raise ValueError(f"Account {account_code} not found")
            
            # Build query
            query = session.query(JournalEntry)\
                .join(Transaction)\
                .filter(
                    JournalEntry.account_code == account_code,
                    Transaction.status == TransactionStatus.POSTED.value
                )
            
            if as_of_date:
                query = query.filter(Transaction.posting_date <= as_of_date)
            
            entries = query.all()
            
            # Calculate balance based on account type
            total_debits = Decimal('0')
            total_credits = Decimal('0')
            
            for entry in entries:
                if entry.entry_type == 'DEBIT':
                    total_debits += entry.amount
                else:
                    total_credits += entry.amount
            
            # Calculate balance based on account type
            account_type = AccountType(account.account_type)
            
            if account_type in [AccountType.ASSET, AccountType.EXPENSE]:
                balance = total_debits - total_credits
            else:  # LIABILITY, EQUITY, REVENUE
                balance = total_credits - total_debits
            
            return balance
    
    def verify_double_entry_integrity(
        self,
        transaction_id: Optional[str] = None
    ) -> Tuple[bool, List[str]]:
        """
        Verify double-entry integrity.
        
        Returns:
            (is_valid, error_messages)
        """
        with self.SessionLocal() as session:
            errors = []
            
            # Build query
            query = session.query(Transaction)\
                .filter(Transaction.status == TransactionStatus.POSTED.value)
            
            if transaction_id:
                query = query.filter(Transaction.transaction_id == transaction_id)
            
            transactions = query.all()
            
            for txn in transactions:
                # Get entries
                entries = session.query(JournalEntry)\
                    .filter(JournalEntry.transaction_id == txn.transaction_id)\
                    .all()
                
                total_debits = Decimal('0')
                total_credits = Decimal('0')
                
                for entry in entries:
                    if entry.entry_type == 'DEBIT':
                        total_debits += entry.amount
                    else:
                        total_credits += entry.amount
                
                if total_debits != total_credits:
                    errors.append(
                        f"Transaction {txn.transaction_number}: "
                        f"Debits ({total_debits}) != Credits ({total_credits})"
                    )
            
            return (len(errors) == 0, errors)
    
    def get_trial_balance(
        self,
        as_of_date: Optional[datetime] = None
    ) -> List[Dict]:
        """
        Get trial balance report.
        
        Returns list of accounts with debits, credits, and balances.
        """
        with self.SessionLocal() as session:
            # Get all active accounts
            accounts = session.query(ChartOfAccounts)\
                .filter(ChartOfAccounts.is_active == True)\
                .order_by(ChartOfAccounts.account_code)\
                .all()
            
            trial_balance = []
            
            for account in accounts:
                balance = self.get_account_balance(account.account_code, as_of_date)
                
                trial_balance.append({
                    'account_code': account.account_code,
                    'account_name': account.account_name,
                    'account_type': account.account_type,
                    'balance': balance
                })
            
            return trial_balance


def main():
    """Example usage."""
    # This would be configured via environment or config file
    print("Ledger Engine - Core Module")
    print("Use this module in your application by importing LedgerEngine")


if __name__ == "__main__":
    main()