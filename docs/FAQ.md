# Frequently Asked Questions

Quick reference for common questions. For detailed operational procedures, see RUNBOOK.md. For design rationale, see ARCHITECTURE.md and DECISIONS.md.

---

## Setup and Installation

### How do I install the system?

Run `python setup.py` and follow the prompts. The script creates virtual environment, installs dependencies, creates .env file, and optionally initializes the database with sample accounts.

See README.md "Getting Started" section for detailed steps.

### What database do I need?

Production: MySQL 8.0+ or MariaDB 10.5+  
Development/Testing: SQLite 3.x (limited — does not enforce triggers)

MySQL is strongly recommended for all non-development use. SQLite does not enforce immutability triggers the same way, creating false security confidence.

### Can I use PostgreSQL?

Yes, but requires work. The Python code (SQLAlchemy ORM) is database-agnostic. The SQL schema and triggers are MySQL-specific and must be rewritten for PostgreSQL PL/pgSQL syntax.

See ARCHITECTURE.md "Known Limits and Risks" → "MySQL Trigger Dependency" for migration details.

### What Python version is required?

Python 3.10 or higher. The system uses type hints and features introduced in Python 3.10.

Check your version: `python --version`

### How do I configure the database connection?

Edit `.env` file and set `LEDGER_DB_URI`. Format:

```
LEDGER_DB_URI=mysql+pymysql://username:password@hostname:3306/database_name?charset=utf8mb4
```

Test connection: `mysql -u username -p -h hostname -e "SELECT 1"`

### Do I need to create the database manually?

Yes. Create the database first:

```sql
CREATE DATABASE ledger_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Then run `python ledger_admin_cli.py init --confirm` to create tables.

### Where are the database credentials stored?

In `.env` file (not committed to version control). The `.env.template` file provides example format. Copy and modify:

```bash
cp .env.template .env
# Edit .env with your credentials
```

### Can I run this on Windows?

Yes, but WSL (Windows Subsystem for Linux) is recommended for better compatibility with shell scripts and MySQL command-line tools. Native Windows support exists but is less tested.

---

## Execution and Operations

### How do I post my first transaction?

1. Create chart of accounts (or use sample accounts from setup)
2. Create JSON file with journal entries (see README.md example)
3. Run: `python ledger_admin_cli.py post-transaction --event-type <type> --description "<desc>" --user <your_email> --entries entries.json`

See README.md "First Transaction" section for complete example.

### What happens if I post an unbalanced transaction?

The transaction is rejected before reaching the database. You'll receive error message:

```
ValueError: Transaction not balanced: Debits=1000.00, Credits=500.00
```

Fix the entries.json file so debits equal credits, then retry.

### Can I update a transaction after it's posted?

No. Immutability is core principle. Once posted (status = POSTED), transactions cannot be modified or deleted.

To correct errors, use reversal: `python ledger_admin_cli.py reverse --transaction-id <id> --reason "<reason>" --user <your_email>`

See RUNBOOK.md "Reversal Operation Failure" for details.

### How do I reverse a transaction?

```bash
python ledger_admin_cli.py reverse \
  --transaction-id <transaction_id> \
  --reason "Explanation for reversal" \
  --user your.email@company.com
```

System creates new transaction with inverted entries (DEBIT ↔ CREDIT) and marks original as REVERSED.

### Can I delete a transaction?

No. Database triggers prevent deletion of posted transactions. This is intentional to maintain audit trail integrity.

If transaction was posted in error, reverse it. If transaction is test data, mark it clearly in the description field when posting.

### What's the difference between transaction_date and posting_date?

- **transaction_date**: When the economic event occurred (IFRS requirement)
- **posting_date**: When the entry was recorded in the ledger (system timestamp)

Example: Sale happens December 31, 2025 (transaction_date). Accountant posts entry January 5, 2026 (posting_date).

Financial reports use transaction_date for period classification. Audit trail uses posting_date for timeline reconstruction.

### How do I check if my data is valid?

Run integrity verification:

```bash
python ledger_admin_cli.py verify
```

Expected output: "✅ All transactions balanced correctly!"

If violations found, see RUNBOOK.md "Double-Entry Violation Detected".

### Can I import transactions from Excel or CSV?

Not directly in current version. You must convert Excel/CSV to JSON format matching the entries structure:

```json
[
  {"account_code": "1100", "entry_type": "DEBIT", "amount": "1000.00"},
  {"account_code": "4100", "entry_type": "CREDIT", "amount": "1000.00"}
]
```

Write a script to transform your data format into this structure, then use `post-transaction` command.

### How do I generate reports?

Common reports:

```bash
# Trial balance
python ledger_admin_cli.py trial-balance --output report.json

# Balance sheet
python ledger_admin_cli.py report --type balance-sheet --output bs.json --user <email>

# Income statement (requires date range)
python ledger_admin_cli.py report --type income-statement \
  --start-date 2026-01-01 --end-date 2026-01-31 \
  --output is.json --user <email>
```

Reports are saved to specified output file. View with any JSON reader or import into Excel.

---

## Common Failures

### "Account <code> not found" error

The account code referenced in your journal entries does not exist in chart of accounts.

**Fix**: Create the account first:

```bash
python ledger_admin_cli.py create-account \
  --code <code> \
  --name "Account Name" \
  --type ASSET \
  --user <your_email>
```

Account types: ASSET, LIABILITY, EQUITY, REVENUE, EXPENSE

### "Cannot modify posted transaction" error

You attempted to UPDATE or DELETE a transaction in the database directly. This violates immutability and is blocked by triggers.

**Fix**: Do not modify transactions directly. Use reversal to correct errors.

If you need to modify test data, delete the database and reinitialize from scratch.

### "Transaction number already exists" error

Race condition occurred — two processes tried to post transactions simultaneously and generated the same transaction number.

**Fix**: Wait 1 second and retry. System will generate next sequential number.

**Prevention**: Do not run multiple instances of the application simultaneously (see ARCHITECTURE.md "Single Instance vs. Horizontal Scaling").

### "Database connection lost" error

Application cannot reach MySQL server.

**Check**:
1. Database is running: `systemctl status mysql`
2. Network connectivity: `ping <database_host>`
3. Credentials are correct in `.env`

See RUNBOOK.md "Database Connection Loss" for detailed troubleshooting.

### "Trial balance is very slow" error

With 500+ active accounts, trial balance uses one query per account (N+1 problem).

**Workaround**: Query SQL view directly:

```bash
mysql -u user -p -h host ledger_db -e "SELECT * FROM v_trial_balance"
```

**Permanent fix**: Modify report engine to use view. See RUNBOOK.md "Trial Balance Performance Degradation".

### Why are failed operations not in the audit log?

Current implementation only logs successful operations. Failed attempts roll back and do not create audit entries.

This is a known gap documented in DECISIONS.md "DEC-008 — Audit Log Excludes Failed Operations". Production deployment should implement failure logging for security-sensitive operations.

**Workaround**: Monitor application logs (not database audit log) for error patterns.

### Can I recover a deleted database?

Only from backup. System does not provide undelete functionality.

**Recovery**:
1. Restore latest backup to new database
2. Verify data integrity
3. Repost transactions created after backup
4. Run `verify` to ensure correctness

See RUNBOOK.md "Backup Failure" for backup procedures.

---

## Monitoring and Maintenance

### How do I monitor system health?

Current version has minimal built-in monitoring. Recommended checks:

**Daily**:
- Verify backup completed successfully
- Check disk space: `df -h /var/lib/mysql`
- Run integrity check: `python ledger_admin_cli.py verify`

**Weekly**:
- Review audit log for anomalies
- Check transaction volume trends
- Test report generation performance

**Monthly**:
- Archive old audit log entries (>2 years)
- Review database size growth
- Update dependencies: `pip list --outdated`

### What should I back up?

**Essential**:
- MySQL database (`mysqldump` with --single-transaction)
- `.env` configuration file (credentials)
- Custom SQL scripts

**Optional but recommended**:
- Application code (already in version control)
- Generated reports (can be regenerated)
- Audit log archives

Backup schedule: Daily minimum. See `.env` → `BACKUP_SCHEDULE=0 2 * * *` (daily at 2 AM).

### How do I check database size?

```sql
SELECT 
    table_schema AS 'Database',
    SUM(data_length + index_length) / 1024 / 1024 / 1024 AS 'Size_GB'
FROM information_schema.tables
WHERE table_schema = 'ledger_db'
GROUP BY table_schema;
```

Or from shell:

```bash
du -sh /var/lib/mysql/ledger_db
```

### When should I archive old data?

Default retention: 7 years (configurable in `.env` → `AUDIT_RETENTION_DAYS`).

Consider archiving when:
- Database exceeds 100GB
- Backup time exceeds maintenance window
- Query performance degrades due to table size

See RUNBOOK.md "Database Size Management" for archiving procedures.

### Can I run multiple instances for high availability?

No, not without code changes. Transaction numbering uses count-then-increment which has race condition with multiple instances.

**Consequence**: Running two instances simultaneously will cause transaction number collisions.

**Solution**: Keep single instance for writes, use read replicas for reports.

See ARCHITECTURE.md "Known Limits and Risks" → "Single Instance Limitation" and DECISIONS.md "DEC-004 — Sequential Transaction Numbering".

### How do I update the application code?

1. **Stop application**: `systemctl stop ledger_app` (if running as service)
2. **Backup database**: `mysqldump` to safe location
3. **Test migration on backup** first
4. **Apply schema migrations** if needed (via Alembic or manual SQL)
5. **Update Python code**: `git pull` or manual file replacement
6. **Update dependencies**: `pip install -r requirements.txt --upgrade`
7. **Test**: Run `verify` and post test transaction
8. **Start application**: `systemctl start ledger_app`

**Rollback plan**: Restore backup and revert code if issues occur.

### What logs should I monitor?

**Application logs**: Python exception traces, validation errors  
**Database logs**: Connection errors, slow queries (enable slow query log)  
**Audit log**: All posted transactions, reversals, account creations  
**System logs**: Backup completion, cron job execution

Configure `.env` → `ENABLE_DETAILED_AUDIT=True` for verbose logging.

---

## Chart of Accounts

### How do I create a new account?

```bash
python ledger_admin_cli.py create-account \
  --code <code> \
  --name "Account Name" \
  --type ASSET \
  --description "Optional description" \
  --user your.email@company.com
```

Account code must be unique. Common convention: hierarchical numbering (1000 → 1100 → 1110).

### Can I create child accounts?

Yes, use `--parent` flag:

```bash
python ledger_admin_cli.py create-account \
  --code 1110 \
  --name "Petty Cash" \
  --type ASSET \
  --parent 1100 \
  --user <email>
```

System tracks hierarchy via `parent_account_id` and `level` fields.

### Can I rename an account?

No direct method exists. Renaming affects historical report interpretation.

**Recommended approach**:
1. Create new account with desired name
2. Post adjustment transaction to transfer balance from old to new
3. Deactivate old account (prevents new transactions)
4. Document reason in account description

**Never** UPDATE account_name directly — this breaks hash verification for transactions referencing that account.

### Can I delete an account?

No. Immutability principle applies to chart of accounts.

**Instead**: Deactivate the account by setting `is_active = FALSE`. This:
- Removes account from trial balance and reports
- Prevents new transactions from using account
- Preserves historical transactions and references

Currently no CLI command for deactivation — must UPDATE database directly (this is the ONE permitted update on chart_of_accounts).

### What account types are supported?

Five types per double-entry accounting:

- **ASSET**: Resources owned (cash, receivables, inventory, equipment)
- **LIABILITY**: Obligations owed (payables, loans, accrued expenses)
- **EQUITY**: Owner's interest (capital, retained earnings)
- **REVENUE**: Income earned (sales, services, interest income)
- **EXPENSE**: Costs incurred (salaries, rent, supplies, depreciation)

Debit/credit behavior varies by type — see ARCHITECTURE.md "Calculate Account Balance" for logic.

### How do I organize accounts hierarchically?

Use numeric codes with hierarchy convention:

```
1000    Assets (parent)
  1100  Current Assets (child of 1000)
    1110  Cash (child of 1100)
    1120  Petty Cash (child of 1100)
  1200  Accounts Receivable (child of 1000)
2000    Liabilities (parent)
  2100  Current Liabilities (child of 2000)
```

Set parent when creating account via `--parent` flag. System automatically tracks `level` (1 for top-level, 2 for children, etc.).

---

## Multi-Currency and International

### Does the system support multiple currencies?

No, not in current version. All transactions use AOA (Angolan Kwanza).

The `currency` field exists in journal_entries table but is hardcoded to 'AOA'. Multi-currency support requires:
- Exchange rate table
- Conversion logic
- Functional vs. presentation currency handling

See DECISIONS.md "DEC-010 — Single Currency Implementation" for extension path.

### Can I use this in a different country?

Yes, with configuration changes:

1. Update `.env` → `DEFAULT_CURRENCY` to your currency code (ISO 4217)
2. Update `.env` → `LEDGER_TIMEZONE` to your timezone
3. Update `.env` → `JURISDICTION` to your country code
4. Update `.env` → `ACCOUNTING_STANDARD` if not using IFRS

Code is not Angola-specific. Comments and documentation reference Angola as example deployment, but architecture is jurisdiction-agnostic.

### What accounting standards are supported?

System is designed for IFRS (International Financial Reporting Standards). The core principles (double-entry, immutability, separation of transaction date and posting date) align with IFRS requirements.

GAAP (US Generally Accepted Accounting Principles) is similar enough that system can be used with minor adaptation. Specific differences (revenue recognition timing, inventory valuation) are business logic, not system constraints.

For other regional standards, review requirements against system capabilities. Double-entry accounting is universal; specific rules vary.

---

## Security and Compliance

### Who can post transactions?

Currently: anyone with access to the Python engine or CLI. There is no authentication or authorization.

The `created_by` parameter is recorded but not validated. Production deployment requires adding authentication layer (API gateway with OAuth, CLI wrapper with user validation, etc.).

See DECISIONS.md "DEC-009 — No Authentication in Engine Layer" for rationale and implementation guidance.

### Is there role-based access control?

No, not in current version. All users who can access the system can perform all operations.

`.env` contains flags like `CORRECTION_APPROVAL_THRESHOLD` but these are not enforced by the code. Implementation requires:
- User authentication
- Permission mapping (who can post, who can reverse, who can create accounts)
- Approval workflows for high-value operations

### How is data integrity verified?

Three mechanisms:

1. **Double-entry validation**: Sum(debits) = Sum(credits) before database commit
2. **SHA-256 hashing**: Each transaction and entry has cryptographic hash
3. **Database triggers**: Block UPDATE/DELETE on posted transactions

Verify integrity: `python ledger_admin_cli.py verify`

### What if someone modifies the database directly?

Database triggers prevent UPDATE and DELETE on posted transactions. Attempting these operations returns error:

```
ERROR 1644 (45000): Cannot modify posted transaction
```

If someone has root database access and disables triggers, modification would:
- Violate hash (stored hash ≠ recalculated hash)
- Be detectable via integrity verification
- Trigger investigation per RUNBOOK.md "Hash Integrity Failure"

**Prevention**: Restrict database permissions. Only application user needs INSERT/SELECT. No users need UPDATE/DELETE.

### How long is data retained?

Default: 7 years (`AUDIT_RETENTION_DAYS=2555` in `.env`).

This aligns with common financial record retention requirements. Angola's specific requirements should be verified with legal/compliance team.

Data older than retention period should be archived (not deleted) per ARCHITECTURE.md "Immutability vs. Storage Cost" trade-off.

### Can I prove to auditors that data hasn't been tampered with?

Yes, via cryptographic hashes:

1. Generate integrity report: `python ledger_admin_cli.py report --type general-ledger --output audit.json --user auditor@company.com`
2. Report includes SHA-256 hash of all data
3. Auditor can regenerate report with same parameters
4. If hashes match, data is identical (no tampering)

Additionally:
- Audit log is immutable and includes all operations
- Database triggers prevent silent modification
- Backup chain provides point-in-time verification

See ARCHITECTURE.md "Cryptographic Integrity" for hash calculation details.

---

## Performance and Scaling

### How many transactions can the system handle?

**Current limits**:
- 999,999 transactions per day (numbering format YYYYMMDD-NNNNNN)
- No tested upper limit on total transactions, but expect degradation above 1 million

**Performance characteristics**:
- Single transaction post: <50ms
- Trial balance with 500 accounts: several seconds (N+1 query issue)
- Reports scale with data volume but remain acceptable up to 100K transactions

See ARCHITECTURE.md "Transaction Volume Ceiling" for details.

### Why is trial balance slow?

The `get_trial_balance()` method executes one SQL query per active account. With 500 accounts, this is 500 queries.

**Solution exists**: SQL view `v_trial_balance` computes all balances in single query. Not yet integrated into Python engine.

**Workaround**: Query view directly via MySQL command-line.

See RUNBOOK.md "Trial Balance Performance Degradation" for implementation.

### Can I use read replicas for reports?

Yes, architecturally supported. `LedgerReportEngine` can be configured with different database URI:

```python
# Primary database for writes
ledger = LedgerEngine(db_uri="mysql://primary/ledger_db")

# Replica database for reads
report_engine = LedgerReportEngine()
report_engine.ledger.db_uri = "mysql://replica/ledger_db"
```

Requires setting up MySQL replication (not included in current deployment).

### How much disk space do I need?

**Estimate**: ~1KB per transaction (includes all journal entries and audit log).

For 10,000 transactions/month:
- Year 1: ~120MB
- Year 3: ~360MB
- Year 7: ~840MB

Add 2x headroom for indexes and temp tables → ~2GB for 7 years of moderate volume.

High-volume scenarios (100K+/month) multiply accordingly. Monitor with `df -h /var/lib/mysql`.

---

## Troubleshooting

### How do I enable debug logging?

Set in `.env`:

```
DEBUG_MODE=True
ENABLE_DETAILED_AUDIT=True
```

Then check logs for detailed SQL queries and operation traces.

**Warning**: Debug mode generates large log volumes. Do not enable in production except during troubleshooting.

### Where are log files located?

Python application logs: stdout/stderr (capture via systemd if running as service)  
MySQL logs: `/var/log/mysql/error.log`  
Audit log: in database (`audit_log` table)

Configure application logging in production to write to dedicated file or logging service.

### How do I test changes without affecting production data?

1. Restore production backup to separate test database
2. Update `.env` → `LEDGER_DB_URI` to point to test database
3. Make changes and test thoroughly
4. Run `verify` to ensure integrity
5. Document changes and migration procedure
6. Apply to production during maintenance window

Never test directly on production database.

### What's the best way to report a bug?

Include:

1. Exact command executed
2. Full error message (not screenshot, copy text)
3. Input data (JSON file content if relevant)
4. Expected behavior
5. Actual behavior
6. Output of `python --version` and `pip freeze`
7. Relevant section of audit log

Avoid "it doesn't work" reports. Specific detail enables faster diagnosis.

---

## Additional Resources

### Where can I learn more about double-entry accounting?

- [Double-Entry Bookkeeping (Wikipedia)](https://en.wikipedia.org/wiki/Double-entry_bookkeeping)
- IFRS Foundation: [www.ifrs.org](https://www.ifrs.org)
- Accounting textbooks covering journal entries, trial balance, and financial statements

System assumes user understands accounting principles. It enforces rules but does not teach accounting.

### How do I contribute to the project?

Currently: Internal use only. Contribution process not defined.

If contribution workflow is established in future:
1. Review ARCHITECTURE.md and DECISIONS.md first
2. Discuss proposed changes before implementing
3. Add tests for new functionality
4. Update documentation
5. Follow coding standards (black, flake8, mypy)

### Where do I get support?

First: consult documentation in order:
1. This FAQ for quick answers
2. RUNBOOK.md for operational issues
3. ARCHITECTURE.md for design understanding
4. DECISIONS.md for design rationale

If issue persists: contact Financial Systems Architecture Team (contact information depends on organizational structure — add appropriate contact details here).

For production incidents: follow escalation criteria in RUNBOOK.md.

---

**Document Version**: 1.0  
**Last Updated**: February 2026  
**Maintained By**: Financial Systems Architecture Team
