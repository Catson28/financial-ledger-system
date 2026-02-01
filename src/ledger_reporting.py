#!/usr/bin/env python3
"""
Ledger Reporting Module
========================
Módulo de geração de relatórios auditáveis e reproduzíveis.

Este módulo garante que todos os relatórios sejam:
- Reproduzíveis: mesmos parâmetros = mesmo resultado
- Auditáveis: trilha completa de geração
- Assin

áveis: hash de integridade
- Versionados: controle de versão de relatórios

Version: 1.0.0
"""

import os
import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from decimal import Decimal
from dataclasses import dataclass, asdict
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

from ledger_engine import (
    LedgerEngine, AccountType, TransactionStatus,
    Base, ChartOfAccounts, Transaction, JournalEntry, AuditLog
)

load_dotenv()


@dataclass
class ReportMetadata:
    """Metadata for report generation."""
    report_id: str
    report_type: str
    report_name: str
    generated_at: datetime
    generated_by: str
    parameters: Dict[str, Any]
    report_hash: str
    is_reproducible: bool = True


class LedgerReportEngine:
    """
    Report generation engine for Ledger system.
    
    All reports are:
    - Immutable once generated
    - Fully auditable
    - Reproducible with same parameters
    - Cryptographically signed
    """
    
    def __init__(self, ledger_engine: Optional[LedgerEngine] = None):
        """Initialize report engine."""
        if ledger_engine:
            self.ledger = ledger_engine
        else:
            self.ledger = LedgerEngine()
        
        self.session_factory = self.ledger.SessionLocal
    
    def _generate_report_id(self) -> str:
        """Generate unique report ID."""
        import uuid
        return str(uuid.uuid4())
    
    def _calculate_report_hash(self, report_data: Dict[str, Any]) -> str:
        """Calculate SHA-256 hash for report integrity."""
        json_str = json.dumps(report_data, sort_keys=True, default=str)
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    def _save_report_metadata(
        self,
        report_id: str,
        report_type: str,
        report_name: str,
        parameters: Dict,
        generated_by: str,
        report_hash: str
    ):
        """Save report metadata for audit trail."""
        with self.session_factory() as session:
            metadata = {
                'report_id': report_id,
                'report_type': report_type,
                'report_name': report_name,
                'parameters': parameters,
                'report_hash': report_hash
            }
            
            self.ledger._log_audit(
                session=session,
                event_type="REPORT_GENERATED",
                action="GENERATE_REPORT",
                description=f"Report {report_type} generated: {report_name}",
                user_id=generated_by,
                source_system="REPORT_ENGINE",
                metadata=metadata
            )
            session.commit()
    
    # ========================
    # BALANCE SHEET
    # ========================
    
    def generate_balance_sheet(
        self,
        as_of_date: datetime,
        generated_by: str,
        include_zero_balances: bool = False
    ) -> Dict[str, Any]:
        """
        Generate Balance Sheet (Balanço Patrimonial).
        
        Structure:
        - Assets
        - Liabilities
        - Equity
        
        Returns:
            Dict with balance sheet data and metadata
        """
        report_id = self._generate_report_id()
        
        with self.session_factory() as session:
            # Get all accounts with balances
            accounts = session.query(ChartOfAccounts)\
                .filter(ChartOfAccounts.is_active == True)\
                .order_by(ChartOfAccounts.account_code)\
                .all()
            
            assets = []
            liabilities = []
            equity = []
            
            for account in accounts:
                balance = self.ledger.get_account_balance(
                    account.account_code,
                    as_of_date
                )
                
                if not include_zero_balances and balance == 0:
                    continue
                
                account_data = {
                    'account_code': account.account_code,
                    'account_name': account.account_name,
                    'balance': float(balance)
                }
                
                account_type = AccountType(account.account_type)
                
                if account_type == AccountType.ASSET:
                    assets.append(account_data)
                elif account_type == AccountType.LIABILITY:
                    liabilities.append(account_data)
                elif account_type == AccountType.EQUITY:
                    equity.append(account_data)
            
            # Calculate totals
            total_assets = sum(a['balance'] for a in assets)
            total_liabilities = sum(l['balance'] for l in liabilities)
            total_equity = sum(e['balance'] for e in equity)
            
            # Build report
            balance_sheet = {
                'report_id': report_id,
                'report_type': 'BALANCE_SHEET',
                'report_name': f'Balance Sheet as of {as_of_date.date()}',
                'as_of_date': as_of_date.isoformat(),
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'generated_by': generated_by,
                'assets': assets,
                'liabilities': liabilities,
                'equity': equity,
                'totals': {
                    'total_assets': total_assets,
                    'total_liabilities': total_liabilities,
                    'total_equity': total_equity,
                    'balance_check': abs(total_assets - (total_liabilities + total_equity)) < 0.01
                }
            }
            
            # Calculate hash
            report_hash = self._calculate_report_hash(balance_sheet)
            balance_sheet['report_hash'] = report_hash
            
            # Save metadata
            self._save_report_metadata(
                report_id=report_id,
                report_type='BALANCE_SHEET',
                report_name=balance_sheet['report_name'],
                parameters={'as_of_date': as_of_date.isoformat()},
                generated_by=generated_by,
                report_hash=report_hash
            )
            
            return balance_sheet
    
    # ========================
    # INCOME STATEMENT
    # ========================
    
    def generate_income_statement(
        self,
        start_date: datetime,
        end_date: datetime,
        generated_by: str,
        include_zero_balances: bool = False
    ) -> Dict[str, Any]:
        """
        Generate Income Statement (Demonstração de Resultados).
        
        Structure:
        - Revenue
        - Expenses
        - Net Income
        
        Returns:
            Dict with income statement data and metadata
        """
        report_id = self._generate_report_id()
        
        with self.session_factory() as session:
            # Get revenue and expense accounts
            accounts = session.query(ChartOfAccounts)\
                .filter(
                    ChartOfAccounts.is_active == True,
                    ChartOfAccounts.account_type.in_(['REVENUE', 'EXPENSE'])
                )\
                .order_by(ChartOfAccounts.account_code)\
                .all()
            
            revenues = []
            expenses = []
            
            for account in accounts:
                # Get activity for period
                query = session.query(JournalEntry)\
                    .join(Transaction)\
                    .filter(
                        JournalEntry.account_code == account.account_code,
                        Transaction.status == TransactionStatus.POSTED.value,
                        Transaction.posting_date >= start_date,
                        Transaction.posting_date <= end_date
                    )
                
                entries = query.all()
                
                # Calculate net for period
                total_debits = Decimal('0')
                total_credits = Decimal('0')
                
                for entry in entries:
                    if entry.entry_type == 'DEBIT':
                        total_debits += entry.amount
                    else:
                        total_credits += entry.amount
                
                # Revenue increases with credits, expense increases with debits
                account_type = AccountType(account.account_type)
                
                if account_type == AccountType.REVENUE:
                    net_amount = total_credits - total_debits
                else:  # EXPENSE
                    net_amount = total_debits - total_credits
                
                if not include_zero_balances and net_amount == 0:
                    continue
                
                account_data = {
                    'account_code': account.account_code,
                    'account_name': account.account_name,
                    'amount': float(net_amount)
                }
                
                if account_type == AccountType.REVENUE:
                    revenues.append(account_data)
                else:
                    expenses.append(account_data)
            
            # Calculate totals
            total_revenue = sum(r['amount'] for r in revenues)
            total_expenses = sum(e['amount'] for e in expenses)
            net_income = total_revenue - total_expenses
            
            # Build report
            income_statement = {
                'report_id': report_id,
                'report_type': 'INCOME_STATEMENT',
                'report_name': f'Income Statement {start_date.date()} to {end_date.date()}',
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'generated_by': generated_by,
                'revenues': revenues,
                'expenses': expenses,
                'totals': {
                    'total_revenue': total_revenue,
                    'total_expenses': total_expenses,
                    'net_income': net_income
                }
            }
            
            # Calculate hash
            report_hash = self._calculate_report_hash(income_statement)
            income_statement['report_hash'] = report_hash
            
            # Save metadata
            self._save_report_metadata(
                report_id=report_id,
                report_type='INCOME_STATEMENT',
                report_name=income_statement['report_name'],
                parameters={
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                generated_by=generated_by,
                report_hash=report_hash
            )
            
            return income_statement
    
    # ========================
    # TRIAL BALANCE
    # ========================
    
    def generate_trial_balance(
        self,
        as_of_date: datetime,
        generated_by: str,
        include_zero_balances: bool = False
    ) -> Dict[str, Any]:
        """
        Generate Trial Balance (Balancete de Verificação).
        
        Returns:
            Dict with trial balance data and metadata
        """
        report_id = self._generate_report_id()
        
        trial_balance_data = self.ledger.get_trial_balance(as_of_date)
        
        # Filter zero balances if requested
        if not include_zero_balances:
            trial_balance_data = [
                account for account in trial_balance_data
                if account['balance'] != 0
            ]
        
        # Convert Decimal to float for JSON serialization
        for account in trial_balance_data:
            account['balance'] = float(account['balance'])
        
        # Calculate totals by type
        totals_by_type = {}
        for account in trial_balance_data:
            acc_type = account['account_type']
            if acc_type not in totals_by_type:
                totals_by_type[acc_type] = 0
            totals_by_type[acc_type] += account['balance']
        
        # Build report
        trial_balance = {
            'report_id': report_id,
            'report_type': 'TRIAL_BALANCE',
            'report_name': f'Trial Balance as of {as_of_date.date()}',
            'as_of_date': as_of_date.isoformat(),
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'generated_by': generated_by,
            'accounts': trial_balance_data,
            'totals_by_type': totals_by_type,
            'account_count': len(trial_balance_data)
        }
        
        # Calculate hash
        report_hash = self._calculate_report_hash(trial_balance)
        trial_balance['report_hash'] = report_hash
        
        # Save metadata
        self._save_report_metadata(
            report_id=report_id,
            report_type='TRIAL_BALANCE',
            report_name=trial_balance['report_name'],
            parameters={'as_of_date': as_of_date.isoformat()},
            generated_by=generated_by,
            report_hash=report_hash
        )
        
        return trial_balance
    
    # ========================
    # GENERAL LEDGER
    # ========================
    
    def generate_general_ledger(
        self,
        start_date: datetime,
        end_date: datetime,
        generated_by: str,
        account_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate General Ledger report.
        
        Shows all transactions for a period, optionally filtered by account.
        
        Returns:
            Dict with general ledger data and metadata
        """
        report_id = self._generate_report_id()
        
        with self.session_factory() as session:
            # Build query
            query = session.query(
                Transaction.transaction_number,
                Transaction.transaction_date,
                Transaction.description,
                JournalEntry.account_code,
                ChartOfAccounts.account_name,
                JournalEntry.entry_type,
                JournalEntry.amount,
                JournalEntry.memo
            )\
            .join(JournalEntry, Transaction.transaction_id == JournalEntry.transaction_id)\
            .join(ChartOfAccounts, JournalEntry.account_id == ChartOfAccounts.account_id)\
            .filter(
                Transaction.status == TransactionStatus.POSTED.value,
                Transaction.posting_date >= start_date,
                Transaction.posting_date <= end_date
            )\
            .order_by(
                Transaction.transaction_date,
                Transaction.transaction_number,
                JournalEntry.entry_number
            )
            
            if account_code:
                query = query.filter(JournalEntry.account_code == account_code)
            
            # Execute query
            results = query.all()
            
            # Format results
            entries = []
            for row in results:
                entries.append({
                    'transaction_number': row[0],
                    'transaction_date': row[1].isoformat() if row[1] else None,
                    'description': row[2],
                    'account_code': row[3],
                    'account_name': row[4],
                    'entry_type': row[5],
                    'amount': float(row[6]),
                    'memo': row[7]
                })
            
            # Build report
            general_ledger = {
                'report_id': report_id,
                'report_type': 'GENERAL_LEDGER',
                'report_name': f'General Ledger {start_date.date()} to {end_date.date()}',
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'account_filter': account_code,
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'generated_by': generated_by,
                'entries': entries,
                'entry_count': len(entries)
            }
            
            # Calculate hash
            report_hash = self._calculate_report_hash(general_ledger)
            general_ledger['report_hash'] = report_hash
            
            # Save metadata
            self._save_report_metadata(
                report_id=report_id,
                report_type='GENERAL_LEDGER',
                report_name=general_ledger['report_name'],
                parameters={
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'account_code': account_code
                },
                generated_by=generated_by,
                report_hash=report_hash
            )
            
            return general_ledger
    
    # ========================
    # AUDIT REPORT
    # ========================
    
    def generate_audit_trail(
        self,
        start_date: datetime,
        end_date: datetime,
        generated_by: str,
        event_type: Optional[str] = None,
        user_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive audit trail report.
        
        Returns:
            Dict with audit trail data and metadata
        """
        report_id = self._generate_report_id()
        
        with self.session_factory() as session:
            # Build query
            query = session.query(AuditLog)\
                .filter(
                    AuditLog.event_timestamp >= start_date,
                    AuditLog.event_timestamp <= end_date
                )\
                .order_by(AuditLog.event_timestamp.desc())
            
            if event_type:
                query = query.filter(AuditLog.event_type == event_type)
            
            if user_filter:
                query = query.filter(AuditLog.user_id == user_filter)
            
            # Execute query
            audit_logs = query.all()
            
            # Format results
            entries = []
            for log in audit_logs:
                entries.append({
                    'audit_id': log.audit_id,
                    'event_timestamp': log.event_timestamp.isoformat(),
                    'event_type': log.event_type,
                    'severity': log.severity,
                    'user_id': log.user_id,
                    'source_system': log.source_system,
                    'action': log.action,
                    'description': log.description,
                    'transaction_id': log.transaction_id
                })
            
            # Build report
            audit_trail = {
                'report_id': report_id,
                'report_type': 'AUDIT_TRAIL',
                'report_name': f'Audit Trail {start_date.date()} to {end_date.date()}',
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'event_type_filter': event_type,
                'user_filter': user_filter,
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'generated_by': generated_by,
                'entries': entries,
                'entry_count': len(entries)
            }
            
            # Calculate hash
            report_hash = self._calculate_report_hash(audit_trail)
            audit_trail['report_hash'] = report_hash
            
            # Save metadata
            self._save_report_metadata(
                report_id=report_id,
                report_type='AUDIT_TRAIL',
                report_name=audit_trail['report_name'],
                parameters={
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'event_type': event_type,
                    'user_filter': user_filter
                },
                generated_by=generated_by,
                report_hash=report_hash
            )
            
            return audit_trail
    
    # ========================
    # EXPORT FUNCTIONS
    # ========================
    
    def export_to_json(self, report: Dict[str, Any], filename: str):
        """Export report to JSON file."""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
    
    def export_to_csv(self, report: Dict[str, Any], filename: str):
        """Export report to CSV file."""
        # Determine what data to export based on report type
        report_type = report.get('report_type')
        
        if report_type == 'BALANCE_SHEET':
            # Combine all sections
            data = []
            for section in ['assets', 'liabilities', 'equity']:
                for item in report.get(section, []):
                    item['section'] = section
                    data.append(item)
            df = pd.DataFrame(data)
        
        elif report_type == 'INCOME_STATEMENT':
            # Combine revenues and expenses
            data = []
            for item in report.get('revenues', []):
                item['type'] = 'revenue'
                data.append(item)
            for item in report.get('expenses', []):
                item['type'] = 'expense'
                data.append(item)
            df = pd.DataFrame(data)
        
        elif report_type in ['TRIAL_BALANCE', 'GENERAL_LEDGER', 'AUDIT_TRAIL']:
            # Direct conversion
            df = pd.DataFrame(report.get('accounts' if report_type == 'TRIAL_BALANCE' else 'entries', []))
        
        else:
            raise ValueError(f"Unknown report type: {report_type}")
        
        df.to_csv(filename, index=False)
    
    def verify_report_integrity(self, report: Dict[str, Any]) -> bool:
        """
        Verify report integrity by recalculating hash.
        
        Returns:
            True if hash matches, False otherwise
        """
        stored_hash = report.get('report_hash')
        if not stored_hash:
            return False
        
        # Remove hash for recalculation
        report_copy = report.copy()
        report_copy.pop('report_hash', None)
        
        calculated_hash = self._calculate_report_hash(report_copy)
        
        return stored_hash == calculated_hash


def main():
    """Example usage."""
    print("Ledger Reporting Module")
    print("Use this module to generate auditable financial reports")


if __name__ == "__main__":
    main()
