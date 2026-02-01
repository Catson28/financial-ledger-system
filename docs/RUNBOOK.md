# Operational Runbook

## Target Audience

On-call engineers, SRE team, database administrators, and compliance officers responding to incidents or performing routine maintenance.

## When to Use This Runbook

Use this document when you observe:

- Transaction posting failures or errors
- Unbalanced transactions detected
- Database connection problems
- Performance degradation (slow reports, high latency)
- Integrity verification failures (hash mismatches)
- Audit trail gaps or anomalies
- Reversal attempts failing
- Planned maintenance activities (backups, schema changes)

For architecture understanding, see ARCHITECTURE.md. For design rationale, see DECISIONS.md.

---

## Quick Reference

| Symptom | Section | Severity |
|---------|---------|----------|
| Cannot post transactions | [Transaction Posting Failure](#transaction-posting-failure) | HIGH |
| Database connection lost | [Database Connection Loss](#database-connection-loss) | HIGH |
| Unbalanced transaction detected | [Double-Entry Violation](#double-entry-violation-detected) | CRITICAL |
| Slow trial balance generation | [Trial Balance Performance](#trial-balance-performance-degradation) | MEDIUM |
| Hash verification fails | [Hash Integrity Failure](#hash-integrity-failure) | CRITICAL |
| Reversal not working | [Reversal Operation Failure](#reversal-operation-failure) | MEDIUM |
| High disk usage | [Database Size Management](#database-size-management) | MEDIUM |
| Backup failed | [Backup Failure](#backup-failure) | HIGH |

---

## Transaction Posting Failure

### Symptoms

- CLI command `post-transaction` returns error
- Error message contains "not balanced", "account not found", or database constraint violation
- Transactions appear in audit log but not in transactions table
- User reports "transaction was rejected"

### Immediate Actions

1. **DO NOT** retry immediately without understanding cause
2. Capture exact error message and transaction input data
3. Verify database connectivity: `mysql -u user -p -h host -e "SELECT 1"`
4. Check audit log for the attempt:
   ```sql
   SELECT * FROM audit_log 
   WHERE user_id = '<user>' 
   AND event_timestamp > NOW() - INTERVAL 1 HOUR 
   ORDER BY event_timestamp DESC 
   LIMIT 10;
   ```

### Diagnostic Steps

**Check 1: Verify account codes exist**

```sql
SELECT account_code, account_name, is_active 
FROM chart_of_accounts 
WHERE account_code IN ('CODE1', 'CODE2', ...);
```

Expected: All referenced accounts exist and `is_active = 1`.

If account missing: User error. Guide user to create account first via:
```bash
python ledger_admin_cli.py create-account --code <code> --name <name> --type <type> --user <user>
```

**Check 2: Verify transaction balances**

Add up debits and credits from input file:
```bash
python -c "
import json
from decimal import Decimal
data = json.load(open('entries.json'))
debits = sum(Decimal(e['amount']) for e in data if e['entry_type'] == 'DEBIT')
credits = sum(Decimal(e['amount']) for e in data if e['entry_type'] == 'CREDIT')
print(f'Debits: {debits}, Credits: {credits}, Balanced: {debits == credits}')
"
```

Expected: Debits exactly equal credits.

If unbalanced: User error in input data. Correct entries.json and retry.

**Check 3: Verify database constraints**

```sql
SHOW CREATE TABLE transactions;
SHOW CREATE TABLE journal_entries;
```

Look for constraint violations in error message. Common causes:
- Duplicate transaction_number (race condition with multiple instances)
- Foreign key violation (parent account does not exist)
- CHECK constraint failure (negative amount, invalid entry_type)

### Safe Corrective Actions

**For missing accounts**:
1. Create required accounts first
2. Retry transaction post with same input
3. Impact: None. Idempotent operation.

**For unbalanced transactions**:
1. Correct input file to balance debits and credits
2. Retry with corrected data
3. Impact: None. Failed attempt creates no database records.

**For duplicate transaction number**:
1. Wait 1 second and retry (sequence will increment)
2. Or wait until next day (daily sequence resets)
3. Impact: Transaction number gap. Acceptable (numbers need not be contiguous).

**For database connection loss**:
1. See [Database Connection Loss](#database-connection-loss) section
2. Retry after connection restored
3. Impact: Delay only. Transaction will succeed when connection available.

### What NOT to Do

- Do NOT manually INSERT into transactions table
- Do NOT modify transaction_number sequence
- Do NOT disable database triggers to "force" transaction through
- Do NOT retry indefinitely without understanding root cause

### Escalation Criteria

Escalate to database team if:
- Database reports internal error (not constraint violation)
- Connection cannot be established after 5 minutes
- Same valid transaction fails repeatedly (suspect trigger corruption)
- Error message is unclear or undocumented

---

## Database Connection Loss

### Symptoms

- Error contains "Can't connect to MySQL", "Lost connection", or "Connection refused"
- All operations fail, not just specific transaction
- `pool_pre_ping=True` prevents most dead connection issues, so active failure indicates recent disconnect

### Immediate Actions

1. Verify database server is running:
   ```bash
   mysql -u user -p -h host -e "SELECT 1"
   ```
2. Check network connectivity:
   ```bash
   ping <database_host>
   telnet <database_host> 3306
   ```
3. Review database error log for recent restarts or crashes

### Diagnostic Steps

**Check 1: Database server status**

```bash
systemctl status mysql  # or mariadb
```

Expected: active (running)

If stopped: Database service is down. Start via `systemctl start mysql`.

**Check 2: Connection limit**

```sql
SHOW VARIABLES LIKE 'max_connections';
SHOW PROCESSLIST;
```

Expected: Current connections < max_connections.

If at limit: Kill idle connections or increase max_connections in MySQL config.

**Check 3: Application connection pool**

Verify `.env` configuration:
```
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
```

If pool exhausted: Connections not being released. Check for code not using context managers properly. All database operations should use:
```python
with self.SessionLocal() as session:
    # operations
```

### Safe Corrective Actions

**For service down**:
1. Start database service: `systemctl start mysql`
2. Verify: `systemctl status mysql`
3. Test connection: `mysql -u user -p -h host -e "SELECT 1"`
4. Retry failed operations
5. Impact: RTO depends on database startup time (~30 seconds). No data loss if database was shutdown cleanly.

**For connection limit**:
1. Immediate: Kill idle connections
   ```sql
   SHOW PROCESSLIST;
   KILL <id>;  -- For idle connections
   ```
2. Long-term: Increase `max_connections` in /etc/mysql/my.cnf
3. Restart MySQL service
4. Impact: Killing connections terminates in-progress queries. Kill only idle connections.

**For network issue**:
1. Verify firewall: `iptables -L` or `firewall-cmd --list-all`
2. Check routing: `traceroute <database_host>`
3. Contact network team if outside application scope
4. Impact: Depends on network resolution time.

### Post-Incident Verification

1. Verify audit log continuity:
   ```sql
   SELECT DATE(event_timestamp) AS day, COUNT(*) AS events
   FROM audit_log
   WHERE event_timestamp > NOW() - INTERVAL 7 DAY
   GROUP BY day;
   ```
   Look for gaps during incident period.

2. Check for partial transactions (should be none due to rollback):
   ```sql
   SELECT COUNT(*) FROM transactions WHERE status = 'PENDING';
   ```
   Expected: 0 (system does not use PENDING state).

3. Run integrity check:
   ```bash
   python ledger_admin_cli.py verify
   ```
   Expected: "All transactions balanced correctly!"

### What NOT to Do

- Do NOT increase connection pool size arbitrarily (may exhaust database connections)
- Do NOT disable `pool_pre_ping` (removes dead connection detection)
- Do NOT modify database while investigating (can destroy evidence)

### Escalation Criteria

Escalate to infrastructure team if:
- Database cannot be restarted
- Connection limit increase does not resolve issue
- Network team must investigate routing or firewall
- Repeated connection losses indicate infrastructure problem

---

## Double-Entry Violation Detected

### Symptoms

- `verify` command reports "Debits != Credits" for one or more transactions
- Trial balance does not zero out (total debits - total credits != 0)
- Audit report shows integrity violation

### Immediate Actions

**STOP. This is a CRITICAL integrity issue.**

1. Identify affected transaction(s):
   ```bash
   python ledger_admin_cli.py verify
   ```
   Output will list transaction numbers where debits != credits.

2. Do NOT post new transactions until root cause is identified
3. Notify compliance team immediately
4. Capture full transaction details:
   ```sql
   SELECT t.*, 
          (SELECT SUM(amount) FROM journal_entries WHERE transaction_id = t.transaction_id AND entry_type = 'DEBIT') AS total_debits,
          (SELECT SUM(amount) FROM journal_entries WHERE transaction_id = t.transaction_id AND entry_type = 'CREDIT') AS total_credits
   FROM transactions t
   WHERE transaction_number = '<number>';
   
   SELECT * FROM journal_entries WHERE transaction_id = '<id>';
   ```

### Diagnostic Steps

**This should never happen with data created via engine.** Double-entry violation indicates:
- Direct database modification bypassing application
- Database corruption
- Software bug in validation logic

**Check 1: Verify hash integrity**

```python
import json, hashlib
from decimal import Decimal

# Get transaction and entries from database
# Recalculate hash
hash_input = {
    'transaction_id': transaction_id,
    'transaction_date': transaction_date.isoformat(),
    'entries': [{'account': e.account_code, 'type': e.entry_type, 'amount': str(e.amount)} for e in entries]
}
calculated_hash = hashlib.sha256(json.dumps(hash_input, sort_keys=True).encode()).hexdigest()

# Compare with stored hash
print(f"Stored: {stored_hash}")
print(f"Calculated: {calculated_hash}")
print(f"Match: {stored_hash == calculated_hash}")
```

If hashes match: Data was modified after hash calculation (database tampering).

If hashes differ: Data corruption during storage or transmission.

**Check 2: Review audit log for the transaction**

```sql
SELECT * FROM audit_log 
WHERE transaction_id = '<id>' 
ORDER BY event_timestamp;
```

Look for:
- Who created the transaction (`user_id`, `source_system`)
- When it was created (`event_timestamp`)
- Any subsequent events referencing this transaction
- Any manual database operations in window (check DBA logs)

**Check 3: Verify trigger integrity**

```sql
SHOW TRIGGERS FROM ledger_db;
```

Expected triggers:
- `trg_prevent_transaction_update` on transactions table
- `trg_prevent_transaction_delete` on transactions table

If missing: Database triggers were dropped or disabled. Immutability is compromised.

### Safe Corrective Actions

**DO NOT modify the invalid transaction. Instead:**

1. **Document the violation**:
   - Screenshot of verify output
   - Full SQL dumps of affected transaction and entries
   - Hash verification results
   - Audit log excerpt

2. **Create correction transaction**:
   ```bash
   # Calculate difference
   # If debits > credits by X, create correcting entry:
   # CREDIT the overstated account by X
   # DEBIT an appropriate suspense/adjustment account by X
   ```

3. **Mark original transaction for review**:
   ```sql
   -- Add note to audit log (manual insert, one-time exception)
   INSERT INTO audit_log (audit_id, event_timestamp, event_type, severity, user_id, source_system, action, description, transaction_id)
   VALUES (UUID(), NOW(), 'INTEGRITY_VIOLATION', 'CRITICAL', 'SYSTEM', 'MANUAL_CORRECTION', 'MARK_INVALID', 
           'Double-entry violation detected. Corrected via transaction <correction_txn_id>', '<invalid_txn_id>');
   ```

4. **Generate integrity report for compliance**:
   ```bash
   python ledger_admin_cli.py report --type general-ledger --start-date <date> --end-date <date> --output violation_report.json --user compliance@company.com
   ```

### Post-Incident Actions

1. **Investigate root cause**:
   - Review database access logs for manual modifications
   - Check application logs for errors during transaction post
   - Verify no code deployment occurred around transaction timestamp
   - Examine backup to see if corruption existed in backup

2. **Prevent recurrence**:
   - Audit database permissions (who can UPDATE/DELETE?)
   - Verify triggers are enabled and correct
   - Add automated daily integrity check via cron
   - Consider read-only replicas for all non-posting access

3. **Compliance notification**:
   - Prepare incident report with timeline
   - Document correction transaction
   - Explain impact on financial reports
   - Provide evidence that corrected data is now valid

### What NOT to Do

- Do NOT UPDATE journal_entries to fix amounts
- Do NOT DELETE invalid entries
- Do NOT regenerate transaction hash to match invalid data
- Do NOT hide the violation (this is fraud)

### Escalation Criteria

**This incident ALWAYS escalates.**

Notify immediately:
- Compliance team (responsible for financial accuracy)
- Database administrator (investigate how data was modified)
- Security team (if tampering suspected)
- External auditor (if audit is in progress)

Escalate to executive management if:
- Tampering is confirmed
- Financial reports have been issued with invalid data
- Multiple transactions affected
- Root cause cannot be determined

---

## Trial Balance Performance Degradation

### Symptoms

- Trial balance generation takes >30 seconds
- User reports "report is hanging"
- Database CPU usage spikes during report generation
- Query timeout errors

### Immediate Actions

1. Check number of active accounts:
   ```sql
   SELECT COUNT(*) FROM chart_of_accounts WHERE is_active = 1;
   ```

2. Check total transaction volume:
   ```sql
   SELECT COUNT(*) FROM transactions;
   SELECT COUNT(*) FROM journal_entries;
   ```

3. Monitor database during trial balance generation:
   ```sql
   SHOW PROCESSLIST;
   ```
   Look for multiple queries with similar pattern (indicates N+1 problem).

### Diagnostic Steps

**Root cause**: `get_trial_balance()` method executes one query per active account. With 500 accounts and 10,000 transactions, this is 500 queries.

**Check 1: Verify view exists**

```sql
SHOW CREATE VIEW v_trial_balance;
```

Expected: View exists and selects from v_account_balances.

If missing: View was dropped or database was not initialized with full schema.

**Check 2: Test view performance**

```sql
SELECT * FROM v_trial_balance;
```

Time this query. Should complete in <2 seconds even with thousands of transactions.

**Check 3: Verify indexes**

```sql
SHOW INDEX FROM journal_entries;
SHOW INDEX FROM transactions;
```

Required indexes:
- journal_entries(account_code)
- journal_entries(transaction_id)
- transactions(status)

If missing: Indexes were dropped. Recreate from schema.

### Safe Corrective Actions

**Short-term workaround (immediate relief)**:

Use SQL view directly instead of Python method:

```bash
mysql -u user -p -h host ledger_db -e "SELECT * FROM v_trial_balance" > trial_balance.csv
```

Impact: Bypasses Python engine. Report metadata (report_id, hash) not generated. Acceptable for ad-hoc queries.

**Medium-term fix (code modification)**:

Modify `LedgerReportEngine.generate_trial_balance()` to use view:

```python
# In /home/claude/ledger_reporting.py
def generate_trial_balance(self, as_of_date, generated_by, include_zero_balances=False):
    with self.session_factory() as session:
        # Use view instead of calling get_account_balance() per account
        result = session.execute(text("""
            SELECT account_code, account_name, account_type, balance
            FROM v_trial_balance
            ORDER BY account_code
        """))
        accounts = [dict(row) for row in result]
        # Continue with report generation...
```

Impact: Single query instead of N queries. 10-100x performance improvement. Requires code deployment.

**Long-term fix (database optimization)**:

Add materialized view or summary table updated via trigger:

```sql
CREATE TABLE account_balance_cache (
    account_code VARCHAR(50) PRIMARY KEY,
    balance DECIMAL(20,2),
    last_updated DATETIME
);

-- Trigger to update cache on each journal entry insert
-- (implementation details omitted)
```

Impact: Trial balance reads from cache table, no computation needed. Requires schema migration and trigger development.

### Post-Action Verification

1. Measure performance after fix:
   ```bash
   time python ledger_admin_cli.py trial-balance --output test.json
   ```
   Expected: <5 seconds for 500 accounts.

2. Verify report accuracy (compare with slow method):
   ```bash
   # Generate with old method (slow)
   # Generate with new method (fast)
   # Compare outputs - should be identical
   diff old_report.json new_report.json
   ```

### What NOT to Do

- Do NOT increase database query timeout to mask performance problem
- Do NOT add caching without considering data staleness
- Do NOT disable indexes to reduce write overhead (makes read performance worse)

### Escalation Criteria

Escalate to development team if:
- View does not exist and cannot be created from schema
- Code modification is required but no deployment window available
- Performance remains poor even with view (indicates different bottleneck)

---

## Hash Integrity Failure

### Symptoms

- `verify_report_integrity()` returns hash mismatch
- Recalculated transaction hash differs from stored hash
- Report regenerated with same parameters produces different hash

### Immediate Actions

**STOP. This is CRITICAL.**

1. Do NOT dismiss as "software bug" without investigation
2. Isolate affected transaction or report
3. Capture evidence:
   ```sql
   SELECT * FROM transactions WHERE transaction_id = '<id>';
   SELECT * FROM journal_entries WHERE transaction_id = '<id>';
   ```

4. Notify compliance team immediately

### Diagnostic Steps

**Check 1: Verify data has not been modified**

Compare current data with backup:

```bash
# Restore transaction from last known good backup to temporary table
mysqldump -u user -p -h host ledger_db transactions --where="transaction_id='<id>'" > backup_txn.sql

# Compare fields
# If different: data was modified after hash calculation
```

**Check 2: Recalculate hash manually**

```python
import json, hashlib
from decimal import Decimal

# Get transaction and entries from database
transaction_id = '<id>'
transaction_date = '<date>'  # from database
entries = [
    {'account': 'CODE1', 'type': 'DEBIT', 'amount': '1000.00'},
    {'account': 'CODE2', 'type': 'CREDIT', 'amount': '1000.00'}
]  # from database

hash_input = json.dumps({
    'transaction_id': transaction_id,
    'transaction_date': transaction_date.isoformat(),
    'entries': [{'account': e['account'], 'type': e['type'], 'amount': str(e['amount'])} for e in entries]
}, sort_keys=True)

calculated_hash = hashlib.sha256(hash_input.encode()).hexdigest()
print(f"Calculated: {calculated_hash}")
print(f"Stored: <hash_from_database>")
```

**Check 3: Review audit log**

```sql
SELECT * FROM audit_log 
WHERE transaction_id = '<id>' 
OR description LIKE '%<transaction_number>%'
ORDER BY event_timestamp;
```

Look for:
- Manual database operations
- Unexpected UPDATE statements
- System events during hash mismatch window

### Safe Corrective Actions

**If data was NOT modified (software bug):**

1. Regenerate hash with correct algorithm
2. Document bug in issue tracker
3. Update stored hash:
   ```sql
   -- ONE-TIME EXCEPTION: Only if proven to be software bug
   UPDATE transactions SET transaction_hash = '<correct_hash>' WHERE transaction_id = '<id>';
   ```
4. Log correction in audit trail

Impact: Restores integrity verification. No financial data changed.

**If data WAS modified (tampering or corruption):**

1. DO NOT UPDATE hash
2. Mark transaction for investigation:
   ```sql
   INSERT INTO audit_log (audit_id, event_timestamp, event_type, severity, user_id, source_system, action, description, transaction_id)
   VALUES (UUID(), NOW(), 'HASH_VIOLATION', 'CRITICAL', 'SYSTEM', 'INTEGRITY_CHECK', 'TAMPER_DETECTED', 
           'Hash mismatch indicates data modification. Original hash: <original>, Current hash: <recalculated>', '<id>');
   ```
3. Restore transaction from backup if available
4. Generate correction transaction if restore not possible
5. Forensic investigation to determine how modification occurred

### Post-Incident Actions

1. **Security audit**:
   - Review database access logs for modification attempts
   - Verify trigger integrity (SHOW TRIGGERS)
   - Check user permissions (who can UPDATE transactions?)

2. **Implement prevention**:
   - Schedule daily hash verification job
   - Add monitoring alert on hash mismatches
   - Restrict database permissions (read-only for non-admin users)
   - Enable database audit logging

3. **Compliance reporting**:
   - Document incident with timeline
   - Explain impact on financial reports
   - Demonstrate corrective actions taken
   - Provide assurance controls are strengthened

### What NOT to Do

- Do NOT update hash to match modified data (this conceals tampering)
- Do NOT dismiss hash mismatch as "rounding error" (hashes are deterministic)
- Do NOT continue posting new transactions before root cause identified

### Escalation Criteria

**This incident ALWAYS escalates.**

Notify immediately:
- Security team (potential tampering)
- Database administrator (investigate modification source)
- Compliance team (financial data integrity)
- External auditor (if audit in progress)

Escalate to law enforcement if tampering suspected.

---

## Reversal Operation Failure

### Symptoms

- `reverse` command returns error
- Error message contains "already reversed", "not POSTED", or "transaction not found"
- User reports reversal was rejected

### Immediate Actions

1. Verify transaction exists and status:
   ```sql
   SELECT transaction_id, transaction_number, status, reversed_by_transaction_id
   FROM transactions
   WHERE transaction_number = '<number>';
   ```

2. Check if reversal already exists:
   ```sql
   SELECT * FROM transactions
   WHERE reverses_transaction_id = '<original_id>';
   ```

### Diagnostic Steps

**Check 1: Transaction status**

Expected: `status = 'POSTED'` and `reversed_by_transaction_id IS NULL`

Common failures:
- Status is REVERSED: Already reversed (find existing reversal)
- Status is PENDING: Transaction not yet posted (cannot reverse)
- Status is CANCELLED: Transaction was cancelled, not posted

**Check 2: User permissions (future feature)**

Currently no permissions check. If reversal fails for authorization, indicates future RBAC implementation.

**Check 3: Date constraints (future feature)**

`.env` defines `MAX_CORRECTION_AGE_DAYS=90` but not enforced. If reversal fails citing age, indicates enforcement was added.

### Safe Corrective Actions

**For already reversed transaction**:

1. Find existing reversal:
   ```sql
   SELECT * FROM transactions
   WHERE transaction_id = (SELECT reversed_by_transaction_id FROM transactions WHERE transaction_number = '<number>');
   ```

2. Verify reversal is correct (entries are inverted)
3. No action needed - reversal already exists

Impact: None. Inform user of existing reversal.

**For non-POSTED transaction**:

1. Check why transaction is not POSTED
2. If legitimately PENDING: post transaction first, then reverse
3. If erroneously CANCELLED: investigate why

Impact: Requires investigation before reversal.

**For missing transaction**:

1. Verify transaction number is correct
2. Check audit log for transaction creation:
   ```sql
   SELECT * FROM audit_log WHERE event_type = 'TRANSACTION_POSTED' AND description LIKE '%<number>%';
   ```
3. If in audit log but not in transactions table: data corruption, restore from backup

### Post-Reversal Verification

1. Verify reversal transaction exists:
   ```sql
   SELECT * FROM transactions WHERE is_reversal = 1 AND reverses_transaction_id = '<original_id>';
   ```

2. Verify original transaction marked:
   ```sql
   SELECT status, reversed_by_transaction_id FROM transactions WHERE transaction_id = '<original_id>';
   ```
   Expected: `status = 'REVERSED'`, `reversed_by_transaction_id = <reversal_id>`

3. Verify entries are inverted:
   ```sql
   SELECT account_code, entry_type, amount FROM journal_entries WHERE transaction_id = '<original_id>';
   SELECT account_code, entry_type, amount FROM journal_entries WHERE transaction_id = '<reversal_id>';
   ```
   Each DEBIT in original should have matching CREDIT in reversal.

4. Verify balances updated:
   ```bash
   python ledger_admin_cli.py balance --account-code <affected_account>
   ```

### What NOT to Do

- Do NOT manually UPDATE status to REVERSED
- Do NOT DELETE original transaction instead of reversing
- Do NOT modify journal entries to "fix" instead of reversing

### Escalation Criteria

Escalate to development team if:
- Valid reversal request fails for unknown reason
- Error message is unclear
- Business rules prevent legitimate reversal (need exception process)

---

## Database Size Management

### Symptoms

- Disk usage alert triggered
- Backup time increasing significantly
- `df -h` shows database partition >80% full

### Immediate Actions

1. Check current database size:
   ```sql
   SELECT 
       table_schema AS 'Database',
       SUM(data_length + index_length) / 1024 / 1024 / 1024 AS 'Size_GB'
   FROM information_schema.tables
   WHERE table_schema = 'ledger_db'
   GROUP BY table_schema;
   ```

2. Check table sizes:
   ```sql
   SELECT 
       table_name AS 'Table',
       ROUND((data_length + index_length) / 1024 / 1024, 2) AS 'Size_MB'
   FROM information_schema.tables
   WHERE table_schema = 'ledger_db'
   ORDER BY (data_length + index_length) DESC;
   ```

3. Check transaction count:
   ```sql
   SELECT COUNT(*) AS total_transactions,
          MIN(created_at) AS oldest,
          MAX(created_at) AS newest
   FROM transactions;
   ```

### Diagnostic Steps

**Expected growth pattern**:
- Audit log grows fastest (1 entry per transaction + 1 per report)
- Journal entries grow linearly with transactions (2-10 entries per transaction)
- Transactions table grows linearly (1 per post)

**Check 1: Identify largest tables**

From query above, typically:
1. audit_log (largest, unbounded growth)
2. journal_entries (2nd largest)
3. transactions (3rd largest)

**Check 2: Review retention policy**

`.env` defines:
- `AUDIT_RETENTION_DAYS=2555` (7 years)
- `REPORT_RETENTION_DAYS=2555` (7 years)

Data older than retention period is candidate for archiving.

**Check 3: Check for orphaned data**

```sql
-- Journal entries without transaction (should be 0)
SELECT COUNT(*) FROM journal_entries je
LEFT JOIN transactions t ON je.transaction_id = t.transaction_id
WHERE t.transaction_id IS NULL;
```

### Safe Corrective Actions

**Short-term (immediate relief)**:

1. Archive old audit log entries (read-only archiving, do not delete):
   ```bash
   # Export audit log older than 2 years to file
   mysql -u user -p -h host ledger_db -e "
   SELECT * FROM audit_log 
   WHERE event_timestamp < DATE_SUB(NOW(), INTERVAL 2 YEAR)
   " > audit_archive_$(date +%Y%m%d).sql
   
   # Verify export
   wc -l audit_archive_*.sql
   
   # Compress
   gzip audit_archive_*.sql
   
   # Store in archive location (S3, tape, etc.)
   ```

2. Consider partitioning audit_log by year:
   ```sql
   -- This requires table rebuild, plan maintenance window
   ALTER TABLE audit_log PARTITION BY RANGE (YEAR(event_timestamp)) (
       PARTITION p2024 VALUES LESS THAN (2025),
       PARTITION p2025 VALUES LESS THAN (2026),
       PARTITION p2026 VALUES LESS THAN (2027),
       PARTITION pmax VALUES LESS THAN MAXVALUE
   );
   ```

**Medium-term (proactive management)**:

1. Implement scheduled archiving job (monthly):
   ```bash
   # Cron job to archive audit log older than 3 years
   0 1 1 * * /usr/local/bin/archive_audit_log.sh
   ```

2. Monitor database growth:
   ```bash
   # Daily size check with alert
   0 6 * * * /usr/local/bin/check_db_size.sh
   ```

**Long-term (architectural change)**:

1. Move old transactions to separate cold storage database
2. Keep last 3 years in hot database
3. Union queries across hot and cold when needed

Impact: Requires application changes to query multiple databases. Not implemented in current version.

### What NOT to Do

- Do NOT DELETE from audit_log without archiving first
- Do NOT DELETE from transactions (violates immutability)
- Do NOT TRUNCATE any table (data loss)
- Do NOT disable indexes to save space (destroys performance)

### Escalation Criteria

Escalate to database team if:
- Disk will be full within 48 hours
- Partition resizing required
- Architectural change needed (hot/cold split)

---

## Backup Failure

### Symptoms

- Backup cron job failed
- Backup file size is 0 or much smaller than expected
- Email alert "backup failed"

### Immediate Actions

1. Check backup status:
   ```bash
   ls -lh /backup/ledger_db_*.sql.gz
   tail -50 /var/log/backup_ledger.log
   ```

2. Verify database is accessible:
   ```bash
   mysqldump -u user -p -h host --single-transaction ledger_db > /dev/null
   echo $?  # Should be 0
   ```

3. Check disk space on backup destination:
   ```bash
   df -h /backup
   ```

### Diagnostic Steps

**Check 1: Backup script permissions**

```bash
ls -l /usr/local/bin/backup_ledger.sh
```

Expected: Executable by backup user.

**Check 2: Database credentials**

```bash
# Test credentials used by backup script
mysql -u backup_user -p -h host ledger_db -e "SELECT 1"
```

**Check 3: Network connectivity** (if remote backup)

```bash
ping <backup_server>
nc -zv <backup_server> <backup_port>
```

### Safe Corrective Actions

**For permission issue**:

```bash
chmod +x /usr/local/bin/backup_ledger.sh
chown backup_user:backup_group /usr/local/bin/backup_ledger.sh
```

Impact: None. Fixes execution permission.

**For disk space issue**:

```bash
# Delete old backups beyond retention period
find /backup -name "ledger_db_*.sql.gz" -mtime +90 -delete

# Or move to archive storage
find /backup -name "ledger_db_*.sql.gz" -mtime +90 -exec mv {} /archive/ \;
```

Impact: Frees disk space. Verify files moved to archive successfully.

**For credential issue**:

```bash
# Update backup script with correct credentials
# Test manually first:
mysqldump -u backup_user -p -h host --single-transaction --routines --triggers ledger_db | gzip > /backup/manual_test.sql.gz

# Verify size is reasonable:
ls -lh /backup/manual_test.sql.gz

# If successful, update automated script
```

Impact: None if tested manually first.

**For failed backup (perform manual backup immediately)**:

```bash
# Full backup with all options
mysqldump \
  -u backup_user -p \
  -h host \
  --single-transaction \
  --routines \
  --triggers \
  --events \
  --flush-logs \
  --master-data=2 \
  ledger_db | gzip > /backup/ledger_db_$(date +%Y%m%d_%H%M%S).sql.gz

# Verify backup integrity
gunzip -c /backup/ledger_db_*.sql.gz | mysql -u user -p -h test_host test_db

# Compare row counts
mysql -u user -p -h host ledger_db -e "SELECT COUNT(*) FROM transactions"
mysql -u user -p -h test_host test_db -e "SELECT COUNT(*) FROM transactions"
```

Impact: Creates valid backup. Test restore required to verify.

### Post-Backup Verification

1. **Verify backup file exists and has reasonable size**:
   ```bash
   ls -lh /backup/ledger_db_$(date +%Y%m%d)*.sql.gz
   ```
   Expected: Size should be proportional to database size (~70% compression ratio).

2. **Test restore to temporary database**:
   ```bash
   mysql -u user -p -h host -e "CREATE DATABASE ledger_backup_test"
   gunzip -c /backup/latest.sql.gz | mysql -u user -p -h host ledger_backup_test
   mysql -u user -p -h host ledger_backup_test -e "SELECT COUNT(*) FROM transactions"
   mysql -u user -p -h host -e "DROP DATABASE ledger_backup_test"
   ```

3. **Verify backup contains triggers**:
   ```bash
   gunzip -c /backup/latest.sql.gz | grep "CREATE TRIGGER" | wc -l
   ```
   Expected: At least 2 (prevent update and delete on transactions).

### What NOT to Do

- Do NOT skip backup verification (silent corruption possible)
- Do NOT delete old backups without verifying new backup is valid
- Do NOT backup to same disk as database (single point of failure)

### Escalation Criteria

Escalate to infrastructure team if:
- Multiple consecutive backup failures
- Backup size inconsistent with database growth
- Network issues prevent remote backup
- Backup window exceeds maintenance window

---

## Scheduled Maintenance

### Pre-Maintenance Checklist

□ Notify users of maintenance window (email, Slack, etc.)
□ Verify last backup is valid and accessible
□ Check audit log is current (no gaps)
□ Run integrity verification: `python ledger_admin_cli.py verify`
□ Document current transaction count and latest transaction number
□ Prepare rollback plan

### Database Schema Migration

**Example: Renaming column (e.g., metadata → event_metadata)**

1. **Test migration on backup first**:
   ```bash
   # Restore backup to test database
   mysql -u user -p -h host -e "CREATE DATABASE ledger_test"
   gunzip -c /backup/latest.sql.gz | mysql -u user -p -h host ledger_test
   
   # Apply migration
   mysql -u user -p -h host ledger_test < migracao_metadata.sql
   
   # Verify
   mysql -u user -p -h host ledger_test -e "DESCRIBE audit_log"
   ```

2. **Stop application** (prevent writes during migration):
   ```bash
   systemctl stop ledger_app
   ```

3. **Backup immediately before migration**:
   ```bash
   mysqldump -u user -p -h host --single-transaction ledger_db | gzip > /backup/pre_migration_$(date +%Y%m%d_%H%M%S).sql.gz
   ```

4. **Apply migration**:
   ```bash
   mysql -u user -p -h host ledger_db < migracao_metadata.sql
   ```

5. **Verify migration**:
   ```sql
   DESCRIBE audit_log;  -- Verify column renamed
   SELECT COUNT(*) FROM audit_log WHERE event_metadata IS NOT NULL;
   ```

6. **Test application functionality**:
   ```bash
   # Update .env if needed
   # Test posting a transaction
   python ledger_admin_cli.py verify
   ```

7. **Start application**:
   ```bash
   systemctl start ledger_app
   ```

### Post-Maintenance Verification

1. **Verify all critical functions**:
   ```bash
   python ledger_admin_cli.py verify
   python ledger_admin_cli.py trial-balance --output test.json
   ```

2. **Check audit log continuity**:
   ```sql
   SELECT MIN(event_timestamp), MAX(event_timestamp), COUNT(*)
   FROM audit_log
   WHERE event_timestamp > DATE_SUB(NOW(), INTERVAL 1 DAY);
   ```

3. **Monitor application logs** for errors

4. **Notify users** maintenance is complete

### Rollback Procedure

If migration fails or causes issues:

```bash
# Stop application
systemctl stop ledger_app

# Restore pre-migration backup
mysql -u user -p -h host -e "DROP DATABASE ledger_db"
mysql -u user -p -h host -e "CREATE DATABASE ledger_db"
gunzip -c /backup/pre_migration_*.sql.gz | mysql -u user -p -h host ledger_db

# Verify restore
mysql -u user -p -h host ledger_db -e "SELECT COUNT(*) FROM transactions"

# Start application with old code
systemctl start ledger_app
```

Impact: Transactions posted during migration are lost. Window should be minimized.

---

**Document Version**: 1.0  
**Last Updated**: February 2026  
**Review Cycle**: After each production incident or quarterly  
**On-Call Contact**: [Add contact information for on-call engineer]
