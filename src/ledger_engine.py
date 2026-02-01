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
    Boolean, Text, Index, CheckConstraint, ForeignKey, text
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
    account_code = Column(String(50), unique=True, nullable=False)  # Index in __table_args__
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
        Index('idx_coa_account_code', 'account_code'),
        Index('idx_coa_account_type', 'account_type'),
        Index('idx_coa_parent_account', 'parent_account_id'),
    )


class Transaction(Base):
    """Transaction header - immutable."""
    __tablename__ = 'transactions'
    
    transaction_id = Column(String(36), primary_key=True)
    transaction_number = Column(String(50), unique=True, nullable=False)  # Index in __table_args__
    transaction_date = Column(DateTime(timezone=True), nullable=False)  # Index in __table_args__
    posting_date = Column(DateTime(timezone=True), nullable=True)
    
    # Business context
    business_event_type = Column(String(100), nullable=False)
    business_key = Column(String(200), nullable=True)  # Index in __table_args__
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
        Index('idx_txn_number', 'transaction_number'),
        Index('idx_txn_date', 'transaction_date'),
        Index('idx_txn_business_key', 'business_key'),
        Index('idx_txn_status', 'status'),
        Index('idx_txn_reversal', 'is_reversal', 'reverses_transaction_id'),
    )


class JournalEntry(Base):
    """Journal Entry (Ledger Entry) - immutable."""
    __tablename__ = 'journal_entries'
    
    entry_id = Column(String(36), primary_key=True)
    transaction_id = Column(String(36), ForeignKey('transactions.transaction_id'), nullable=False)  # Index in __table_args__
    entry_number = Column(Numeric(5, 0), nullable=False)
    
    # Account reference
    account_id = Column(String(36), ForeignKey('chart_of_accounts.account_id'), nullable=False)
    account_code = Column(String(50), nullable=False)  # Index in __table_args__
    
    # Entry details
    entry_type = Column(String(10), nullable=False)  # DEBIT/CREDIT - Index in __table_args__
    amount = Column(Numeric(20, 2), nullable=False, default=0.00)
    currency = Column(String(3), nullable=False, default='AOA')
    
    # Additional dimensions
    cost_center = Column(String(50), nullable=True)
    department = Column(String(50), nullable=True)
    project = Column(String(50), nullable=True)
    memo = Column(Text, nullable=True)
    
    # Posting info
    posting_date = Column(DateTime(timezone=True), nullable=False)  # Index in __table_args__
    
    # Hash for integrity
    entry_hash = Column(String(64), nullable=False)
    
    __table_args__ = (
        Index('idx_je_txn_id', 'transaction_id'),
        Index('idx_je_account_code', 'account_code'),
        Index('idx_je_entry_type', 'entry_type'),
        Index('idx_je_posting_date', 'posting_date'),
        CheckConstraint('amount >= 0', name='chk_positive_amount'),
        CheckConstraint("entry_type IN ('DEBIT', 'CREDIT')", name='chk_entry_type'),
    )


class AuditLog(Base):
    """Audit Log - immutable event log."""
    __tablename__ = 'audit_log'
    
    audit_id = Column(String(36), primary_key=True)
    event_timestamp = Column(DateTime(timezone=True), nullable=False)  # Index in __table_args__
    
    # Event classification
    event_type = Column(String(100), nullable=False)
    severity = Column(String(20), nullable=False)  # Index in __table_args__
    
    # References
    transaction_id = Column(String(36), ForeignKey('transactions.transaction_id'), nullable=True)  # Index in __table_args__
    user_id = Column(String(200), nullable=False)  # Index in __table_args__
    source_system = Column(String(100), nullable=False)
    source_ip = Column(String(45), nullable=True)
    
    # Action details
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50), nullable=True)
    entity_id = Column(String(36), nullable=True)
    description = Column(Text, nullable=False)
    event_metadata = Column(Text, nullable=True)  # Renamed from metadata
    
    __table_args__ = (
        Index('idx_audit_timestamp', 'event_timestamp'),
        Index('idx_audit_txn_id', 'transaction_id'),
        Index('idx_audit_user_id', 'user_id'),
        Index('idx_audit_severity', 'severity'),
        CheckConstraint("severity IN ('INFO', 'WARNING', 'ERROR', 'CRITICAL')", name='chk_severity'),
    )


# ========================
# INPUT DATA CLASSES
# ========================

@dataclass
class AccountDefinition:
    """Account definition for chart of accounts."""
    account_code: str
    account_name: str
    account_type: AccountType
    parent_account_code: Optional[str] = None
    description: Optional[str] = None
    
    def validate(self) -> None:
        """Validate account definition."""
        if not self.account_code or not self.account_code.strip():
            raise ValueError("Account code is required")
        
        if not self.account_name or not self.account_name.strip():
            raise ValueError("Account name is required")
        
        if not isinstance(self.account_type, AccountType):
            raise ValueError(f"Invalid account type: {self.account_type}")


@dataclass
class JournalEntryInput:
    """Input for a journal entry."""
    account_code: str
    entry_type: EntryType
    amount: Decimal
    cost_center: Optional[str] = None
    department: Optional[str] = None
    project: Optional[str] = None
    memo: Optional[str] = None
    
    def validate(self) -> None:
        """Validate journal entry input."""
        if not self.account_code or not self.account_code.strip():
            raise ValueError("Account code is required")
        
        if not isinstance(self.entry_type, EntryType):
            raise ValueError(f"Invalid entry type: {self.entry_type}")
        
        if not isinstance(self.amount, Decimal):
            raise ValueError("Amount must be a Decimal")
        
        if self.amount < 0:
            raise ValueError("Amount must be non-negative")


@dataclass
class TransactionInput:
    """Input for creating a transaction."""
    business_event_type: str
    description: str
    transaction_date: datetime
    entries: List[JournalEntryInput]
    business_key: Optional[str] = None
    reference_number: Optional[str] = None
    
    def validate(self) -> None:
        """Validate transaction input."""
        if not self.business_event_type or not self.business_event_type.strip():
            raise ValueError("Business event type is required")
        
        if not self.description or not self.description.strip():
            raise ValueError("Description is required")
        
        if not self.entries or len(self.entries) == 0:
            raise ValueError("At least one journal entry is required")
        
        # Validate each entry
        for entry in self.entries:
            entry.validate()
        
        # Verify double entry (debits = credits)
        total_debits = Decimal('0')
        total_credits = Decimal('0')
        
        for entry in self.entries:
            if entry.entry_type == EntryType.DEBIT:
                total_debits += entry.amount
            else:
                total_credits += entry.amount
        
        if total_debits != total_credits:
            raise ValueError(
                f"Transaction not balanced: Debits={total_debits}, Credits={total_credits}"
            )


# ========================
# LEDGER ENGINE
# ========================

class LedgerEngine:
    """
    Core Ledger Engine.
    
    This class implements the double-entry accounting system with:
    - Immutable transactions
    - Full audit trail
    - Cryptographic integrity
    - Support for reversals
    """
    
    def __init__(self, db_uri: Optional[str] = None):
        """
        Initialize Ledger Engine.
        
        Args:
            db_uri: Database connection string. If None, uses LEDGER_DB_URI from environment.
        """
        self.db_uri = db_uri or os.getenv('LEDGER_DB_URI')
        
        if not self.db_uri:
            raise ValueError("Database URI not configured. Set LEDGER_DB_URI environment variable.")
        
        # Create engine
        self.engine = create_engine(
            self.db_uri,
            echo=False,
            pool_pre_ping=True,
            pool_recycle=3600
        )
        
        # Create tables
        Base.metadata.create_all(self.engine)
        
        # Create session factory
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    def _generate_transaction_number(self, session: Session) -> str:
        """Generate sequential transaction number: YYYYMMDD-NNNNNN."""
        today = datetime.now(timezone.utc).strftime('%Y%m%d')
        
        query = """
            SELECT COUNT(*) 
            FROM transactions 
            WHERE transaction_number LIKE :pattern
        """
        
        count = session.execute(
            text(query),
            {'pattern': f"{today}-%"}
        ).scalar()
        
        seq = count + 1 if count else 1
        return f"{today}-{seq:06d}"
    
    def _calculate_transaction_hash(
        self,
        transaction_id: str,
        transaction_date: datetime,
        entries: List[JournalEntryInput]
    ) -> str:
        """
        Calculate cryptographic hash for transaction.
        
        Hash ensures transaction integrity and immutability.
        """
        hash_input = {
            'transaction_id': transaction_id,
            'transaction_date': transaction_date.isoformat(),
            'entries': [
                {
                    'account': e.account_code,
                    'type': e.entry_type.value,
                    'amount': str(e.amount)
                }
                for e in entries
            ]
        }
        
        hash_str = json.dumps(hash_input, sort_keys=True)
        return hashlib.sha256(hash_str.encode()).hexdigest()
    
    def _calculate_entry_hash(
        self,
        entry_id: str,
        transaction_id: str,
        account_code: str,
        entry_type: str,
        amount: Decimal
    ) -> str:
        """Calculate hash for individual entry."""
        hash_input = {
            'entry_id': entry_id,
            'transaction_id': transaction_id,
            'account': account_code,
            'type': entry_type,
            'amount': str(amount)
        }
        
        hash_str = json.dumps(hash_input, sort_keys=True)
        return hashlib.sha256(hash_str.encode()).hexdigest()
    
    def _log_audit(
        self,
        session: Session,
        event_type: str,
        severity: SeverityLevel,
        action: str,
        description: str,
        user_id: str,
        source_system: str,
        transaction_id: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        source_ip: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """Log audit event."""
        audit_id = str(uuid.uuid4())
        
        audit_log = AuditLog(
            audit_id=audit_id,
            event_timestamp=datetime.now(timezone.utc),
            event_type=event_type,
            severity=severity.value,
            transaction_id=transaction_id,
            user_id=user_id,
            source_system=source_system,
            source_ip=source_ip,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            description=description,
            event_metadata=json.dumps(metadata) if metadata else None
        )
        
        session.add(audit_log)
        return audit_id
    
    # ========================
    # Chart of Accounts
    # ========================
    
    def create_account(
        self,
        account_def: AccountDefinition,
        created_by: str
    ) -> str:
        """
        Create a new account in the chart of accounts.
        
        Args:
            account_def: Account definition
            created_by: User creating the account
            
        Returns:
            account_id: UUID of created account
        """
        account_def.validate()
        
        with self.SessionLocal() as session:
            try:
                # Check if account code exists
                existing = session.query(ChartOfAccounts)\
                    .filter(ChartOfAccounts.account_code == account_def.account_code)\
                    .first()
                
                if existing:
                    raise ValueError(f"Account code {account_def.account_code} already exists")
                
                # Determine level and parent
                parent_account = None
                level = 1
                
                if account_def.parent_account_code:
                    parent_account = session.query(ChartOfAccounts)\
                        .filter(ChartOfAccounts.account_code == account_def.parent_account_code)\
                        .first()
                    
                    if not parent_account:
                        raise ValueError(f"Parent account {account_def.parent_account_code} not found")
                    
                    level = parent_account.level + 1
                
                # Create account
                account_id = str(uuid.uuid4())
                
                account = ChartOfAccounts(
                    account_id=account_id,
                    account_code=account_def.account_code,
                    account_name=account_def.account_name,
                    account_type=account_def.account_type.value,
                    parent_account_id=parent_account.account_id if parent_account else None,
                    level=level,
                    is_active=True,
                    description=account_def.description,
                    created_at=datetime.now(timezone.utc),
                    created_by=created_by,
                    version=1
                )
                
                session.add(account)
                
                # Log audit
                self._log_audit(
                    session=session,
                    event_type="ACCOUNT_CREATED",
                    severity=SeverityLevel.INFO,
                    action="CREATE_ACCOUNT",
                    description=f"Account created: {account_def.account_code} - {account_def.account_name}",
                    user_id=created_by,
                    source_system="LEDGER_ENGINE",
                    entity_type="ACCOUNT",
                    entity_id=account_id,
                    metadata={
                        'account_code': account_def.account_code,
                        'account_type': account_def.account_type.value
                    }
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
                'parent_account_id': account.parent_account_id,
                'level': int(account.level),
                'is_active': account.is_active,
                'description': account.description,
                'created_at': account.created_at,
                'created_by': account.created_by
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
        Post a transaction to the ledger.
        
        This is the core operation that creates immutable journal entries.
        
        Args:
            transaction_input: Transaction details
            created_by: User posting the transaction
            source_system: Source system identifier
            source_ip: IP address of source
            
        Returns:
            transaction_id: UUID of posted transaction
        """
        transaction_input.validate()
        
        with self.SessionLocal() as session:
            try:
                # Generate transaction ID and number
                transaction_id = str(uuid.uuid4())
                transaction_number = self._generate_transaction_number(session)
                posting_date = datetime.now(timezone.utc)
                
                # Calculate transaction hash
                transaction_hash = self._calculate_transaction_hash(
                    transaction_id,
                    transaction_input.transaction_date,
                    transaction_input.entries
                )
                
                # Create transaction
                transaction = Transaction(
                    transaction_id=transaction_id,
                    transaction_number=transaction_number,
                    transaction_date=transaction_input.transaction_date,
                    posting_date=posting_date,
                    business_event_type=transaction_input.business_event_type,
                    business_key=transaction_input.business_key,
                    reference_number=transaction_input.reference_number,
                    description=transaction_input.description,
                    status=TransactionStatus.POSTED.value,
                    is_reversal=False,
                    created_at=posting_date,
                    created_by=created_by,
                    source_system=source_system,
                    source_ip=source_ip,
                    transaction_hash=transaction_hash
                )
                
                session.add(transaction)
                
                # Create journal entries
                for idx, entry_input in enumerate(transaction_input.entries, start=1):
                    # Verify account exists
                    account = session.query(ChartOfAccounts)\
                        .filter(ChartOfAccounts.account_code == entry_input.account_code)\
                        .first()
                    
                    if not account:
                        raise ValueError(f"Account {entry_input.account_code} not found")
                    
                    # Create entry
                    entry_id = str(uuid.uuid4())
                    entry_hash = self._calculate_entry_hash(
                        entry_id,
                        transaction_id,
                        entry_input.account_code,
                        entry_input.entry_type.value,
                        entry_input.amount
                    )
                    
                    journal_entry = JournalEntry(
                        entry_id=entry_id,
                        transaction_id=transaction_id,
                        entry_number=idx,
                        account_id=account.account_id,
                        account_code=entry_input.account_code,
                        entry_type=entry_input.entry_type.value,
                        amount=entry_input.amount,
                        currency='AOA',
                        cost_center=entry_input.cost_center,
                        department=entry_input.department,
                        project=entry_input.project,
                        memo=entry_input.memo,
                        posting_date=posting_date,
                        entry_hash=entry_hash
                    )
                    
                    session.add(journal_entry)
                
                # Log audit
                self._log_audit(
                    session=session,
                    event_type="TRANSACTION_POSTED",
                    severity=SeverityLevel.INFO,
                    transaction_id=transaction_id,
                    action="POST_TRANSACTION",
                    description=f"Transaction posted: {transaction_number} - {transaction_input.description}",
                    user_id=created_by,
                    source_system=source_system,
                    source_ip=source_ip,
                    metadata={
                        'transaction_number': transaction_number,
                        'business_event_type': transaction_input.business_event_type,
                        'entry_count': len(transaction_input.entries)
                    }
                )
                
                session.commit()
                return transaction_id
                
            except Exception as e:
                session.rollback()
                raise
    
    def reverse_transaction(
        self,
        transaction_id: str,
        reversal_reason: str,
        reversed_by: str,
        source_system: str,
        source_ip: Optional[str] = None
    ) -> str:
        """
        Reverse a posted transaction.
        
        This creates a new transaction with opposite entries.
        The original transaction is marked as REVERSED.
        
        Args:
            transaction_id: ID of transaction to reverse
            reversal_reason: Reason for reversal
            reversed_by: User performing reversal
            source_system: Source system
            source_ip: IP address
            
        Returns:
            reversal_transaction_id: ID of reversal transaction
        """
        with self.SessionLocal() as session:
            try:
                # Get original transaction
                original_txn = session.query(Transaction)\
                    .filter(Transaction.transaction_id == transaction_id)\
                    .first()
                
                if not original_txn:
                    raise ValueError(f"Transaction {transaction_id} not found")
                
                if original_txn.status != TransactionStatus.POSTED.value:
                    raise ValueError(
                        f"Cannot reverse transaction with status {original_txn.status}"
                    )
                
                if original_txn.reversed_by_transaction_id:
                    raise ValueError(
                        f"Transaction already reversed by {original_txn.reversed_by_transaction_id}"
                    )
                
                # Get original entries
                original_entries = session.query(JournalEntry)\
                    .filter(JournalEntry.transaction_id == transaction_id)\
                    .order_by(JournalEntry.entry_number)\
                    .all()
                
                # Create reversal entries by flipping debit/credit
                reversal_entries = []
                for orig_entry in original_entries:
                    reversal_type = (
                        EntryType.CREDIT if orig_entry.entry_type == 'DEBIT' 
                        else EntryType.DEBIT
                    )
                    
                    reversal_entries.append(
                        JournalEntryInput(
                            account_code=orig_entry.account_code,
                            entry_type=reversal_type,
                            amount=orig_entry.amount,
                            memo=f"Reversal of entry {orig_entry.entry_number}: {reversal_reason}"
                        )
                    )
                
                # Create reversal transaction input
                reversal_input = TransactionInput(
                    business_event_type=f"REVERSAL_{original_txn.business_event_type}",
                    description=f"Reversal of {original_txn.transaction_number}: {reversal_reason}",
                    transaction_date=datetime.now(timezone.utc),
                    entries=reversal_entries,
                    business_key=original_txn.business_key,
                    reference_number=original_txn.reference_number
                )
                
                # Post reversal
                reversal_id = self.post_transaction(
                    reversal_input,
                    created_by=reversed_by,
                    source_system=source_system,
                    source_ip=source_ip
                )
                
                # Update original and reversal
                reversal_txn = session.query(Transaction)\
                    .filter(Transaction.transaction_id == reversal_id)\
                    .first()
                
                original_txn.status = TransactionStatus.REVERSED.value
                original_txn.reversed_by_transaction_id = reversal_id
                
                reversal_txn.is_reversal = True
                reversal_txn.reverses_transaction_id = transaction_id
                reversal_txn.reversal_reason = reversal_reason
                
                # Log audit for reversal
                self._log_audit(
                    session=session,
                    event_type="TRANSACTION_REVERSED",
                    severity=SeverityLevel.WARNING,
                    transaction_id=original_txn.transaction_id,
                    action="REVERSE_TRANSACTION",
                    description=f"Transaction reversed: {original_txn.transaction_number} - Reason: {reversal_reason}",
                    user_id=reversed_by,
                    source_system=source_system,
                    source_ip=source_ip,
                    metadata={
                        'original_transaction': original_txn.transaction_number,
                        'reversal_transaction': reversal_txn.transaction_number
                    }
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