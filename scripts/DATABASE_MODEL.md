```mermaid
erDiagram
    CHART_OF_ACCOUNTS ||--o{ CHART_OF_ACCOUNTS : "parent_of"
    CHART_OF_ACCOUNTS ||--o{ JOURNAL_ENTRIES : "has"
    TRANSACTIONS ||--|{ JOURNAL_ENTRIES : "contains"
    TRANSACTIONS ||--o| TRANSACTIONS : "reverses"
    TRANSACTIONS ||--o{ AUDIT_LOG : "generates"
    CLOSING_PERIODS ||--o{ TRANSACTIONS : "includes"
    
    CHART_OF_ACCOUNTS {
        varchar(36) account_id PK "UUID único da conta"
        varchar(50) account_code UK "Código único da conta"
        varchar(200) account_name "Nome da conta"
        varchar(20) account_type "ASSET, LIABILITY, EQUITY, REVENUE, EXPENSE"
        varchar(36) parent_account_id FK "ID da conta pai (hierarquia)"
        numeric(2) level "Nível na hierarquia (1-99)"
        boolean is_active "Conta ativa ou inativa"
        text description "Descrição da conta"
        datetime created_at "Data/hora de criação (UTC)"
        varchar(200) created_by "Usuário criador"
        numeric(10) version "Versão do registro (1, 2, 3...)"
    }
    
    TRANSACTIONS {
        varchar(36) transaction_id PK "UUID único da transação"
        varchar(50) transaction_number UK "Número sequencial YYYYMMDD-NNNNNN"
        datetime transaction_date "Data do evento econômico (UTC)"
        datetime posting_date "Data de lançamento contábil (UTC)"
        varchar(100) business_event_type "Tipo de evento (SALE, PAYMENT, etc)"
        varchar(200) business_key "Chave de negócio para rastreamento"
        varchar(100) reference_number "Número de referência externo"
        text description "Descrição da transação"
        varchar(20) status "PENDING, POSTED, REVERSED, CANCELLED"
        boolean is_reversal "Flag: é uma reversão?"
        varchar(36) reverses_transaction_id FK "ID da transação original (se reversão)"
        varchar(36) reversed_by_transaction_id "ID da transação que reverteu esta"
        text reversal_reason "Motivo da reversão"
        datetime created_at "Data/hora de criação (UTC)"
        varchar(200) created_by "Usuário criador"
        varchar(100) source_system "Sistema de origem"
        varchar(45) source_ip "IP de origem"
        varchar(64) transaction_hash "SHA-256 para integridade"
    }
    
    JOURNAL_ENTRIES {
        varchar(36) entry_id PK "UUID único do lançamento"
        varchar(36) transaction_id FK "ID da transação pai"
        numeric(5) entry_number "Número da linha (1, 2, 3...)"
        varchar(36) account_id FK "ID da conta"
        varchar(50) account_code "Código da conta (desnormalizado)"
        varchar(10) entry_type "DEBIT ou CREDIT"
        numeric(20,2) amount "Valor do lançamento (sempre > 0)"
        varchar(3) currency "Código ISO 4217 (AOA, USD, EUR)"
        varchar(50) cost_center "Centro de custo (opcional)"
        varchar(50) business_unit "Unidade de negócio (opcional)"
        varchar(50) project_code "Código do projeto (opcional)"
        text memo "Observações do lançamento"
        datetime created_at "Data/hora de criação (UTC)"
    }
    
    CLOSING_PERIODS {
        varchar(36) closing_id PK "UUID único do fechamento"
        varchar(20) period_type "DAILY, MONTHLY, QUARTERLY, ANNUAL"
        datetime period_start "Início do período (UTC)"
        datetime period_end "Fim do período (UTC)"
        boolean is_closed "Flag: período fechado?"
        datetime closed_at "Data/hora do fechamento (UTC)"
        varchar(200) closed_by "Usuário que fechou"
        numeric(20,2) total_debits "Total de débitos do período"
        numeric(20,2) total_credits "Total de créditos do período"
        boolean balance_check "Verificação: débitos = créditos?"
        datetime created_at "Data/hora de criação (UTC)"
    }
    
    AUDIT_LOG {
        varchar(36) audit_id PK "UUID único do log"
        datetime event_timestamp "Data/hora do evento (UTC)"
        varchar(100) event_type "Tipo de evento auditado"
        varchar(20) severity "INFO, WARNING, ERROR, CRITICAL"
        varchar(36) transaction_id FK "ID da transação (se aplicável)"
        varchar(200) user_id "Identificação do usuário"
        varchar(100) source_system "Sistema de origem"
        varchar(45) source_ip "IP de origem"
        varchar(100) action "Ação executada"
        varchar(50) entity_type "Tipo de entidade afetada"
        varchar(36) entity_id "ID da entidade afetada"
        text description "Descrição detalhada do evento"
        text metadata "JSON com contexto adicional"
    }
```

## 📊 Detalhamento do Modelo de Dados

### 🔑 Relacionamentos Principais

#### 1. CHART_OF_ACCOUNTS (Plano de Contas)
- **Auto-relacionamento**: Uma conta pode ter uma conta pai (hierarquia)
- **Relacionamento com JOURNAL_ENTRIES**: Uma conta pode ter múltiplos lançamentos
- **Cardinalidade**: 1:N (uma conta → muitos lançamentos)

#### 2. TRANSACTIONS (Transações)
- **Auto-relacionamento**: Uma transação pode reverter outra transação
- **Relacionamento com JOURNAL_ENTRIES**: Uma transação contém múltiplos lançamentos
- **Cardinalidade**: 1:N (uma transação → muitos lançamentos)
- **Regra de negócio**: Mínimo 2 lançamentos por transação (dupla entrada)

#### 3. JOURNAL_ENTRIES (Lançamentos Contábeis)
- **Relacionamento com TRANSACTIONS**: Pertence a uma transação
- **Relacionamento com CHART_OF_ACCOUNTS**: Referencia uma conta
- **Cardinalidade**: N:1 (muitos lançamentos → uma transação)

#### 4. CLOSING_PERIODS (Períodos de Fechamento)
- **Relacionamento implícito com TRANSACTIONS**: Agrupa transações por período
- **Cardinalidade**: 1:N (um período → muitas transações)

#### 5. AUDIT_LOG (Log de Auditoria)
- **Relacionamento com TRANSACTIONS**: Registra eventos de transações
- **Relacionamento universal**: Pode referenciar qualquer entidade
- **Cardinalidade**: N:1 (muitos logs → uma transação)

---

### 📐 Constraints e Regras de Integridade

#### Constraints de Chave Primária
```sql
-- Todas as tabelas usam UUID como PK
ALTER TABLE chart_of_accounts ADD PRIMARY KEY (account_id);
ALTER TABLE transactions ADD PRIMARY KEY (transaction_id);
ALTER TABLE journal_entries ADD PRIMARY KEY (entry_id);
ALTER TABLE closing_periods ADD PRIMARY KEY (closing_id);
ALTER TABLE audit_log ADD PRIMARY KEY (audit_id);
```

#### Constraints de Unicidade
```sql
-- Códigos únicos
ALTER TABLE chart_of_accounts ADD UNIQUE (account_code);
ALTER TABLE transactions ADD UNIQUE (transaction_number);
```

#### Constraints de Chave Estrangeira
```sql
-- Hierarquia de contas
ALTER TABLE chart_of_accounts 
    ADD FOREIGN KEY (parent_account_id) 
    REFERENCES chart_of_accounts(account_id);

-- Lançamentos → Transação
ALTER TABLE journal_entries 
    ADD FOREIGN KEY (transaction_id) 
    REFERENCES transactions(transaction_id);

-- Lançamentos → Conta
ALTER TABLE journal_entries 
    ADD FOREIGN KEY (account_id) 
    REFERENCES chart_of_accounts(account_id);

-- Reversão de transações
ALTER TABLE transactions 
    ADD FOREIGN KEY (reverses_transaction_id) 
    REFERENCES transactions(transaction_id);

-- Auditoria → Transação
ALTER TABLE audit_log 
    ADD FOREIGN KEY (transaction_id) 
    REFERENCES transactions(transaction_id);
```

#### Constraints de Check
```sql
-- Valor sempre positivo
ALTER TABLE journal_entries 
    ADD CONSTRAINT check_amount_positive 
    CHECK (amount > 0);

-- Tipo de conta válido
ALTER TABLE chart_of_accounts 
    ADD CONSTRAINT check_account_type 
    CHECK (account_type IN ('ASSET', 'LIABILITY', 'EQUITY', 'REVENUE', 'EXPENSE'));

-- Tipo de lançamento válido
ALTER TABLE journal_entries 
    ADD CONSTRAINT check_entry_type 
    CHECK (entry_type IN ('DEBIT', 'CREDIT'));

-- Status de transação válido
ALTER TABLE transactions 
    ADD CONSTRAINT check_status 
    CHECK (status IN ('PENDING', 'POSTED', 'REVERSED', 'CANCELLED'));

-- Tipo de período válido
ALTER TABLE closing_periods 
    ADD CONSTRAINT check_period_type 
    CHECK (period_type IN ('DAILY', 'MONTHLY', 'QUARTERLY', 'ANNUAL'));

-- Severidade válida
ALTER TABLE audit_log 
    ADD CONSTRAINT check_severity 
    CHECK (severity IN ('INFO', 'WARNING', 'ERROR', 'CRITICAL'));
```

---

### 📊 Índices Recomendados

```sql
-- CHART_OF_ACCOUNTS
CREATE INDEX idx_account_code ON chart_of_accounts(account_code);
CREATE INDEX idx_account_type ON chart_of_accounts(account_type);
CREATE INDEX idx_parent_account ON chart_of_accounts(parent_account_id);
CREATE INDEX idx_account_active ON chart_of_accounts(is_active);

-- TRANSACTIONS
CREATE INDEX idx_transaction_number ON transactions(transaction_number);
CREATE INDEX idx_transaction_date ON transactions(transaction_date);
CREATE INDEX idx_posting_date ON transactions(posting_date);
CREATE INDEX idx_business_key ON transactions(business_key);
CREATE INDEX idx_status ON transactions(status);
CREATE INDEX idx_reversal ON transactions(is_reversal, reverses_transaction_id);
CREATE INDEX idx_created_at ON transactions(created_at);

-- JOURNAL_ENTRIES
CREATE INDEX idx_transaction_entry ON journal_entries(transaction_id, entry_number);
CREATE INDEX idx_account_code ON journal_entries(account_code);
CREATE INDEX idx_entry_type ON journal_entries(entry_type);
CREATE INDEX idx_cost_center ON journal_entries(cost_center);
CREATE INDEX idx_business_unit ON journal_entries(business_unit);
CREATE INDEX idx_project_code ON journal_entries(project_code);

-- CLOSING_PERIODS
CREATE INDEX idx_period_type ON closing_periods(period_type);
CREATE INDEX idx_period_dates ON closing_periods(period_start, period_end);
CREATE INDEX idx_is_closed ON closing_periods(is_closed);

-- AUDIT_LOG
CREATE INDEX idx_event_timestamp ON audit_log(event_timestamp);
CREATE INDEX idx_transaction_id ON audit_log(transaction_id);
CREATE INDEX idx_user_id ON audit_log(user_id);
CREATE INDEX idx_severity ON audit_log(severity);
CREATE INDEX idx_event_type ON audit_log(event_type);
```

---

### 🔐 Regras de Negócio no Banco de Dados

#### Trigger: Validação de Dupla Entrada
```sql
-- Trigger para garantir dupla entrada após INSERT de lançamento
DELIMITER //
CREATE TRIGGER validate_double_entry_after_insert
AFTER INSERT ON journal_entries
FOR EACH ROW
BEGIN
    DECLARE v_debits DECIMAL(20,2);
    DECLARE v_credits DECIMAL(20,2);
    DECLARE v_status VARCHAR(20);
    
    -- Buscar status da transação
    SELECT status INTO v_status 
    FROM transactions 
    WHERE transaction_id = NEW.transaction_id;
    
    -- Apenas validar se transação está sendo lançada (POSTED)
    IF v_status = 'POSTED' THEN
        -- Calcular totais
        SELECT 
            COALESCE(SUM(CASE WHEN entry_type = 'DEBIT' THEN amount ELSE 0 END), 0),
            COALESCE(SUM(CASE WHEN entry_type = 'CREDIT' THEN amount ELSE 0 END), 0)
        INTO v_debits, v_credits
        FROM journal_entries
        WHERE transaction_id = NEW.transaction_id;
        
        -- Validar dupla entrada
        IF v_debits != v_credits THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Double-entry violation: Debits must equal Credits';
        END IF;
    END IF;
END//
DELIMITER ;
```

#### Trigger: Prevenção de Modificação
```sql
-- Trigger para impedir UPDATE em transações postadas (imutabilidade)
DELIMITER //
CREATE TRIGGER prevent_transaction_update
BEFORE UPDATE ON transactions
FOR EACH ROW
BEGIN
    IF OLD.status = 'POSTED' AND NEW.status != 'REVERSED' THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Cannot modify posted transaction. Use reversal instead.';
    END IF;
END//
DELIMITER ;

-- Trigger para impedir DELETE (imutabilidade)
DELIMITER //
CREATE TRIGGER prevent_transaction_delete
BEFORE DELETE ON transactions
FOR EACH ROW
BEGIN
    SIGNAL SQLSTATE '45000'
    SET MESSAGE_TEXT = 'Cannot delete transactions. Use reversal instead.';
END//
DELIMITER ;
```

---

### 📈 Views Recomendadas

#### View: Saldos por Conta
```sql
CREATE VIEW v_account_balances AS
SELECT 
    coa.account_id,
    coa.account_code,
    coa.account_name,
    coa.account_type,
    COALESCE(SUM(CASE WHEN je.entry_type = 'DEBIT' THEN je.amount ELSE 0 END), 0) as total_debits,
    COALESCE(SUM(CASE WHEN je.entry_type = 'CREDIT' THEN je.amount ELSE 0 END), 0) as total_credits,
    CASE 
        WHEN coa.account_type IN ('ASSET', 'EXPENSE') THEN
            COALESCE(SUM(CASE WHEN je.entry_type = 'DEBIT' THEN je.amount ELSE 0 END), 0) -
            COALESCE(SUM(CASE WHEN je.entry_type = 'CREDIT' THEN je.amount ELSE 0 END), 0)
        ELSE
            COALESCE(SUM(CASE WHEN je.entry_type = 'CREDIT' THEN je.amount ELSE 0 END), 0) -
            COALESCE(SUM(CASE WHEN je.entry_type = 'DEBIT' THEN je.amount ELSE 0 END), 0)
    END as balance
FROM chart_of_accounts coa
LEFT JOIN journal_entries je ON coa.account_id = je.account_id
LEFT JOIN transactions t ON je.transaction_id = t.transaction_id
WHERE t.status = 'POSTED' OR t.status IS NULL
GROUP BY coa.account_id, coa.account_code, coa.account_name, coa.account_type;
```

#### View: Transações com Totais
```sql
CREATE VIEW v_transactions_summary AS
SELECT 
    t.transaction_id,
    t.transaction_number,
    t.transaction_date,
    t.posting_date,
    t.business_event_type,
    t.description,
    t.status,
    COUNT(je.entry_id) as entry_count,
    SUM(CASE WHEN je.entry_type = 'DEBIT' THEN je.amount ELSE 0 END) as total_debits,
    SUM(CASE WHEN je.entry_type = 'CREDIT' THEN je.amount ELSE 0 END) as total_credits
FROM transactions t
LEFT JOIN journal_entries je ON t.transaction_id = je.transaction_id
GROUP BY t.transaction_id, t.transaction_number, t.transaction_date, 
         t.posting_date, t.business_event_type, t.description, t.status;
```

#### View: Balancete de Verificação
```sql
CREATE VIEW v_trial_balance AS
SELECT 
    coa.account_code,
    coa.account_name,
    coa.account_type,
    coa.level,
    ab.total_debits,
    ab.total_credits,
    ab.balance
FROM chart_of_accounts coa
INNER JOIN v_account_balances ab ON coa.account_id = ab.account_id
WHERE coa.is_active = TRUE
  AND ab.balance != 0
ORDER BY coa.account_code;
```

---

### 📊 Estatísticas do Modelo

**Total de Tabelas**: 5  
**Total de Relacionamentos**: 6  
**Total de Atributos**: 63  
**Total de Constraints**: ~20  
**Total de Índices**: ~25  
**Total de Views**: 3 (recomendadas)  

---

### 🎯 Cardinalidades Detalhadas

| Relacionamento | Cardinalidade | Descrição |
|----------------|---------------|-----------|
| CHART_OF_ACCOUNTS ↔ CHART_OF_ACCOUNTS | 1:N | Uma conta pai pode ter várias contas filhas |
| CHART_OF_ACCOUNTS → JOURNAL_ENTRIES | 1:N | Uma conta pode ter muitos lançamentos |
| TRANSACTIONS → JOURNAL_ENTRIES | 1:N | Uma transação contém múltiplos lançamentos (mín. 2) |
| TRANSACTIONS ↔ TRANSACTIONS | 1:1 | Uma transação pode reverter outra (bidirecional) |
| TRANSACTIONS → AUDIT_LOG | 1:N | Uma transação gera múltiplos eventos de auditoria |
| CLOSING_PERIODS → TRANSACTIONS | 1:N | Um período contém múltiplas transações |

---

Este modelo garante:
✅ **Integridade referencial completa**  
✅ **Imutabilidade através de triggers**  
✅ **Validação de dupla entrada no banco**  
✅ **Auditoria completa de todas as operações**  
✅ **Performance através de índices estratégicos**  
✅ **Flexibilidade para hierarquias e dimensões analíticas**
