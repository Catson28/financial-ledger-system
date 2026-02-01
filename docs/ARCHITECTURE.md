# System Architecture

## Target Audience

This document is written for: software architects reviewing the system design, senior developers implementing integrations or extensions, compliance officers validating audit trail completeness, and external auditors verifying system integrity.

If you need operational procedures, see RUNBOOK.md. If you need implementation history, see DECISIONS.md.

## Context and Constraints

### Environment

The system operates in Angola's commercial and industrial sectors under IFRS accounting standards. Financial data has legal value for official reporting, external audit verification, and regulatory compliance. Transactions must remain immutable for 7 years minimum.

Current deployment is on-premises with MySQL 8.0+ database. Cloud migration is architecturally possible without code rewrite (SQLAlchemy abstractions allow database URI substitution).

### Operating Constraints

- **Single instance only**: Transaction numbering uses count-then-increment, creating race condition with multiple instances
- **Business hours availability**: No high-availability infrastructure (replica reads, load balancer, health checks)
- **Backup frequency**: Daily at 2 AM, yielding RTO up to 24 hours and RPO up to 24 hours
- **Volume ceiling**: Transaction numbering supports 999,999 transactions per day before rollover
- **Performance profile**: Individual transaction posts resolve in <50ms; trial balance with 500+ accounts may take several seconds

### Regulatory Pressures

IFRS requirements enforced by system design:

- Recognition by economic event (transaction_date) separate from accounting posting (posting_date)
- Immutable transaction records after posting
- Complete audit trail with user identification and timestamps
- Reproducible reports with cryptographic verification
- Retention period enforcement (7 years minimum for financial records)

## Architectural Objectives

The system maintains these invariants across all operations:

### 1. Immutability

Once a transaction reaches POSTED status, no field can be modified and no entry can be deleted. This is enforced at three levels:

- Application layer: Python engine provides no update or delete methods for posted transactions
- Database layer: MySQL triggers block UPDATE and DELETE operations on transactions table when status = 'POSTED'
- Audit layer: Every operation is logged before commit; rollback does not erase audit entry

**Verification**: Query `SELECT * FROM transactions WHERE status = 'POSTED'` and attempt direct UPDATE or DELETE in MySQL console. Operation will fail with trigger violation.

### 2. Double-Entry Balance

Every transaction must have total debits exactly equal to total credits before database commit. This is enforced:

- Input validation: `TransactionInput.validate()` rejects unbalanced transactions before database interaction
- Database constraint: CHECK constraints on journal_entries table prevent negative amounts
- Post-commit verification: `verify_double_entry_integrity()` method available for periodic audits

**Consequence of failure**: If imbalance is detected post-commit (indicating database corruption), system continues operating but marks transaction in integrity report. No automatic remediation — requires manual investigation.

### 3. Cryptographic Integrity

Each transaction and each journal entry carries SHA-256 hash calculated from immutable fields. Hash input includes: transaction ID, date, and ordered list of all entries with account code, type, and amount.

Hashes are calculated once at creation and stored permanently. System does not automatically re-verify hashes — verification must be triggered manually via `verify_report_integrity()` for reports.

**Limitation**: Hash corruption is not detected automatically. Periodic scheduled verification job must be implemented externally.

### 4. Complete Audit Trail

Every write operation generates audit log entry before commit. Audit includes: event type, severity level, user ID, source system, source IP, timestamp (UTC), action performed, affected entity, and structured metadata in JSON format.

**Current gap**: Failed operations do not generate audit entries. System rolls back and raises exception without logging the failure. For production compliance, failed attempts (especially reversals and account creation) should log before rollback with severity WARNING or ERROR.

### 5. Controlled Evolution

Schema changes follow forward-only migration pattern. New functionality adds tables or columns; existing data is never altered in-place. Account structure supports versioning via `version` field (currently unused but present in schema).

Chart of accounts modifications:

- New accounts: Added via `create_account()` with unique code
- Account deactivation: Set `is_active = FALSE`, removes from new reports but preserves historical references
- Account renaming: Create new account and transfer balances via adjustment transaction — never modify name of account with existing transactions

## Non-Objectives

The system deliberately does NOT:

1. **Support multi-currency transactions**: Single transaction cannot mix currencies. Each journal entry stores currency field but engine always writes AOA. Cross-currency requires external conversion layer.

2. **Provide real-time replication**: No write-ahead log, no synchronous replica, no automatic failover. DR site configuration exists in .env but is not implemented in engine.

3. **Enforce role-based access control**: All operations accept `created_by` as string parameter without validation. Authentication and authorization must be implemented in calling layer (API, CLI wrapper, or integration middleware).

4. **Detect hash corruption automatically**: Hashes are calculated and stored but not periodically re-verified. Integrity verification is available via method call but not scheduled.

5. **Scale horizontally without code changes**: Single-instance limitation due to transaction numbering race condition. Horizontal scaling requires sequence-based numbering or distributed ID generation.

6. **Support closing period locks**: Schema includes `closing_periods` table but Python engine has no implementation. Transactions can be posted to any date regardless of period status.

## System Overview

### Component Map

```
┌─────────────────────────────────────────────────────────────┐
│                    CLIENT LAYER                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ CLI Admin    │  │ Discovery    │  │ Future: API  │      │
│  │ Tool         │  │ Tool         │  │ (FastAPI)    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    ENGINE LAYER                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ LedgerEngine (ledger_engine.py)                      │   │
│  │  - create_account()                                  │   │
│  │  - post_transaction()                                │   │
│  │  - reverse_transaction()                             │   │
│  │  - get_account_balance()                             │   │
│  │  - verify_double_entry_integrity()                   │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ LedgerReportEngine (ledger_reporting.py)             │   │
│  │  - generate_trial_balance()                          │   │
│  │  - generate_balance_sheet()                          │   │
│  │  - generate_income_statement()                       │   │
│  │  - generate_general_ledger()                         │   │
│  │  - generate_audit_trail()                            │   │
│  │  - verify_report_integrity()                         │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   DATABASE LAYER                            │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ Chart of    │  │ Transactions │  │ Journal      │       │
│  │ Accounts    │  │              │  │ Entries      │       │
│  └─────────────┘  └──────────────┘  └──────────────┘       │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ Audit Log   │  │ Closing      │  │ SQL Views    │       │
│  │ (immutable) │  │ Periods      │  │ (balances)   │       │
│  └─────────────┘  └──────────────┘  └──────────────┘       │
│                                                              │
│  Triggers: Block DELETE/UPDATE on posted transactions       │
└─────────────────────────────────────────────────────────────┘
```

### Responsibilities

**LedgerEngine**

Core accounting operations. Responsible for:

- Validating transaction balance (debits = credits) before database interaction
- Generating sequential transaction numbers (format: YYYYMMDD-NNNNNN)
- Calculating SHA-256 hashes for transactions and journal entries
- Creating reversal transactions by inverting original entries
- Enforcing account existence before posting
- Logging all operations to audit trail

Does NOT: authenticate users, enforce approval workflows, schedule jobs, replicate data, or manage database migrations.

**LedgerReportEngine**

Report generation with reproducibility guarantee. Responsible for:

- Querying transaction and balance data via SQLAlchemy session
- Calculating account balances by type (assets/liabilities use different debit/credit logic)
- Generating report metadata with SHA-256 hash
- Exporting to JSON and CSV formats
- Providing hash verification for previously generated reports

Does NOT: cache results, enforce access control on report data, schedule report generation, or store generated reports in database.

**Database Triggers (MySQL)**

Immutability enforcement. Responsible for:

- Blocking DELETE operations on transactions with status = 'POSTED'
- Blocking UPDATE operations on transactions with status = 'POSTED'
- Raising clear error messages on violation attempts

Does NOT: validate business logic, enforce double-entry balance, or log to audit trail (logging happens in Python layer before trigger execution).

**Audit Log**

Immutable event recording. Responsible for:

- Storing all write operations with timestamp, user, source system, and structured metadata
- Supporting queries by date range, event type, user, and severity level
- Preserving record of reversals and corrections

Does NOT: log failed operations (current gap), log read operations (configurable but not implemented), or automatically alert on critical events.

## Boundaries and Justification

### Engine Layer ↔ Client Layer

**Boundary**: Python function calls with typed dataclasses (`TransactionInput`, `AccountDefinition`)

**Justification**: Separates business logic (double-entry validation, hash calculation) from presentation (CLI formatting, future API serialization). Engine has zero knowledge of how it is invoked — same code serves CLI, future API, or batch jobs.

**Consequence**: Client must construct valid input objects. Engine validates but does not guide — error messages are technical, not user-friendly.

### Engine Layer ↔ Database Layer

**Boundary**: SQLAlchemy ORM with explicit session management

**Justification**: Database independence. Switching from MySQL to PostgreSQL requires only SQL script rewrite (triggers, initial schema), not Python code changes. Session scope is explicit to prevent connection leaks.

**Consequence**: ORM overhead adds latency versus raw SQL. Trial balance performance suffers from N+1 query pattern (one query per account). Optimization requires bypassing ORM to use pre-built SQL view.

**Why not use SQL view in Python?** Engineering trade-off. View exists for manual SQL access and future optimization. Current Python code prioritizes clarity (explicit balance calculation logic) over performance. Production deployment with high account counts should use view via raw SQL query.

### Report Engine ↔ Ledger Engine

**Boundary**: Separate class with shared database session factory

**Justification**: Reports are read operations with different lifecycle than write operations. Separation allows:

- Independent scaling: report generation can move to replica database
- Different security model: reports may be accessible to users without transaction posting rights
- Hash calculation specific to reports, not transactions

**Consequence**: Duplicate code for balance calculation. `LedgerEngine.get_account_balance()` and `LedgerReportEngine` both implement similar logic. Consolidation deferred to avoid coupling report hash calculation to transaction engine.

### Transaction ↔ Journal Entries

**Boundary**: One-to-many foreign key with cascade restrictions

**Justification**: Transaction is atomic unit; entries are implementation detail. Prevents:

- Orphaned journal entries (FK constraint blocks)
- Deleting transaction without deleting entries (ON DELETE RESTRICT)
- Updating transaction ID after entries reference it (ON UPDATE CASCADE)

**Consequence**: Must query both tables to get complete transaction. No single-table view of transaction with entries. Performance impact is minimal due to indexed FK.

### Posting Date ↔ Transaction Date

**Boundary**: Two separate datetime columns in transactions table

**Justification**: IFRS compliance. Economic event date (transaction_date) is when business activity occurred. Accounting posting date (posting_date) is when ledger recognized it. Gap between dates is normal and expected.

**Example**: Sale occurs December 31, 2025 (transaction_date). Accountant posts entry January 5, 2026 (posting_date). Financial statements use transaction_date for period classification.

**Consequence**: Reports must specify which date to use. Trial balance uses posting_date by default (when was it in the ledger?). Income statement uses transaction_date (when did revenue occur?).

## Main Flows

### Post Transaction

```
1. Client constructs TransactionInput with entries list
2. Client calls ledger.post_transaction(input, created_by, source_system)
3. Engine validates input:
   - All entries have account_code, entry_type, amount
   - Amount >= 0
   - Sum(debits) == Sum(credits)
4. Engine opens database session
5. For each entry:
   - Verify account exists in chart_of_accounts
   - Fail entire transaction if any account missing
6. Generate transaction_id (UUID), transaction_number (sequential)
7. Calculate transaction_hash from ID, date, and ordered entries
8. Insert transaction record with status = POSTED
9. For each entry:
   - Generate entry_id (UUID)
   - Calculate entry_hash
   - Insert journal_entry record
10. Insert audit_log record with event metadata
11. Commit database transaction
12. Return transaction_id to client

Failure at any step: rollback entire transaction, no audit entry created
```

**Critical decision**: Transaction goes directly to POSTED status. PENDING status exists in enum but is never used. This means:

- No two-phase commit (post now, approve later)
- No queue for failed posts
- Caller must handle all errors immediately

**Alternative considered**: PENDING → approval workflow → POSTED. Rejected because it adds complexity for uncertain benefit. Current users (CLI admin) are trusted to post correctly. Future API integration may need PENDING status for external systems.

### Reverse Transaction

```
1. Client provides transaction_id and reversal_reason
2. Engine queries original transaction
3. Validate:
   - Transaction exists
   - Status is POSTED (cannot reverse PENDING, REVERSED, or CANCELLED)
   - Not already reversed (reversed_by_transaction_id is NULL)
4. Query all journal entries for original transaction
5. For each original entry:
   - Create reversal entry with inverted type (DEBIT ↔ CREDIT)
   - Same account, same amount, memo indicates reversal
6. Construct new TransactionInput for reversal entries
7. Post reversal transaction via standard post_transaction() flow
8. Update original transaction:
   - Set status = REVERSED
   - Set reversed_by_transaction_id = new transaction ID
9. Update reversal transaction:
   - Set is_reversal = TRUE
   - Set reverses_transaction_id = original transaction ID
   - Set reversal_reason
10. Log audit event with severity WARNING
11. Commit
12. Return reversal transaction_id

Failure: rollback, original transaction unchanged
```

**Why WARNING severity?** Reversals are always exceptional. Even legitimate corrections require audit attention to verify reason and authorization.

**Limitation**: No approval workflow. Any user who can reverse any transaction of any amount. `CORRECTION_APPROVAL_THRESHOLD` exists in .env but is not enforced. Production deployment requires external approval gate before calling `reverse_transaction()`.

### Calculate Account Balance

```
1. Client provides account_code and optional as_of_date
2. Engine queries chart_of_accounts to verify account exists and get type
3. Build query:
   - Join journal_entries with transactions
   - Filter: account_code match AND transaction status = POSTED
   - If as_of_date provided: filter posting_date <= as_of_date
4. Execute query, retrieve all matching entries
5. Sum debits and credits separately
6. Calculate balance based on account type:
   - ASSET or EXPENSE: balance = debits - credits
   - LIABILITY, EQUITY, or REVENUE: balance = credits - debits
7. Return Decimal balance

No caching, no optimization
```

**Performance issue**: Trial balance calls this method once per active account. With 500 accounts and 10,000 total transactions, this executes 500 queries each scanning all 10,000 transactions. Database view `v_account_balances` solves this with single query but is not used by Python code.

**Why not always use the view?** Python logic is explicit and testable. View SQL is implicit and harder to test in isolation. Trade-off favors code clarity over performance in current phase. Production optimization path is clear.

### Generate Report

```
1. Client calls report method (trial_balance, balance_sheet, etc.) with parameters
2. Engine generates report_id (UUID)
3. Execute queries to gather data
4. Format results into structured dictionary
5. Calculate report_hash from JSON serialization of full results
6. Log audit event with report metadata
7. Commit audit log
8. Return report dictionary with metadata

Reports are never stored — only metadata is logged
```

**Reproducibility**: Same parameters on same data produce same hash. This allows:

- Future verification: regenerate report with same parameters, compare hashes
- Integrity proof: hash proves report was generated from unmodified data
- Audit trail: report metadata shows who generated what, when

**Limitation**: If underlying transactions are modified (database corruption), regenerated report will produce different hash. System does not detect this automatically — auditor must trigger verification.

## Failure Behavior

### Transaction Post Failure

**What fails**: Database commit during `post_transaction()`

**Trigger**: Connection loss, constraint violation, disk full, concurrent transaction conflict

**System behavior**: 
- SQLAlchemy raises exception
- `except` block calls `session.rollback()`
- All database changes are reverted (transaction, entries, audit log)
- Exception propagates to caller with error message
- No partial transaction exists in database

**User impact**: Transaction is lost. Client must retry entire operation.

**Recovery**: None required. System state is unchanged. Client constructs new TransactionInput and retries.

### Reversal Failure

**What fails**: Original transaction does not exist, or already reversed, or status is not POSTED

**Trigger**: Client error (wrong transaction ID), concurrent reversal by another user, attempting to reverse PENDING transaction

**System behavior**:
- Validation check fails before any database operation
- ValueError raised with specific message
- No database session opened, no rollback needed
- No audit entry created

**User impact**: Reversal not created. Error message indicates specific reason.

**Recovery**: Verify transaction ID and status. If transaction was already reversed, check `reversed_by_transaction_id` to find reversal.

### Hash Corruption

**What fails**: Recalculated hash does not match stored hash

**Trigger**: Direct database UPDATE bypassing triggers (requires DBA access), storage bit flip, software bug in hash calculation

**System behavior**:
- No automatic detection
- Manual verification via `verify_report_integrity()` or recalculating transaction hash
- Method returns mismatch indication but does not modify database

**User impact**: Report integrity cannot be verified. Historical audit trail is compromised.

**Recovery**:
1. Identify affected transaction via hash recalculation script
2. Compare stored hash with recalculated hash
3. If data is unchanged but hash differs: software bug, regenerate correct hash
4. If data was modified: database corruption, requires investigation and potential restoration from backup
5. Log incident in audit trail manually with CRITICAL severity
6. Notify compliance team

**Prevention**: Periodic scheduled job to verify hashes on all transactions. Not implemented in current version.

### Database Connection Loss During Transaction

**What fails**: Network interruption or database restart while transaction is in progress

**Trigger**: Infrastructure failure, planned database maintenance, connection pool exhausted

**System behavior**:
- SQLAlchemy raises OperationalError or DisconnectionError
- Transaction is automatically rolled back by database (not yet committed)
- `pool_pre_ping=True` prevents using dead connections for new transactions
- Session is disposed, exception propagates

**User impact**: Transaction fails, must retry. No partial data in database.

**Recovery**: Client waits for database availability and retries. No manual intervention needed.

### Trial Balance Query Timeout

**What fails**: Trial balance generation exceeds database query timeout (default 30 seconds)

**Trigger**: Large number of accounts (500+), high transaction volume, slow disk I/O

**System behavior**:
- Database kills query after timeout
- SQLAlchemy raises TimeoutError
- No partial result returned
- No database state change (read-only operation)

**User impact**: Report not generated. User must retry or use alternative method (SQL view direct query).

**Recovery**: 
- Short term: increase `DB_QUERY_TIMEOUT` in .env
- Long term: modify report engine to use `v_trial_balance` view (single query instead of N queries)
- Immediate workaround: query view directly via SQL console

## Trade-Offs Consciously Assumed

### Immutability vs. Storage Cost

**Decision**: Never delete posted transactions, even after retention period expires

**What was gained**: Absolute data integrity. Audit trail cannot be tampered with. Hash verification remains valid indefinitely.

**What was sacrificed**: Storage grows without bound. Database will eventually require archiving strategy even if not legally required.

**When this becomes a problem**: After several years of operation, database size may impact backup duration and restore time. Mitigation requires implementing cold storage archive (export old data to compressed JSON files with hash preservation, keep metadata in main database for reference).

**Reversibility**: Low. Moving to mutable architecture would require complete redesign of audit system and compliance validation.

### Performance vs. Code Clarity

**Decision**: Trial balance executes one query per account instead of using optimized SQL view

**What was gained**: Python code is explicit, testable, and easy to modify. Balance calculation logic is visible in one place. No hidden SQL view behavior.

**What was sacrificed**: Performance with high account counts. View would execute in <1 second versus current several seconds for 500+ accounts.

**When this becomes a problem**: Production deployment with hundreds of accounts and frequent trial balance generation. Users will notice delay.

**Reversibility**: High. Switching to view requires only modifying `get_trial_balance()` to execute raw SQL instead of calling `get_account_balance()` in loop. View already exists in schema.

### Single Instance vs. Horizontal Scaling

**Decision**: Transaction numbering uses count-then-increment, which has race condition with multiple instances

**What was gained**: Simple implementation. No external dependencies (Redis, database sequences). Transaction numbers are readable (YYYYMMDD-NNNNNN).

**What was sacrificed**: Cannot run multiple application instances without collision risk. Limits scalability and prevents zero-downtime deployments.

**When this becomes a problem**: High transaction volume requiring parallel processing, or deployment strategy requiring rolling updates.

**Reversibility**: Medium. Requires replacing transaction number generation with database sequence (MySQL AUTO_INCREMENT) or distributed ID generator. Existing transaction numbers are immutable and cannot be changed, so new system must continue sequence from current maximum.

### Validation in Application vs. Database

**Decision**: Double-entry balance validation happens in Python before database insert, not via database constraint

**What was gained**: Clear error messages. Validation logic is testable in Python. Can validate complex conditions not expressible in SQL CHECK constraint.

**What was sacrificed**: Database can be corrupted if transactions are inserted bypassing Python layer (direct SQL INSERT). No database-level enforcement of debits = credits.

**When this becomes a problem**: If external system gets direct database access, or migration scripts insert transactions without using engine.

**Reversibility**: Low. Adding CHECK constraint for balance would require complex SQL (sum debits across multiple rows equals sum credits) which MySQL does not support. Would need database trigger performing full validation, adding latency to every insert.

### No Authentication in Engine vs. Security

**Decision**: Engine accepts `created_by` as string parameter without validation

**What was gained**: Engine is decoupled from authentication mechanism. Same code works with CLI (no auth), API (OAuth), and batch jobs (service accounts).

**What was sacrificed**: No built-in security. Any code importing engine can perform any operation impersonating any user.

**When this becomes a problem**: As soon as multiple users have access, or when system is exposed via network API.

**Reversibility**: High. Authentication must be added in calling layer (API middleware, CLI wrapper), not in engine. Engine continues to accept `created_by` but calling layer validates token and provides verified user ID.

### Reporting Engine Separate vs. Integrated

**Decision**: Reports use separate `LedgerReportEngine` class instead of methods on `LedgerEngine`

**What was gained**: Clear separation of read and write operations. Reports can be routed to replica database. Different security policies for viewing vs. posting.

**What was sacrificed**: Duplicate balance calculation logic. Increased complexity for users (must instantiate two engines).

**When this becomes a problem**: Code maintenance burden increases when balance logic changes. High-volume deployments want read replica for reports but must coordinate session factories.

**Reversibility**: Medium. Consolidating into single engine requires merging two classes and reconciling different hash calculation approaches (transactions vs. reports).

## Known Limits and Risks

### Transaction Volume Ceiling

Current architecture supports 999,999 transactions per day before numbering format overflows. At 1 million transactions per day:

- Transaction number format YYYYMMDD-NNNNNN cannot represent sequence > 999,999
- System will raise exception on transaction 1,000,000 in single day
- No automatic rollover or format extension

**Mitigation**: Change numbering format to YYYYMMDD-NNNNNNN (7 digits) before reaching limit. Requires database migration to widen transaction_number column.

**Probability**: Low for current deployment (commercial/industrial sector in Angola). High-frequency trading or payment processing would hit this limit.

### Hash Algorithm Obsolescence

SHA-256 is currently considered cryptographically secure, but may be deprecated in future:

- All transaction and report hashes use SHA-256
- Changing algorithm requires recalculating all historical hashes
- Historical reports reference old hashes and cannot be verified with new algorithm

**Mitigation**: Store algorithm identifier with each hash. Planned format: `sha256:abc123...` instead of `abc123...`. When algorithm changes, new transactions use new format, old transactions remain verifiable with old algorithm.

**Probability**: Medium-low over 10-year horizon. SHA-256 replacement (SHA-3, post-quantum) would be gradual industry transition with advance notice.

### MySQL Trigger Dependency

Immutability enforcement depends on database triggers:

- Triggers are MySQL-specific syntax
- Migration to PostgreSQL requires rewriting triggers in PL/pgSQL
- SQLite does not support triggers with same behavior
- If triggers are disabled or removed, immutability is not enforced

**Mitigation**: Test suite should verify triggers exist and function correctly. Include trigger validation in periodic integrity checks.

**Probability**: Low for production (no one disables triggers accidentally). High for development (developers may use SQLite without realizing immutability is not enforced).

### Audit Log Unbounded Growth

Audit log is append-only with no archiving mechanism:

- Every transaction creates minimum 1 audit entry
- Every account creation creates 1 audit entry
- Every report generation creates 1 audit entry
- After years of operation, table will contain millions of rows

**Impact**: Query performance degrades, backup time increases, database size grows

**Mitigation**: Partition audit_log table by date. Archive old partitions to separate storage. Current schema does not implement partitioning.

**Probability**: High over multi-year deployment. Will require action within 2-3 years of production operation.

### Single Point of Failure

No replication or failover:

- Application runs single instance (race condition limitation)
- Database is single server (no replica reads)
- Connection loss stops all operations immediately
- Hardware failure requires restoration from backup (24 hour RPO)

**Mitigation**: Implement database replication for reads (reports, balance queries). Keep writes on single primary to avoid numbering conflicts. Set up DR site with manual failover process.

**Probability**: High that production deployment will require better availability than current architecture provides.

---

**Review Criteria for This Architecture**

This architecture should be reconsidered when:

1. Transaction volume approaches 100,000 per day (requires optimization of trial balance and potential partitioning)
2. Availability requirements exceed 99% (requires replication and load balancing)
3. Multiple concurrent systems need to post transactions (requires distributed ID generation)
4. Regulatory requirements mandate real-time hash verification (requires scheduled validation job)
5. Storage costs become prohibitive (requires archiving strategy for old transactions)

**Document Version**: 1.0  
**Last Updated**: February 2026  
**Authors**: Financial Systems Architecture Team  
**Review Cycle**: Quarterly or after significant production incidents
