#!/usr/bin/env python3
"""
Ledger Administration CLI Tool
===============================
Command-line interface for ledger administration and operations.

Usage:
    python ledger_admin_cli.py [command] [options]
    
Commands:
    init              - Initialize database schema
    create-account    - Create account in chart of accounts
    post-transaction  - Post new transaction
    reverse           - Reverse a transaction
    balance           - Get account balance
    trial-balance     - Generate trial balance
    verify            - Verify double-entry integrity
    audit             - View audit logs
    report            - Generate reports
    
Version: 1.0.0
"""

import sys
import os
import click
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
import json

from ledger_engine import (
    LedgerEngine, AccountDefinition, AccountType,
    JournalEntryInput, TransactionInput, EntryType
)
from ledger_reporting import LedgerReportEngine

console = Console()


@click.group()
@click.version_option(version='1.0.0')
def cli():
    """Ledger Administration CLI Tool."""
    pass


@cli.command()
@click.option('--confirm', is_flag=True, help='Confirm database initialization')
def init(confirm):
    """Initialize database schema."""
    if not confirm:
        console.print("[yellow]⚠️  This will create/update database tables.[/yellow]")
        console.print("[yellow]   Use --confirm to proceed.[/yellow]")
        return
    
    try:
        console.print("[blue]🔧 Initializing database...[/blue]")
        ledger = LedgerEngine()
        console.print("[green]✅ Database initialized successfully![/green]")
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--code', required=True, help='Account code')
@click.option('--name', required=True, help='Account name')
@click.option('--type', 'account_type', required=True, 
              type=click.Choice(['ASSET', 'LIABILITY', 'EQUITY', 'REVENUE', 'EXPENSE']),
              help='Account type')
@click.option('--parent', help='Parent account code')
@click.option('--description', help='Account description')
@click.option('--user', required=True, help='Your user ID/email')
def create_account(code, name, account_type, parent, description, user):
    """Create account in chart of accounts."""
    try:
        ledger = LedgerEngine()
        
        account_def = AccountDefinition(
            account_code=code,
            account_name=name,
            account_type=AccountType[account_type],
            parent_account_code=parent,
            description=description
        )
        
        account_id = ledger.create_account(account_def, created_by=user)
        
        console.print(f"[green]✅ Account created successfully![/green]")
        console.print(f"   Account ID: {account_id}")
        console.print(f"   Code: {code}")
        console.print(f"   Name: {name}")
        console.print(f"   Type: {account_type}")
        
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--event-type', required=True, help='Business event type')
@click.option('--description', required=True, help='Transaction description')
@click.option('--business-key', help='Business key/reference')
@click.option('--user', required=True, help='Your user ID/email')
@click.option('--entries', required=True, help='JSON file with entries')
def post_transaction(event_type, description, business_key, user, entries):
    """
    Post new transaction.
    
    Entries file should be JSON array:
    [
        {
            "account_code": "1100",
            "entry_type": "DEBIT",
            "amount": "1000.00",
            "memo": "Optional memo"
        },
        {
            "account_code": "4100",
            "entry_type": "CREDIT",
            "amount": "1000.00"
        }
    ]
    """
    try:
        # Load entries from file
        with open(entries, 'r') as f:
            entries_data = json.load(f)
        
        # Parse entries
        journal_entries = []
        for entry_data in entries_data:
            journal_entry = JournalEntryInput(
                account_code=entry_data['account_code'],
                entry_type=EntryType[entry_data['entry_type']],
                amount=Decimal(str(entry_data['amount'])),
                cost_center=entry_data.get('cost_center'),
                business_unit=entry_data.get('business_unit'),
                project_code=entry_data.get('project_code'),
                memo=entry_data.get('memo')
            )
            journal_entries.append(journal_entry)
        
        # Create transaction input
        txn_input = TransactionInput(
            business_event_type=event_type,
            description=description,
            transaction_date=datetime.now(timezone.utc),
            entries=journal_entries,
            business_key=business_key
        )
        
        # Post transaction
        ledger = LedgerEngine()
        txn_id = ledger.post_transaction(
            txn_input,
            created_by=user,
            source_system="CLI_ADMIN"
        )
        
        console.print(f"[green]✅ Transaction posted successfully![/green]")
        console.print(f"   Transaction ID: {txn_id}")
        console.print(f"   Event Type: {event_type}")
        console.print(f"   Entries: {len(journal_entries)}")
        
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--transaction-id', required=True, help='Transaction ID to reverse')
@click.option('--reason', required=True, help='Reversal reason')
@click.option('--user', required=True, help='Your user ID/email')
def reverse(transaction_id, reason, user):
    """Reverse a transaction."""
    try:
        ledger = LedgerEngine()
        
        reversal_id = ledger.reverse_transaction(
            original_transaction_id=transaction_id,
            reversal_reason=reason,
            created_by=user,
            source_system="CLI_ADMIN"
        )
        
        console.print(f"[green]✅ Transaction reversed successfully![/green]")
        console.print(f"   Original Transaction: {transaction_id}")
        console.print(f"   Reversal Transaction: {reversal_id}")
        console.print(f"   Reason: {reason}")
        
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--account-code', required=True, help='Account code')
@click.option('--as-of-date', help='As of date (YYYY-MM-DD), default: today')
def balance(account_code, as_of_date):
    """Get account balance."""
    try:
        ledger = LedgerEngine()
        
        # Parse date if provided
        date_filter = None
        if as_of_date:
            date_filter = datetime.strptime(as_of_date, '%Y-%m-%d')
            date_filter = date_filter.replace(tzinfo=timezone.utc)
        
        # Get account info
        account = ledger.get_account(account_code)
        if not account:
            console.print(f"[red]❌ Account {account_code} not found[/red]")
            return
        
        # Get balance
        current_balance = ledger.get_account_balance(account_code, date_filter)
        
        # Create table
        table = Table(title=f"Account Balance - {account_code}", box=box.ROUNDED)
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Account Code", account['account_code'])
        table.add_row("Account Name", account['account_name'])
        table.add_row("Account Type", account['account_type'])
        table.add_row("Balance", f"{current_balance:,.2f}")
        
        if as_of_date:
            table.add_row("As of Date", as_of_date)
        else:
            table.add_row("As of Date", "Current")
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--as-of-date', help='As of date (YYYY-MM-DD), default: today')
@click.option('--output', help='Output file (JSON or CSV)')
def trial_balance(as_of_date, output):
    """Generate trial balance."""
    try:
        ledger = LedgerEngine()
        report_engine = LedgerReportEngine(ledger)
        
        # Parse date
        date_filter = datetime.now(timezone.utc)
        if as_of_date:
            date_filter = datetime.strptime(as_of_date, '%Y-%m-%d')
            date_filter = date_filter.replace(tzinfo=timezone.utc)
        
        # Generate report
        report = report_engine.generate_trial_balance(
            as_of_date=date_filter,
            generated_by="CLI_ADMIN",
            include_zero_balances=False
        )
        
        # Display summary
        console.print(Panel(f"[bold]Trial Balance Report[/bold]", box=box.DOUBLE))
        console.print(f"As of: {date_filter.date()}")
        console.print(f"Accounts: {report['account_count']}")
        console.print(f"Report ID: {report['report_id']}")
        console.print(f"Report Hash: {report['report_hash'][:16]}...")
        
        # Create table
        table = Table(title="Account Balances", box=box.ROUNDED)
        table.add_column("Code", style="cyan")
        table.add_column("Name", style="white")
        table.add_column("Type", style="yellow")
        table.add_column("Balance", style="green", justify="right")
        
        for account in report['accounts'][:20]:  # Show first 20
            balance_str = f"{account['balance']:,.2f}"
            table.add_row(
                account['account_code'],
                account['account_name'][:40],
                account['account_type'],
                balance_str
            )
        
        if report['account_count'] > 20:
            table.add_row("...", "...", "...", "...")
        
        console.print(table)
        
        # Save to file if requested
        if output:
            if output.endswith('.json'):
                report_engine.export_to_json(report, output)
            elif output.endswith('.csv'):
                report_engine.export_to_csv(report, output)
            else:
                console.print("[yellow]⚠️  Unknown file format, saving as JSON[/yellow]")
                output = output + '.json'
                report_engine.export_to_json(report, output)
            
            console.print(f"[green]✅ Report saved to: {output}[/green]")
        
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--transaction-id', help='Specific transaction to verify')
def verify(transaction_id):
    """Verify double-entry integrity."""
    try:
        ledger = LedgerEngine()
        
        console.print("[blue]🔍 Verifying double-entry integrity...[/blue]")
        
        is_valid, errors = ledger.verify_double_entry_integrity(transaction_id)
        
        if is_valid:
            console.print("[green]✅ All transactions balanced correctly![/green]")
        else:
            console.print(f"[red]❌ Found {len(errors)} integrity issues:[/red]")
            for error in errors:
                console.print(f"   • {error}")
        
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--days', default=7, help='Number of days to show')
@click.option('--event-type', help='Filter by event type')
@click.option('--user-filter', help='Filter by user')
def audit(days, event_type, user_filter):
    """View audit logs."""
    try:
        report_engine = LedgerReportEngine()
        
        # Calculate date range
        end_date = datetime.now(timezone.utc)
        from datetime import timedelta
        start_date = end_date - timedelta(days=days)
        
        # Generate audit trail
        report = report_engine.generate_audit_trail(
            start_date=start_date,
            end_date=end_date,
            generated_by="CLI_ADMIN",
            event_type=event_type,
            user_filter=user_filter
        )
        
        # Display summary
        console.print(Panel(f"[bold]Audit Trail - Last {days} Days[/bold]", box=box.DOUBLE))
        console.print(f"Total Events: {report['entry_count']}")
        console.print(f"Report ID: {report['report_id']}")
        
        # Create table
        table = Table(title="Recent Audit Events", box=box.ROUNDED)
        table.add_column("Timestamp", style="cyan")
        table.add_column("Event Type", style="yellow")
        table.add_column("User", style="green")
        table.add_column("Action", style="white")
        table.add_column("Severity", style="red")
        
        for entry in report['entries'][:20]:  # Show first 20
            timestamp = datetime.fromisoformat(entry['event_timestamp'])
            table.add_row(
                timestamp.strftime('%Y-%m-%d %H:%M'),
                entry['event_type'],
                entry['user_id'][:30],
                entry['action'],
                entry['severity']
            )
        
        if report['entry_count'] > 20:
            table.add_row("...", "...", "...", "...", "...")
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--type', 'report_type', required=True,
              type=click.Choice(['balance-sheet', 'income-statement', 'general-ledger']),
              help='Report type')
@click.option('--start-date', help='Start date (YYYY-MM-DD)')
@click.option('--end-date', help='End date (YYYY-MM-DD)')
@click.option('--output', required=True, help='Output file (.json or .csv)')
@click.option('--user', required=True, help='Your user ID/email')
def report(report_type, start_date, end_date, output, user):
    """Generate financial reports."""
    try:
        report_engine = LedgerReportEngine()
        
        # Parse dates
        if report_type in ['income-statement', 'general-ledger']:
            if not start_date or not end_date:
                console.print("[red]❌ Start and end dates required for this report type[/red]")
                return
            
            start = datetime.strptime(start_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
            end = datetime.strptime(end_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
        else:
            end = datetime.now(timezone.utc)
            if end_date:
                end = datetime.strptime(end_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
        
        # Generate report
        console.print(f"[blue]📊 Generating {report_type} report...[/blue]")
        
        if report_type == 'balance-sheet':
            generated_report = report_engine.generate_balance_sheet(
                as_of_date=end,
                generated_by=user
            )
        elif report_type == 'income-statement':
            generated_report = report_engine.generate_income_statement(
                start_date=start,
                end_date=end,
                generated_by=user
            )
        elif report_type == 'general-ledger':
            generated_report = report_engine.generate_general_ledger(
                start_date=start,
                end_date=end,
                generated_by=user
            )
        
        # Save report
        if output.endswith('.json'):
            report_engine.export_to_json(generated_report, output)
        elif output.endswith('.csv'):
            report_engine.export_to_csv(generated_report, output)
        else:
            console.print("[red]❌ Output file must be .json or .csv[/red]")
            return
        
        console.print(f"[green]✅ Report generated successfully![/green]")
        console.print(f"   Report ID: {generated_report['report_id']}")
        console.print(f"   Report Hash: {generated_report['report_hash'][:16]}...")
        console.print(f"   Saved to: {output}")
        
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        sys.exit(1)


def main():
    """Main entry point."""
    cli()


if __name__ == '__main__':
    main()
