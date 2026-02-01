# Architecture Decision Records

This document captures significant architectural decisions made during system design and evolution. Each decision is recorded with context, alternatives considered, and consequences.

## Index

- [DEC-001](#dec-001--immutability-enforced-via-database-triggers) — Immutability Enforced via Database Triggers
- [DEC-002](#dec-002--double-entry-validation-in-application-layer) — Double-Entry Validation in Application Layer
- [DEC-003](#dec-003--sha-256-for-transaction-integrity) — SHA-256 for Transaction Integrity
- [DEC-004](#dec-004--sequential-transaction-numbering) — Sequential Transaction Numbering
- [DEC-005](#dec-005--no-pending-state-for-transactions) — No PENDING State for Transactions
- [DEC-006](#dec-006--separate-report-engine-class) — Separate Report Engine Class
- [DEC-007](#dec-007--sqlalchemy-orm-over-raw-sql) — SQLAlchemy ORM Over Raw SQL
- [DEC-008](#dec-008--audit-log-excludes-failed-operations) — Audit Log Excludes Failed Operations
- [DEC-009](#dec-009--no-authentication-in-engine-layer) — No Authentication in Engine Layer
- [DEC-010](#dec-010--single-currency-implementation) — Single Currency Implementation

---

## DEC-001 — Immutability Enforced via Database Triggers

**Status**: Accepted  
**Date**: 2025-12  
**Deciders**: Architecture team, Compliance

### Context

Financial ledger data must be immutable once posted to satisfy audit requirements and prevent silent data tampering. Multiple approaches exist to enforce immutability: application-level controls, database permissions, or database triggers.

Constraints:
- System has legal value for official reporting and external audit
- Multiple client applications may access database (CLI, future API, batch jobs)
- Developers with database access should not be able to modify posted data even with direct SQL
- IFRS compliance requires immutable audit trail

Risk being reduced: Unauthorized modification of posted financial data, either malicious or accidental, that would invalidate audit trail and legal standing of reports.

### Options Considered

**Option A — Application-Level Enforcement Only**

Provide no update/delete methods in Python engine. Rely on developers using the provided API correctly.

Advantages:
- Simple implementation
- No database-specific code
- Easy to test

Disadvantages:
- Does not prevent direct SQL access bypassing application
- Migration scripts could accidentally modify data
- No protection against developer error or malicious intent

**Option B — Database Role Permissions**

Create read-only database role for application. Separate administrative role can modify data.

Advantages:
- Standard database security pattern
- Works across database platforms
- Clear separation of concerns

Disadvantages:
- Application cannot update transaction status (PENDING → POSTED, POSTED → REVERSED)
- Requires administrative intervention for legitimate status changes
- Complex permission management for reversals

**Option C — Database Triggers**

Create BEFORE UPDATE and BEFORE DELETE triggers that block modifications to transactions with status = 'POSTED'.

Advantages:
- Protects against direct SQL access
- Allows legitimate status transitions (PENDING → POSTED)
- Clear error messages on violation
- Works even if application is bypassed

Disadvantages:
- Database-specific syntax (MySQL triggers differ from PostgreSQL)
- Adds complexity to schema
- Trigger bugs could block legitimate operations

### Decision

Implement database triggers to block UPDATE and DELETE on posted transactions.

Trigger logic:
```sql
IF OLD.status = 'POSTED' THEN
  SIGNAL SQLSTATE '45000'
  SET MESSAGE_TEXT = 'Cannot modify posted transaction';
END IF;
```

Combines with application-level controls: engine provides no methods to update posted data, AND database enforces even if application is bypassed.

### Consequences

**What improves**:
- Immutability is guaranteed at infrastructure level
- Audit confidence is higher (external auditors can verify trigger existence)
- Developer errors cannot corrupt posted data
- Migration scripts are safe (trigger prevents accidental updates)

**What worsens**:
- Schema migration complexity: triggers must be recreated on different database platforms
- Testing requires MySQL (SQLite triggers behave differently, may not catch same violations)
- Debugging is harder if trigger fires unexpectedly (error message must be clear)

**What becomes harder in the future**:
- Migrating to PostgreSQL requires rewriting triggers in PL/pgSQL
- If business rules change to allow certain posted transaction updates, trigger logic must be modified
- Trigger-based enforcement is all-or-nothing (cannot have different rules for different users)

### Review Criteria

This decision should be reconsidered if:
- Regulatory requirements change to allow modification of posted transactions under specific conditions
- Database migration to platform without trigger support becomes necessary
- Application architecture evolves to have single trusted backend that can enforce immutability (eliminating need for defense-in-depth via triggers)

---

## DEC-002 — Double-Entry Validation in Application Layer

**Status**: Accepted  
**Date**: 2025-12  
**Deciders**: Architecture team

### Context

Double-entry accounting requires that total debits equal total credits in every transaction. This rule must be enforced somewhere in the system. Options are: database constraint, application validation before insert, or post-insert verification.

Constraints:
- Validation must occur before data reaches database (catch errors early)
- Error messages must be clear for developers and users
- Performance impact must be minimal (validation on every transaction post)

Risk being reduced: Posting unbalanced transactions that violate accounting principles and produce incorrect financial reports.

### Options Considered

**Option A — Database CHECK Constraint**

Create constraint requiring SUM(debits) = SUM(credits) at database level.

Advantages:
- Enforced regardless of application code
- Cannot be bypassed
- Standard SQL feature

Disadvantages:
- MySQL CHECK constraints cannot sum across multiple rows (journal entries)
- Would require complex trigger comparing sums after each insert
- Error messages are generic database errors, not user-friendly
- Cannot validate before starting database transaction

**Option B — Application Validation Before Insert**

Validate balance in Python before any database operation.

Advantages:
- Clear error messages with specific amounts
- Validation happens before database transaction starts
- Can return detailed breakdown of debits vs credits
- Easy to test in isolation

Disadvantages:
- Can be bypassed if transactions inserted via direct SQL
- No database-level protection
- Relies on all client applications implementing same validation

**Option C — Post-Insert Verification**

Allow inserts without validation, then run verification job to detect imbalances.

Advantages:
- No performance impact on transaction posting
- Can batch verification across many transactions
- Allows correction workflows for detected issues

Disadvantages:
- Invalid data enters database
- Discovering imbalance after the fact requires complex correction
- Audit trail shows invalid transaction existed
- Violates "fail fast" principle

### Decision

Implement validation in application layer via `TransactionInput.validate()` method before database interaction.

Validation logic:
```python
total_debits = sum(e.amount for e in entries if e.entry_type == DEBIT)
total_credits = sum(e.amount for e in entries if e.entry_type == CREDIT)
if total_debits != total_credits:
    raise ValueError(f"Transaction not balanced: Debits={total_debits}, Credits={total_credits}")
```

Called before opening database session. Transaction is rejected completely if unbalanced.

Supplement with periodic verification via `verify_double_entry_integrity()` to detect database corruption.

### Consequences

**What improves**:
- Fast feedback to users (error before database interaction)
- Clear error messages showing exact imbalance
- Testable validation logic independent of database

**What worsens**:
- Direct SQL inserts bypass validation (requires process discipline)
- Must trust all client applications to call validate()
- Periodic verification is manual, not automatic

**What becomes harder in the future**:
- Adding complex validation rules (multi-currency balancing, rounding tolerances) increases validate() complexity
- If validation becomes expensive, may need to move to background job
- Different validation rules for different transaction types requires conditional logic

### Review Criteria

This decision should be reconsidered if:
- Direct database access becomes common pattern (need database-level enforcement)
- Validation performance becomes bottleneck (need async validation)
- Business rules require validation that cannot be expressed in Python (need database triggers)
- Regulatory requirements mandate specific validation timing (before vs. after insert)

---

## DEC-003 — SHA-256 for Transaction Integrity

**Status**: Accepted  
**Date**: 2025-12  
**Deciders**: Architecture team, Security

### Context

System requires cryptographic verification that transaction data has not been modified. Hash algorithm must be chosen for integrity verification. Must balance security strength, performance, and long-term viability.

Constraints:
- Hash calculated on every transaction post (performance matters)
- Hash must remain valid for 7+ years (algorithm longevity required)
- External auditors must be able to verify hashes (standard algorithm required)
- Storage overhead should be reasonable (hash length matters)

Risk being reduced: Undetected modification of transaction data, either through database corruption or malicious tampering.

### Options Considered

**Option A — MD5**

128-bit hash, fast computation.

Advantages:
- Fastest hash algorithm
- Smallest storage (32 hex characters)
- Widely supported

Disadvantages:
- Cryptographically broken (collision attacks exist)
- Not acceptable for audit or compliance
- Provides no tamper evidence

**Option B — SHA-256**

256-bit hash from SHA-2 family.

Advantages:
- Cryptographically secure (no known practical attacks)
- Industry standard for financial systems
- Accepted by auditors and regulators
- Well-supported in Python (hashlib standard library)

Disadvantages:
- 64 hex characters storage per hash
- Slower than MD5 (though still fast for transaction-sized data)
- May be deprecated in distant future (SHA-3 or post-quantum)

**Option C — SHA-3**

Newest SHA family, different internal structure from SHA-2.

Advantages:
- Most future-proof
- Different construction (Keccak) provides algorithm diversity
- Similar security to SHA-256

Disadvantages:
- Less widely adopted in existing financial systems
- Not universally supported in older audit tools
- No significant security advantage over SHA-256 for current threats

### Decision

Use SHA-256 for all transaction and report hashes.

Implementation:
```python
hash_input = json.dumps({
    'transaction_id': txn_id,
    'transaction_date': date.isoformat(),
    'entries': [{'account': e.account_code, 'type': e.entry_type.value, 'amount': str(e.amount)} for e in entries]
}, sort_keys=True)
return hashlib.sha256(hash_input.encode()).hexdigest()
```

Store as VARCHAR(64) in database. Format: hexadecimal string (no algorithm prefix in current version).

### Consequences

**What improves**:
- Transaction integrity is cryptographically verifiable
- Audit confidence is high (industry-standard algorithm)
- External verification tools can validate hashes
- Hash collision probability is negligible

**What worsens**:
- Storage overhead: 64 bytes per transaction + 64 bytes per journal entry
- Computation overhead: ~1ms per transaction on modern CPU
- Algorithm is embedded in data (no identifier stored, future migration requires metadata update)

**What becomes harder in the future**:
- Migrating to SHA-3 or post-quantum algorithm requires recalculating all historical hashes
- Verifying old reports with new algorithm requires maintaining two hash functions
- If SHA-256 is deprecated, entire audit trail must be rehashed

### Review Criteria

This decision should be reconsidered when:
- NIST or equivalent authority deprecates SHA-256 for financial systems
- Post-quantum computing makes SHA-256 vulnerable to practical attacks
- Regulatory requirements mandate specific hash algorithm
- Performance profiling shows hashing is bottleneck (unlikely with current transaction volumes)

**Migration Plan** (when needed):
1. Add hash_algorithm column to transactions and journal_entries tables
2. New transactions store "sha256:" or "sha3:" prefix with hash
3. Verification function checks algorithm and uses appropriate hash function
4. Historical data retains SHA-256, remains verifiable
5. Gradual transition without requiring rehash of old data

---

## DEC-004 — Sequential Transaction Numbering

**Status**: Accepted (with known limitation)  
**Date**: 2025-12  
**Deciders**: Architecture team

### Context

Transactions need human-readable identifier separate from UUID (which is cryptographically random). Number must be unique, ordered, and ideally convey information about transaction timing.

Constraints:
- Must be unique across all transactions
- Should be sortable chronologically
- Must be deterministic (no external dependencies)
- Should be readable by accountants reviewing ledger

Risk being reduced: Transaction identification confusion, difficulty tracking transaction sequence, audit trail gaps.

### Options Considered

**Option A — UUID Only**

Use transaction_id UUID as sole identifier.

Advantages:
- Guaranteed unique
- No race conditions
- Supports distributed systems
- No coordination needed

Disadvantages:
- Not human-readable (e.g., "3f2e9a71-c4d8-4b2a-9f1e-8d7c6b5a4e3d")
- Not sortable by time
- No information conveyed by looking at number

**Option B — Sequential with Database AUTO_INCREMENT**

Use MySQL AUTO_INCREMENT or PostgreSQL SEQUENCE.

Advantages:
- Database guarantees uniqueness
- No race condition
- Simple implementation
- Sortable by time (mostly)

Disadvantages:
- Database-specific feature
- Number reveals total transaction count (security concern in some contexts)
- Gaps in sequence on rollback (acceptable but confusing to users)

**Option C — Date-Based Sequential (YYYYMMDD-NNNNNN)**

Generate number from date + daily sequence counter.

Advantages:
- Human-readable (instantly shows transaction date)
- Sortable within each day
- Supports 999,999 transactions per day
- Business-friendly format

Disadvantages:
- Race condition with multiple instances (count-then-increment)
- Requires locking or coordination for concurrent access
- Cannot run multiple application instances

### Decision

Implement date-based sequential numbering: YYYYMMDD-NNNNNN.

Generation logic:
```python
today = datetime.now(timezone.utc).strftime('%Y%m%d')
count = session.execute("SELECT COUNT(*) FROM transactions WHERE transaction_number LIKE :pattern", {'pattern': f"{today}-%"}).scalar()
seq = count + 1 if count else 1
return f"{today}-{seq:06d}"
```

Accept limitation: single instance only. Future horizontal scaling requires migration to different numbering scheme.

### Consequences

**What improves**:
- Transaction numbers are meaningful (20260201-000042 = 42nd transaction on Feb 1, 2026)
- Sorting by number approximates chronological order
- Accountants can reference transactions verbally ("the oh-oh-oh-oh-four-two transaction")
- Daily sequence resets make numbers shorter and more manageable

**What worsens**:
- Cannot run multiple application instances simultaneously without collision risk
- Zero-downtime deployment is not possible (old instance must stop before new instance starts)
- Race condition if two threads post at exact same moment (mitigated by database uniqueness constraint causing one to fail and retry)

**What becomes harder in the future**:
- Horizontal scaling requires replacing numbering logic
- High-frequency scenarios (1000+ transactions per second) will hit race condition frequently
- Distributed deployment across multiple data centers is not feasible

### Review Criteria

This decision should be reconsidered when:
- Transaction volume approaches 1,000 per day (race condition becomes frequent)
- High availability requirements demand multiple active instances
- Zero-downtime deployment becomes operational requirement
- System must support multi-region active-active deployment

**Migration Path** (when needed):
Replace with database sequence or distributed ID generator (Snowflake, ULID). Existing transaction numbers remain immutable. New numbering starts from configurable base or switches to completely different format with different column.

---

## DEC-005 — No PENDING State for Transactions

**Status**: Accepted (may revisit for API integration)  
**Date**: 2025-12  
**Deciders**: Architecture team

### Context

Transactions can have different lifecycle states: draft/pending (created but not finalized), posted (in ledger), reversed (corrected), cancelled (discarded). System must decide which states to implement and what transitions are allowed.

Constraints:
- Current users are trusted administrators (CLI access)
- External system integration planned for future
- IFRS requires clear distinction between posted and non-posted transactions

Risk being reduced: Posting invalid transactions, difficulty recovering from errors, unclear transaction lifecycle.

### Options Considered

**Option A — PENDING → POSTED Two-Phase Model**

Create transaction in PENDING state, then explicitly post to POSTED.

Advantages:
- Allows validation before posting
- Supports approval workflows
- Can queue transactions for batch processing
- Failed posts don't create invalid entries

Disadvantages:
- More complex API (create separate from post)
- PENDING transactions need separate handling in reports (exclude or include?)
- Retry logic must handle both states

**Option B — Direct POSTED (Current Implementation)**

Create transaction directly in POSTED state with single atomic operation.

Advantages:
- Simplest implementation
- No ambiguous state
- Reports are simple (query POSTED only)
- Clear error handling (success or complete failure)

Disadvantages:
- No approval workflow support
- Cannot queue transactions for later posting
- External systems must validate before calling API
- Retry must recreate entire transaction

**Option C — DRAFT → PENDING → POSTED Three-Phase**

Support drafts, pending review, and posted as separate states.

Advantages:
- Maximum flexibility
- Supports complex workflows
- Clear audit trail of approvals

Disadvantages:
- Complex state machine
- Reports must handle multiple states
- More code to maintain

### Decision

Implement direct POSTED model. Skip PENDING state entirely in current version.

Transaction creation logic:
```python
transaction = Transaction(
    transaction_id=transaction_id,
    # ...
    status=TransactionStatus.POSTED.value,  # Direct to POSTED
    # ...
)
```

Validation occurs in `TransactionInput.validate()` before database interaction. If validation fails, no database record is created.

Reserve PENDING for future use when external systems integration requires queuing or approval.

### Consequences

**What improves**:
- Code simplicity (one state to handle)
- Clear semantics (transaction exists = transaction is posted)
- Reports are straightforward (all transactions are valid)
- Testing is simpler (no state transitions to test)

**What worsens**:
- No support for approval workflows
- External systems must implement own validation before calling API
- Cannot implement "post later" or batch posting
- Failed posts leave no trace (no PENDING record to investigate)

**What becomes harder in the future**:
- Adding approval workflow requires schema migration and code changes
- External integration patterns that depend on PENDING state need workaround
- Batch import scenarios require building queue externally

### Review Criteria

This decision should be reconsidered when:
- External system integration requires queuing transactions for review
- Compliance requirements mandate approval workflow before posting
- High-volume batch imports need staging area before validation
- Error recovery patterns benefit from preserving failed attempts as PENDING

**Extension Path** (when needed):
1. Add support for PENDING state in enum (already exists, not used)
2. Modify post_transaction() to accept optional `immediate_post=False` parameter
3. Add separate `finalize_transaction(transaction_id)` method to move PENDING → POSTED
4. Update reports to filter `WHERE status = 'POSTED'` consistently
5. Existing transactions unaffected (all are POSTED)

---

## DEC-006 — Separate Report Engine Class

**Status**: Accepted  
**Date**: 2025-12  
**Deciders**: Architecture team

### Context

System needs to generate reports (trial balance, balance sheet, income statement) from ledger data. Reports can be implemented as methods on main LedgerEngine class or as separate engine. Decision affects code organization and scalability.

Constraints:
- Reports are read-heavy operations (no writes)
- Report generation may need to scale independently from transaction posting
- Different security policies may apply to reading vs. writing

Risk being reduced: Code coupling, inability to scale read operations independently, security boundary violations.

### Options Considered

**Option A — Methods on LedgerEngine**

Add report methods to existing LedgerEngine class.

Advantages:
- Single class for all operations
- Shared session management
- Users instantiate one object
- No code duplication

Disadvantages:
- Class becomes large (20+ methods)
- Cannot scale reads independently
- Security policies apply to entire class
- Mixing read and write concerns

**Option B — Separate LedgerReportEngine Class**

Create distinct class for report operations.

Advantages:
- Clear separation of read and write
- Can route to replica database
- Different security policies possible
- Independent scaling

Disadvantages:
- Users must instantiate two classes
- Some code duplication (balance calculation)
- More complex for simple use cases

**Option C — Report Methods as Module Functions**

Pure functions taking database URI as parameter.

Advantages:
- No class state
- Easy to test
- Very explicit dependencies

Disadvantages:
- No shared session management
- Harder to mock in tests
- No place to store report engine state
- Difficult to add features like caching

### Decision

Implement separate `LedgerReportEngine` class.

Usage pattern:
```python
ledger = LedgerEngine()
report_engine = LedgerReportEngine(ledger)  # Shares session factory
```

Report engine can also be instantiated standalone:
```python
report_engine = LedgerReportEngine()  # Creates own LedgerEngine internally
```

### Consequences

**What improves**:
- Clear API separation (writes via LedgerEngine, reads via LedgerReportEngine)
- Future: can route reports to read replica by changing session factory
- Security: can grant report access without write access
- Each class has focused responsibility

**What worsens**:
- Some code duplication (get_account_balance exists in both engines)
- Users must understand two classes
- More imports in client code
- Balance calculation logic is duplicated

**What becomes harder in the future**:
- Consolidating back to single class requires API breaking change
- Keeping balance calculation logic synchronized requires discipline
- Adding cross-cutting features (caching, metrics) must touch both classes

### Review Criteria

This decision should be reconsidered when:
- Code duplication between engines becomes maintenance burden
- Report operations require transaction posting (read/write mixed)
- Users consistently need both engines (separation provides no value)
- Single-class API would significantly simplify client code

**Consolidation Path** (if needed):
Merge LedgerReportEngine methods into LedgerEngine. Mark LedgerReportEngine as deprecated for one release cycle, then remove. Existing code continues to work (LedgerReportEngine instantiates LedgerEngine internally).

---

## DEC-007 — SQLAlchemy ORM Over Raw SQL

**Status**: Accepted (with escape hatch for performance)  
**Date**: 2025-12  
**Deciders**: Architecture team

### Context

Application needs to interact with relational database. Options are: ORM framework (SQLAlchemy), query builder (SQLAlchemy Core without ORM), or raw SQL strings.

Constraints:
- Must support MySQL for production, SQLite for testing
- Schema may evolve (migrations needed)
- Queries range from simple (get account by code) to complex (trial balance joins)
- Performance is important for high-volume operations

Risk being reduced: SQL injection vulnerabilities, database portability issues, difficult testing, query maintenance complexity.

### Options Considered

**Option A — Raw SQL Strings**

Write all queries as SQL strings, use database cursor directly.

Advantages:
- Maximum control over SQL
- Optimal performance
- No ORM learning curve
- Direct execution

Disadvantages:
- SQL injection risk if not careful
- Database-specific SQL (MySQL vs PostgreSQL differences)
- Difficult to mock in tests
- String concatenation for dynamic queries

**Option B — SQLAlchemy ORM**

Use Object-Relational Mapping with model classes.

Advantages:
- Database abstraction (works with MySQL, PostgreSQL, SQLite)
- Type-safe queries (Python objects, not strings)
- Automatic parameterization (SQL injection protection)
- Easy to test (mock sessions)
- Clear relationship modeling

Disadvantages:
- Performance overhead for complex queries
- Learning curve for team
- Some queries are verbose
- May need raw SQL for optimization

**Option C — SQLAlchemy Core (Query Builder)**

Use SQLAlchemy query construction without ORM.

Advantages:
- More control than ORM
- Still database-independent
- Better performance than ORM
- Type-safe construction

Disadvantages:
- More verbose than ORM for simple queries
- Still has learning curve
- No object mapping (work with dictionaries)

### Decision

Use SQLAlchemy ORM for all standard operations. Allow raw SQL for performance-critical queries via `session.execute(text(...))`.

Model definition pattern:
```python
class Transaction(Base):
    __tablename__ = 'transactions'
    transaction_id = Column(String(36), primary_key=True)
    # ...
```

Query pattern:
```python
transaction = session.query(Transaction)\
    .filter(Transaction.transaction_id == id)\
    .first()
```

Performance escape hatch for trial balance (when implemented):
```python
result = session.execute(text("SELECT * FROM v_trial_balance"))
```

### Consequences

**What improves**:
- Code is database-agnostic (can switch MySQL → PostgreSQL with SQL script changes only)
- SQL injection is prevented automatically
- Testing is easier (can mock session)
- Type hints and IDE autocomplete work with model classes
- Queries are readable Python code

**What worsens**:
- Performance overhead: ORM adds 10-20% latency versus raw SQL
- Complex queries (trial balance) generate inefficient SQL (N+1 problem)
- Schema must be defined twice (SQL for database, Python for ORM)
- Some PostgreSQL-specific features are harder to access

**What becomes harder in the future**:
- High-performance operations may need to bypass ORM entirely
- Adding database-specific optimizations requires breaking abstraction
- Query profiling is more complex (must examine generated SQL)

### Review Criteria

This decision should be reconsidered when:
- Performance profiling shows ORM is bottleneck for critical operations
- Team expertise shifts to favor raw SQL over ORM
- Database-specific features become essential and ORM abstraction adds more cost than value

**Current Performance Hotspots**:
- Trial balance generation: ORM executes one query per account (N+1 pattern)
- Solution available: use raw SQL to query pre-built view `v_trial_balance`
- Trade-off: keep ORM for code clarity, use raw SQL for specific slow queries

---

## DEC-008 — Audit Log Excludes Failed Operations

**Status**: Accepted (with known gap)  
**Date**: 2025-12  
**Deciders**: Architecture team

### Context

System maintains audit log of all operations. Failed operations (validation errors, constraint violations, exceptions) currently do not create audit log entries. Decision is whether to log failures or keep audit log success-only.

Constraints:
- Audit log must be immutable (no deletes)
- Database rollback reverses audit entries created within transaction
- Failed operations may be frequent (user errors, validation failures)
- Log volume affects query performance and storage

Risk being reduced: Insufficient audit trail, inability to detect attack patterns, difficulty troubleshooting user issues.

### Options Considered

**Option A — Log Successes Only (Current)**

Audit entry created only after operation succeeds, within same database transaction.

Advantages:
- Audit log contains only valid operations
- No noise from user errors
- Rollback automatically removes invalid audit entry
- Clear semantics (log entry exists = operation succeeded)

Disadvantages:
- Failed attempts are invisible
- Cannot detect repeated failed authorization attempts (security)
- Difficult to troubleshoot "why did this fail?" questions
- No record of what user tried to do

**Option B — Log All Operations Before Execution**

Create audit entry before operation, in separate transaction.

Advantages:
- Complete record of attempts (success and failure)
- Can detect attack patterns (repeated reversal attempts)
- Troubleshooting is easier (can see what user tried)
- Security audit requires failure logs

Disadvantages:
- Audit log contains failed operations (adds complexity to queries)
- Separate transaction means audit entry persists even on rollback
- Higher log volume (potentially 2-10x depending on error rate)
- Must add "outcome" field to audit_log (SUCCESS, FAILED)

**Option C — Log Failures Only for Critical Operations**

Selective logging: log all transaction posts, log only failures for sensitive operations (reversal attempts, account modifications).

Advantages:
- Balanced approach (critical failures visible, noise reduced)
- Security-relevant attempts are logged
- Lower volume than logging everything

Disadvantages:
- Complex logic determining what to log
- Inconsistent audit trail (some failures logged, others not)
- Difficult to explain to auditors

### Decision

Accept current implementation: log successes only. Document as known gap for production hardening.

Current behavior:
```python
try:
    # perform operation
    self._log_audit(session, event_type, severity, ...)
    session.commit()  # Audit entry saved only if operation succeeds
except Exception as e:
    session.rollback()  # Audit entry is rolled back
    raise
```

Recommendation for production: implement Option B or C before exposing to untrusted users.

### Consequences

**What improves**:
- Audit log is clean (only successful operations)
- Query performance is better (smaller table)
- Storage requirements are lower
- Simpler logic (no need for outcome field)

**What worsens**:
- Security gap: cannot detect failed authorization attempts
- Troubleshooting gap: cannot see what user tried to do
- Compliance gap: some audit standards require failure logging
- Attack detection is blind to unsuccessful attempts

**What becomes harder in the future**:
- Adding failure logging requires schema migration (add outcome field)
- Retrofitting to existing code requires touching many try/except blocks
- Decision about what to log must be made consistently across codebase

### Review Criteria

This decision should be reconsidered when:
- System is exposed to external users or untrusted clients
- Security audit identifies requirement to log failed attempts
- Compliance framework mandates failure logging
- Troubleshooting frequently requires "what did user try to do?" information

**Implementation When Needed**:
1. Add `outcome` ENUM('SUCCESS', 'FAILED') to audit_log table
2. Create separate `_log_audit_attempt()` method that commits immediately
3. Call before operation execution, not after
4. Update queries to filter by outcome where needed
5. Implement log retention policy for failed attempts (shorter than successes)

---

## DEC-009 — No Authentication in Engine Layer

**Status**: Accepted (requires wrapper for production)  
**Date**: 2025-12  
**Deciders**: Architecture team

### Context

Engine accepts `created_by` parameter as string but does not validate identity. Decision is whether authentication belongs in engine or in calling layer.

Constraints:
- CLI users are trusted administrators
- Future API integration will have different authentication (OAuth, API keys)
- Batch jobs need service account support
- Testing requires ability to impersonate users

Risk being reduced: Unauthorized access to ledger operations, audit trail falsification, security boundary confusion.

### Options Considered

**Option A — Authenticate in Engine**

Engine validates `created_by` against authentication provider.

Advantages:
- Security enforced at core
- Cannot bypass authentication
- Consistent across all callers

Disadvantages:
- Engine coupled to authentication mechanism
- Different callers need different auth (CLI vs API vs batch)
- Testing becomes harder (need to mock auth)
- Cannot easily switch auth providers

**Option B — Authenticate in Calling Layer (Current)**

Engine accepts any `created_by`, caller is responsible for validation.

Advantages:
- Engine is decoupled from authentication
- Different callers can use different auth
- Testing is simple (pass any user ID)
- Same engine works with CLI, API, batch jobs

Disadvantages:
- No built-in security
- Caller must implement authentication
- Easy to forget to add auth in new caller
- Engine trusts whatever it receives

**Option C — Optional Authentication**

Engine accepts authentication provider as optional parameter.

Advantages:
- Flexibility for different deployment scenarios
- Can enable/disable auth via configuration
- Supports gradual migration

Disadvantages:
- Complex API (optional parameter)
- Unclear when to use authentication
- Testing scenarios multiply (with and without auth)

### Decision

Keep authentication in calling layer. Engine accepts `created_by` as string without validation.

Pattern:
```python
# CLI validates user via OS authentication
user = os.getenv('USER')

# Future API validates token and extracts user
# user = validate_token(request.headers['Authorization'])

# Both call engine with validated user
ledger.post_transaction(input, created_by=user, ...)
```

Document clearly: Engine provides NO security. Callers MUST validate before calling.

### Consequences

**What improves**:
- Engine is reusable across different authentication schemes
- Testing is straightforward (no auth mocking needed)
- Batch jobs can use service accounts without special handling
- Code is simpler (no authentication logic in engine)

**What worsens**:
- Security responsibility is unclear (who validates?)
- Easy to create insecure caller that forgets to authenticate
- Audit trail can be falsified if caller is compromised
- No defense in depth (engine layer provides no protection)

**What becomes harder in the future**:
- Adding authentication retroactively requires changing all callers
- Different callers may implement auth inconsistently
- Cannot enforce company-wide auth policy at engine level

### Review Criteria

This decision should be reconsidered when:
- Multiple caller implementations exist with inconsistent auth
- Security audit requires auth at core layer
- Single trusted backend would simplify auth (microservice architecture)
- Regulatory requirements mandate specific authentication approach

**Production Deployment Requires**:
- API layer with OAuth2 or API key validation
- CLI wrapper that validates OS user or requires login
- Clear documentation of security boundary
- Automated testing that callers perform authentication

---

## DEC-010 — Single Currency Implementation

**Status**: Accepted (extension planned)  
**Date**: 2025-12  
**Deciders**: Architecture team, Product

### Context

System stores `currency` field in journal_entries table but always writes "AOA". Decision is whether to implement full multi-currency support or keep single currency with future extension path.

Constraints:
- Current operations are Angola-only (AOA)
- Schema already has currency field (future-proofing)
- Multi-currency adds complexity (exchange rates, conversion, reporting)
- IFRS requires functional currency designation

Risk being reduced: Premature complexity, delayed initial deployment, code bloat for unused features.

### Options Considered

**Option A — Full Multi-Currency from Start**

Implement exchange rates, conversion, multi-currency balancing.

Advantages:
- Future-proof from beginning
- No migration needed later
- International operations supported

Disadvantages:
- Significant complexity (3-5x code)
- Exchange rate management required
- Conversion logic in reports
- Not needed for current deployment

**Option B — Single Currency, Field Reserved**

Store currency field but validate all entries use same currency.

Advantages:
- Simple implementation
- Database schema ready for future
- Clear migration path
- No unused code

Disadvantages:
- Cannot handle multi-currency immediately
- Requires code changes to add support
- User expectation may be set incorrectly

**Option C — Currency Field, No Validation**

Allow currency field but do not enforce single-currency rule.

Advantages:
- Flexible
- Could mix currencies accidentally
- Easy to extend

Disadvantages:
- Silent failure (mixed currencies not detected)
- Reports would be wrong
- Dangerous ambiguity

### Decision

Implement single currency with reserved field. Engine writes "AOA" to all entries, does not validate input currency.

Current implementation:
```python
journal_entry = JournalEntry(
    # ...
    currency='AOA',  # Hardcoded
    # ...
)
```

Schema supports currency field, ready for future multi-currency support.

Extension requirements (when needed):
1. Exchange rate table with date and currency pair
2. Validation: all entries in transaction must use same currency OR
3. Reference currency field on transaction with conversion rates
4. Report currency selection (functional vs. presentation)

### Consequences

**What improves**:
- Simple implementation (no exchange rate complexity)
- Fast development (feature not needed now)
- Clear scope (Angola operations only)
- Schema is ready for extension

**What worsens**:
- Cannot handle foreign currency transactions
- International expansion requires code changes
- Currency field exists but is not used (may confuse)
- No validation prevents accidental currency mixing (if code changed)

**What becomes harder in the future**:
- Adding multi-currency requires exchange rate table and conversion logic
- Historical transactions are all AOA (cannot change)
- Reports must handle mixed currency periods (before and after feature)
- Must decide functional currency policy for company

### Review Criteria

This decision should be reconsidered when:
- Company begins international operations requiring foreign currency
- Suppliers or customers transact in non-AOA currencies
- Regulatory reporting requires multi-currency presentation
- Volume of foreign currency transactions justifies implementation cost

**Extension Path** (when needed):
1. Create exchange_rates table (currency_pair, rate, effective_date)
2. Modify TransactionInput to accept currency parameter
3. Validate: all entries in transaction have same currency
4. Add conversion logic to reports (display in functional or presentation currency)
5. Historical AOA transactions remain unchanged, new transactions use specified currency

---

**Document Version**: 1.0  
**Last Updated**: February 2026  
**Review Cycle**: After each significant architecture change or quarterly
