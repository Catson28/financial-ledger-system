# 🏗️ Arquitetura do Sistema - Ledger / Accounting Engine

## Visão Geral

Este documento descreve a arquitetura técnica do sistema de Ledger / Accounting Engine, um sistema de contabilidade imutável de nível bancário.

---

## Princípios de Design

### 1. Imutabilidade (Immutability)
- **Nenhuma atualização ou exclusão** de registros contábeis
- **Correções por compensação**: Erros são corrigidos através de lançamentos de estorno
- **Histórico completo**: Todas as versões de dados são preservadas

### 2. Dupla Entrada (Double-Entry)
- **Validação automática**: Débitos = Créditos sempre
- **Transações atômicas**: Tudo ou nada
- **Integridade referencial**: Contas válidas obrigatórias

### 3. Auditabilidade
- **Trilha completa**: Todos os eventos registrados
- **Hash de integridade**: SHA-256 para cada transação
- **Metadados completos**: Quem, quando, de onde, por quê

### 4. Separação de Responsabilidades
- **Fato**: Eventos econômicos (Transaction, JournalEntry)
- **Regra**: Lógica de negócio (LedgerEngine)
- **Visão**: Relatórios e consultas (LedgerReportEngine)

---

## Arquitetura em Camadas

```
┌─────────────────────────────────────────────────────────┐
│                   PRESENTATION LAYER                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Admin CLI   │  │  Discovery   │  │   API REST   │  │
│  │              │  │     Tool     │  │   (Future)   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────┐
│                   APPLICATION LAYER                      │
│  ┌──────────────────────────────────────────────────┐  │
│  │           Ledger Report Engine                    │  │
│  │  - Balance Sheet    - Trial Balance               │  │
│  │  - Income Statement - General Ledger              │  │
│  │  - Audit Trail      - Report Integrity            │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │              Ledger Engine (Core)                 │  │
│  │  - Chart of Accounts Management                   │  │
│  │  - Transaction Posting                            │  │
│  │  - Double-Entry Validation                        │  │
│  │  - Reversal Logic                                 │  │
│  │  - Balance Calculation                            │  │
│  │  - Integrity Verification                         │  │
│  │  - Audit Logging                                  │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────┐
│                      DATA LAYER                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │               SQLAlchemy ORM                      │  │
│  │  - Session Management                             │  │
│  │  - Transaction Control                            │  │
│  │  - Query Building                                 │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────┐
│                   DATABASE LAYER                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │         MySQL / MariaDB / PostgreSQL              │  │
│  │  - chart_of_accounts                              │  │
│  │  - transactions                                   │  │
│  │  - journal_entries                                │  │
│  │  - closing_periods                                │  │
│  │  - audit_log                                      │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## Modelo de Dados Detalhado

### Entidades Principais

#### 1. ChartOfAccounts
**Propósito**: Plano de contas hierárquico

**Campos Principais**:
- `account_id` (PK): UUID único
- `account_code` (UNIQUE): Código da conta
- `account_name`: Nome da conta
- `account_type`: ASSET, LIABILITY, EQUITY, REVENUE, EXPENSE
- `parent_account_id` (FK): Referência para hierarquia
- `level`: Nível na hierarquia
- `is_active`: Status ativo/inativo

**Índices**:
- `idx_account_code`
- `idx_account_type`
- `idx_parent_account`

#### 2. Transaction
**Propósito**: Cabeçalho da transação contábil

**Campos Principais**:
- `transaction_id` (PK): UUID único
- `transaction_number` (UNIQUE): Número sequencial
- `transaction_date`: Data do evento econômico
- `posting_date`: Data de lançamento
- `business_event_type`: Tipo de evento (SALE, PAYMENT, etc.)
- `business_key`: Chave de negócio para rastreamento
- `status`: PENDING, POSTED, REVERSED, CANCELLED
- `is_reversal`: Flag de reversão
- `reverses_transaction_id`: FK para transação original
- `transaction_hash`: SHA-256 para integridade

**Campos de Auditoria**:
- `created_at`, `created_by`, `source_system`, `source_ip`

**Índices**:
- `idx_transaction_number`
- `idx_transaction_date`
- `idx_business_key`
- `idx_status`
- `idx_reversal`

#### 3. JournalEntry
**Propósito**: Lançamentos contábeis individuais

**Campos Principais**:
- `entry_id` (PK): UUID único
- `transaction_id` (FK): Referência à transação
- `entry_number`: Número da linha
- `account_id` (FK): Referência à conta
- `account_code`: Código da conta (desnormalizado)
- `entry_type`: DEBIT ou CREDIT
- `amount`: Valor (CHECK > 0)
- `currency`: Código ISO 4217

**Dimensões Analíticas**:
- `cost_center`: Centro de custo
- `business_unit`: Unidade de negócio
- `project_code`: Código do projeto

**Constraint**:
- `check_amount_positive`: Garante valor > 0

**Índices**:
- `idx_transaction_entry`
- `idx_account_code`
- `idx_entry_type`

#### 4. AuditLog
**Propósito**: Trilha completa de auditoria

**Campos Principais**:
- `audit_id` (PK): UUID único
- `event_timestamp`: Timestamp UTC
- `event_type`: Tipo de evento
- `severity`: INFO, WARNING, ERROR, CRITICAL
- `transaction_id`: Referência opcional
- `user_id`: Identificação do usuário
- `source_system`: Sistema de origem
- `action`: Ação executada
- `description`: Descrição detalhada
- `metadata`: JSON com contexto adicional

**Índices**:
- `idx_event_timestamp`
- `idx_transaction_id`
- `idx_user_id`
- `idx_severity`

---

## Fluxos de Processo

### Fluxo 1: Lançamento de Transação

```
1. Request: post_transaction(TransactionInput)
   │
2. ├─> Validate Double-Entry Balance
   │   └─> Σ Debits = Σ Credits?
   │       ├─> NO  → Raise ValueError
   │       └─> YES → Continue
   │
3. ├─> Validate Accounts Exist
   │   └─> For each entry:
   │       └─> Account exists and is active?
   │           ├─> NO  → Raise ValueError
   │           └─> YES → Continue
   │
4. ├─> Generate Transaction Number (Sequential)
   │
5. ├─> Calculate Transaction Hash
   │   └─> SHA-256(number + event + amounts + user)
   │
6. ├─> BEGIN Database Transaction
   │
7. ├─> Insert Transaction Record
   │
8. ├─> Insert Journal Entries (N records)
   │
9. ├─> Log Audit Event
   │
10.└─> COMMIT Database Transaction
   │
11. Return: transaction_id
```

### Fluxo 2: Reversão de Transação

```
1. Request: reverse_transaction(original_id, reason)
   │
2. ├─> Get Original Transaction
   │   └─> Exists and not already reversed?
   │       ├─> NO  → Raise ValueError
   │       └─> YES → Continue
   │
3. ├─> Get Original Entries
   │
4. ├─> Create Reversal Entries
   │   └─> For each entry:
   │       └─> Flip DEBIT ↔ CREDIT
   │
5. ├─> Post Reversal Transaction
   │   └─> (Calls post_transaction with reversed entries)
   │
6. ├─> Update Original Transaction
   │   └─> status = REVERSED
   │   └─> reversed_by_transaction_id = reversal_id
   │
7. ├─> Update Reversal Transaction
   │   └─> is_reversal = TRUE
   │   └─> reverses_transaction_id = original_id
   │
8. ├─> Log Audit Event (WARNING level)
   │
9. └─> Return: reversal_transaction_id
```

### Fluxo 3: Cálculo de Saldo

```
1. Request: get_account_balance(account_code, as_of_date)
   │
2. ├─> Get Account
   │   └─> Determine account_type
   │
3. ├─> Query Journal Entries
   │   └─> Filters:
   │       ├─> account_code = X
   │       ├─> status = POSTED
   │       └─> posting_date <= as_of_date (if provided)
   │
4. ├─> Calculate Totals
   │   ├─> Σ Debits
   │   └─> Σ Credits
   │
5. ├─> Apply Account Type Rule
   │   ├─> ASSET or EXPENSE:
   │   │   └─> Balance = Debits - Credits
   │   └─> LIABILITY, EQUITY, or REVENUE:
   │       └─> Balance = Credits - Debits
   │
6. └─> Return: balance (Decimal)
```

### Fluxo 4: Geração de Relatório

```
1. Request: generate_report(type, params)
   │
2. ├─> Query Data from Database
   │   └─> Based on report type and parameters
   │
3. ├─> Process and Calculate
   │   ├─> Aggregate balances
   │   ├─> Apply business rules
   │   └─> Format output structure
   │
4. ├─> Generate Report ID (UUID)
   │
5. ├─> Calculate Report Hash
   │   └─> SHA-256(entire report data)
   │
6. ├─> Save Report Metadata
   │   └─> Log to audit_log
   │
7. └─> Return: Report Dict with:
       ├─> report_id
       ├─> report_type
       ├─> data
       ├─> metadata
       └─> report_hash
```

---

## Decisões de Design

### Por que MySQL/MariaDB?

1. **Transações ACID**: Crítico para integridade contábil
2. **Maturidade**: Décadas de uso em sistemas financeiros
3. **Performance**: Excelente para workloads OLTP
4. **Replicação**: Suporte nativo para DR e HA
5. **Comunidade**: Amplo suporte e ferramentas

### Por que SQLAlchemy ORM?

1. **Abstração**: Facilita mudança de RDBMS
2. **Type Safety**: Validação em Python
3. **Session Management**: Controle transacional robusto
4. **Migrations**: Suporte via Alembic
5. **Query Building**: Construção segura de queries

### Por que Decimal em vez de Float?

1. **Precisão**: Evita erros de arredondamento
2. **Conformidade**: GAAP/IFRS exigem precisão decimal
3. **Auditoria**: Resultados reproduzíveis

### Por que UUID?

1. **Distribuição**: IDs globalmente únicos
2. **Segurança**: Não previsíveis
3. **Merge**: Facilita merge de bases
4. **Escalabilidade**: Sem contenção em sequence

---

## Segurança

### Níveis de Segurança

#### 1. Nível de Banco de Dados
- Usuários com privilégios mínimos
- Criptografia em trânsito (TLS)
- Criptografia em repouso (opcional)
- Backup criptografado

#### 2. Nível de Aplicação
- Validação de entrada
- Prevenção de SQL injection (via ORM)
- Sanitização de dados
- Rate limiting (futuro)

#### 3. Nível de Auditoria
- Log de todas as operações
- Hash de integridade
- Trilha de não-repúdio
- Timestamp UTC

#### 4. Nível de Acesso
- Autenticação obrigatória
- Identificação de usuário em cada operação
- IP tracking
- Sistema de origem tracking

---

## Performance e Escalabilidade

### Otimizações Implementadas

1. **Índices Estratégicos**
   - Por transaction_date para consultas temporais
   - Por business_key para rastreamento
   - Composto para queries frequentes

2. **Pool de Conexões**
   - Configurável via DB_POOL_SIZE
   - Reuso de conexões
   - Timeout configurável

3. **Queries Otimizadas**
   - Uso de JOINs eficientes
   - Paginação em relatórios
   - Filtros no banco

### Considerações de Escala

#### Volume Baixo (< 10K transações/dia)
- Setup padrão suficiente
- Single instance
- Backup diário

#### Volume Médio (10K - 100K transações/dia)
- Read replicas para relatórios
- Índices adicionais
- Cache de consultas frequentes

#### Volume Alto (> 100K transações/dia)
- Particionamento de tabelas
- Sharding por período
- Cache distribuído
- Processamento assíncrono

---

## Extensibilidade

### Pontos de Extensão

1. **Tipos de Conta Customizados**
   ```python
   class CustomAccountType(Enum):
       ASSET = "ASSET"
       # Adicionar novos tipos aqui
   ```

2. **Validações Customizadas**
   ```python
   def custom_validation(self, transaction):
       # Adicionar lógica de validação
       pass
   ```

3. **Relatórios Customizados**
   ```python
   class CustomReportEngine(LedgerReportEngine):
       def generate_custom_report(self, params):
           # Implementar relatório específico
           pass
   ```

4. **Integrações**
   - Web hooks para eventos
   - API REST (futuro)
   - Message queue (futuro)

---

## Limitações e Trade-offs

### Limitações Conhecidas

1. **Não Distributed**: Single database design
2. **Não Real-time**: OLTP, não streaming
3. **Moeda Única**: Por transação (multi-currency futuro)
4. **Sem Workflow**: Aprovações devem ser externas

### Trade-offs de Design

| Decisão | Benefício | Custo |
|---------|-----------|-------|
| Imutabilidade | Auditoria completa | Espaço em disco |
| Dupla entrada | Integridade garantida | Complexidade |
| UUID | Distribuição | 36 bytes vs. 4-8 |
| Hash | Integridade verificável | CPU overhead |
| ORM | Portabilidade | Performance vs. SQL puro |

---

## Evolução Futura

### Roadmap Técnico

#### Fase 1 (Atual)
- ✅ Core ledger engine
- ✅ Double-entry validation
- ✅ Basic reporting
- ✅ CLI administration

#### Fase 2 (Próxima)
- [ ] API REST
- [ ] Closing periods
- [ ] Multi-currency
- [ ] Workflow engine

#### Fase 3 (Futuro)
- [ ] Web UI
- [ ] Advanced analytics
- [ ] Machine learning insights
- [ ] Blockchain integration (optional)

---

## Referências

### Padrões Contábeis
- IFRS (International Financial Reporting Standards)
- GAAP (Generally Accepted Accounting Principles)
- SOX (Sarbanes-Oxley Act)

### Padrões Técnicos
- Event Sourcing
- CQRS (Command Query Responsibility Segregation)
- Domain-Driven Design

### Inspirações
- Sistemas bancários core
- Ledger-CLI
- Beancount
- GnuCash

---

**Versão**: 1.0.0  
**Última Atualização**: Janeiro 2026  
**Arquiteto**: Financial Systems Team
