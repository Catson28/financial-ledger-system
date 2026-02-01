# Ledger / Accounting Engine

Immutable double-entry accounting system with cryptographic integrity and complete audit trail.

## What This System Does

Records financial transactions for enterprise operations using double-entry accounting principles. Every economic event (sale, payment, provision, reversal) is registered exactly once with SHA-256 cryptographic hashing and immutable audit trail — eliminating the risk of silent data manipulation.

The system enforces immutability at database level via triggers, preventing any deletion or update of posted transactions. Errors are corrected through reversal entries, never by modifying historical data.

## Business Context

- **Target jurisdiction**: Angola (IFRS accounting standards)
- **Default currency**: AOA (Angolan Kwanza)
- **Responsible parties**: Compliance and Internal Audit
- **Legal value**: System produces numbers for official reporting, external audit verification, and regulatory compliance
- **Retention period**: 7 years (configurable, aligned with international financial record retention standards)

## Key Principles

1. **Immutability**: Nothing is deleted or updated once posted
2. **Double-Entry**: Debits always equal credits — enforced before commit
3. **Auditability**: Complete trail from account creation to report generation
4. **Correction by Reversal**: Errors generate offsetting transactions, original data preserved
5. **Cryptographic Integrity**: SHA-256 hash per transaction and per journal entry

## Getting Started

### Prerequisites

- Python 3.10 or higher
- MySQL 8.0+ or MariaDB 10.5+ (production) / SQLite 3.x (development only)
- 2GB RAM minimum
- Linux, macOS, or Windows with WSL

### Quick Setup

1. Clone repository and navigate to project directory

2. Run automated setup:
```bash
python setup.py
```

3. Activate virtual environment:
```bash
# Linux/macOS
source env/bin/activate

# Windows
env\Scripts\activate
```

4. Configure database connection in `.env`:
```bash
LEDGER_DB_URI=mysql+pymysql://user:password@host:3306/ledger_db?charset=utf8mb4
```

5. Initialize database schema:
```bash
python ledger_admin_cli.py init --confirm
```

6. (Optional) Create sample chart of accounts:
```bash
python setup.py  # Re-run to create sample accounts after DB init
```

### First Transaction

Create a simple journal entry file `entries.json`:
```json
[
  {
    "account_code": "1100",
    "entry_type": "DEBIT",
    "amount": "1000.00",
    "memo": "Cash received from sale"
  },
  {
    "account_code": "4100",
    "entry_type": "CREDIT",
    "amount": "1000.00",
    "memo": "Revenue from sale"
  }
]
```

Post the transaction:
```bash
python ledger_admin_cli.py post-transaction \
  --event-type SALE \
  --description "Product sale - Invoice #001" \
  --user your.email@company.com \
  --entries entries.json
```

### Verify Integrity

Check that all transactions balance correctly:
```bash
python ledger_admin_cli.py verify
```

Generate trial balance:
```bash
python ledger_admin_cli.py trial-balance --output report.json
```

## Available Tools

### Administration CLI (`ledger_admin_cli.py`)

Command-line interface for all ledger operations:

- `init` — Initialize database schema
- `create-account` — Add account to chart of accounts
- `post-transaction` — Post new transaction
- `reverse` — Reverse existing transaction
- `balance` — Get account balance
- `trial-balance` — Generate trial balance report
- `verify` — Verify double-entry integrity
- `audit` — View audit trail
- `report` — Generate financial reports (balance sheet, income statement, general ledger)

Run `python ledger_admin_cli.py --help` for full command reference.

### Discovery Tool (`ledger_discovery_tool.py`)

Interactive wizard for defining ledger requirements before implementation. Captures legal context, regulatory constraints, account structure, and business rules through guided questionnaire. Use when setting up ledger for new jurisdiction or business entity.

### Report Engine (`ledger_reporting.py`)

Generates auditable, reproducible reports with SHA-256 integrity hashing:

- Balance Sheet
- Income Statement
- Trial Balance
- General Ledger
- Audit Trail
- Custom integrity reports

All reports include: unique report ID, generation timestamp, user identifier, parameter set, and cryptographic hash for verification.

## Current Limitations

Users must be aware of these constraints in the current version:

1. **Single currency only**: System writes AOA to all entries. Multi-currency support requires additional implementation (exchange rate table, conversion logic, reference currency field).

2. **Trial balance performance**: With 500+ active accounts, trial balance generation executes one query per account and may take several seconds. Production optimization available via pre-built SQL view `v_trial_balance` (not yet integrated into Python engine).

3. **Single instance deployment**: Transaction numbering uses count-then-increment pattern with race condition. Running multiple application instances simultaneously will cause transaction number collisions. Multi-instance support requires sequence-based numbering or distributed ID generation.

4. **No authentication or authorization**: Any code with access to the engine can execute any operation. `created_by` parameter is recorded but not validated. Production deployment requires RBAC layer before exposing operations.

5. **Manual hash verification**: System calculates SHA-256 hashes on creation but does not periodically re-verify existing transactions. Scheduled integrity checks must be implemented separately.

## Documentation

Complete technical documentation is organized as follows:

- **[ARCHITECTURE.md](ARCHITECTURE.md)** — System design decisions, component boundaries, failure behavior, trade-offs
- **[DECISIONS.md](DECISIONS.md)** — Architecture Decision Records with context, alternatives, and consequences
- **[RUNBOOK.md](RUNBOOK.md)** — Operational procedures for incidents and routine maintenance
- **[FAQ.md](FAQ.md)** — Common questions organized by category (setup, execution, failures, monitoring)

Additional documentation:

- **[TESTING.md](TESTING.md)** — Test strategy, current coverage, required scenarios before production
- **[DEPLOYMENT.md](DEPLOYMENT.md)** — Deployment strategy, environment separation, migration procedures
- **[SCALABILITY.md](SCALABILITY.md)** — Current limits, scaling strategies, partitioning considerations
- **[OBSERVABILITY.md](OBSERVABILITY.md)** — Logging strategy, alert definitions, monitoring requirements
- **[GLOSSARY.md](GLOSSARY.md)** — Terms used consistently across all documentation

## Support and Contribution

For operational issues, consult **RUNBOOK.md** first.

For architectural questions or proposed changes, review **ARCHITECTURE.md** and **DECISIONS.md** to understand design rationale before proposing modifications.

All changes to chart of accounts structure or engine behavior require approval from Compliance before deployment to production.

## License

Proprietary. Internal use only.

---

**Version**: 1.0.0  
**Last Updated**: February 2026  
**Maintained By**: Financial Systems Architecture Team
