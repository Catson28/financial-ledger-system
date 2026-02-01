# 📒 Ledger / Accounting Engine

## Sistema de Contabilidade Imutável com Dupla Entrada

Sistema de ledger de nível bancário/corporativo projetado para ambientes regulados de alto risco. Implementa princípios de imutabilidade, auditabilidade completa e conformidade contábil.

---

## 🎯 Princípios Fundamentais

Este sistema foi projetado seguindo princípios rigorosos de contabilidade financeira:

### 1. **Imutabilidade**
- Nada é apagado ou atualizado
- Correções são feitas por lançamentos compensatórios
- Histórico completo preservado permanentemente

### 2. **Dupla Entrada**
- Débitos sempre igual a Créditos
- Validação automática em cada transação
- Integridade contábil garantida

### 3. **Auditabilidade**
- Trilha completa de todas as operações
- Hash criptográfico para integridade de dados
- Rastreamento de autor, data, sistema de origem

### 4. **Atomicidade**
- Transações são "tudo ou nada"
- Não existem transações parciais
- Consistência garantida

### 5. **Separação: Fato, Regra e Visão**
- **Fato**: Evento econômico registrado (imutável)
- **Regra**: Lógica de negócio aplicada
- **Visão**: Diferentes perspectivas sobre os mesmos fatos

---

## 📋 Componentes do Sistema

### 1. **Discovery Tool** (`ledger_discovery_tool.py`)
Ferramenta interativa de descoberta de domínio contábil e regulatório. Força o entendimento completo do contexto antes de gerar código.

**Funcionalidades**:
- 8 fases de descoberta
- Validação de requisitos legais e regulatórios
- Definição de modelo contábil
- Configuração de dupla entrada
- Estratégias de correção e fechamento
- Geração de configuração auditável

**Uso**:
```bash
python ledger_discovery_tool.py
```

### 2. **Ledger Engine** (`ledger_engine.py`)
Motor principal do sistema de contabilidade.

**Características**:
- Implementação completa de dupla entrada
- Plano de contas hierárquico
- Transações imutáveis
- Correção por estorno
- Validação de integridade
- Trilha de auditoria completa

**Principais Classes**:
- `LedgerEngine`: Motor principal
- `ChartOfAccounts`: Plano de contas
- `Transaction`: Cabeçalho de transação
- `JournalEntry`: Lançamentos contábeis
- `AuditLog`: Log de auditoria

### 3. **Reporting Module** (`ledger_reporting.py`)
Módulo de geração de relatórios auditáveis.

**Relatórios Disponíveis**:
- **Balance Sheet** (Balanço Patrimonial)
- **Income Statement** (Demonstração de Resultados)
- **Trial Balance** (Balancete de Verificação)
- **General Ledger** (Razão Geral)
- **Audit Trail** (Trilha de Auditoria)

**Características**:
- Relatórios reproduzíveis
- Hash de integridade
- Exportação JSON/CSV
- Metadata completa

### 4. **Admin CLI** (`ledger_admin_cli.py`)
Interface de linha de comando para administração.

**Comandos Disponíveis**:
```bash
# Inicializar banco de dados
python ledger_admin_cli.py init --confirm

# Criar conta
python ledger_admin_cli.py create-account \
  --code 1100 \
  --name "Caixa" \
  --type ASSET \
  --user admin@example.com

# Lançar transação
python ledger_admin_cli.py post-transaction \
  --event-type PAYMENT \
  --description "Pagamento fornecedor" \
  --entries entries.json \
  --user admin@example.com

# Reverter transação
python ledger_admin_cli.py reverse \
  --transaction-id abc-123 \
  --reason "Erro de lançamento" \
  --user admin@example.com

# Consultar saldo
python ledger_admin_cli.py balance --account-code 1100

# Balancete
python ledger_admin_cli.py trial-balance \
  --output balancete.csv

# Verificar integridade
python ledger_admin_cli.py verify

# Logs de auditoria
python ledger_admin_cli.py audit --days 30

# Gerar relatórios
python ledger_admin_cli.py report \
  --type balance-sheet \
  --output balanco.json \
  --user admin@example.com
```

---

## 🚀 Instalação

### Requisitos
- Python 3.10+
- MySQL 8.0+ ou MariaDB 10.5+ (recomendado para sistemas financeiros)
- PostgreSQL 13+ (alternativa)

### Passo a Passo

1. **Clone ou copie os arquivos do sistema**

2. **Crie ambiente virtual**:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. **Instale dependências**:
```bash
pip install -r requirements.txt
```

4. **Configure variáveis de ambiente**:
```bash
cp .env.template .env
# Edite .env com suas configurações
```

5. **Configure banco de dados**:
```env
LEDGER_DB_URI=mysql+pymysql://user:password@localhost:3306/ledger_db?charset=utf8mb4
```

6. **Inicialize o banco de dados**:
```bash
python ledger_admin_cli.py init --confirm
```

---

## 📊 Modelo de Dados

### Estrutura Principal

```
chart_of_accounts
├── account_id (PK)
├── account_code (UNIQUE)
├── account_name
├── account_type (ASSET, LIABILITY, EQUITY, REVENUE, EXPENSE)
├── parent_account_id (FK)
└── level

transactions
├── transaction_id (PK)
├── transaction_number (UNIQUE)
├── transaction_date
├── posting_date
├── business_event_type
├── business_key
├── status (PENDING, POSTED, REVERSED)
├── is_reversal
├── reverses_transaction_id (FK)
├── transaction_hash
└── [audit fields]

journal_entries
├── entry_id (PK)
├── transaction_id (FK)
├── entry_number
├── account_id (FK)
├── account_code
├── entry_type (DEBIT, CREDIT)
├── amount (CHECK > 0)
├── cost_center
├── business_unit
└── project_code

audit_log
├── audit_id (PK)
├── event_timestamp
├── event_type
├── severity
├── transaction_id
├── user_id
├── source_system
├── action
└── description
```

---

## 🔐 Segurança e Auditoria

### Trilha de Auditoria
Todos os eventos são registrados em `audit_log`:
- Criação de contas
- Lançamento de transações
- Reversões
- Geração de relatórios
- Falhas de operação

### Hash de Integridade
Cada transação possui um hash SHA-256 calculado a partir de:
- Número da transação
- Tipo de evento
- Descrição
- Total de débitos/créditos
- Usuário criador

### Rastreamento
Cada registro contém:
- `created_by`: Identificação do usuário
- `source_system`: Sistema de origem
- `source_ip`: IP de origem (opcional)
- `created_at`: Timestamp UTC

---

## 💡 Exemplos de Uso

### Exemplo 1: Criar Plano de Contas

```python
from ledger_engine import LedgerEngine, AccountDefinition, AccountType

ledger = LedgerEngine()

# Criar conta de Ativo
cash_account = AccountDefinition(
    account_code="1100",
    account_name="Caixa",
    account_type=AccountType.ASSET,
    description="Conta de caixa geral"
)

account_id = ledger.create_account(
    cash_account,
    created_by="admin@company.com"
)
```

### Exemplo 2: Lançar Transação

```python
from ledger_engine import TransactionInput, JournalEntryInput, EntryType
from decimal import Decimal
from datetime import datetime, timezone

# Definir lançamentos (débito e crédito)
entries = [
    JournalEntryInput(
        account_code="1100",  # Caixa
        entry_type=EntryType.DEBIT,
        amount=Decimal("1000.00"),
        memo="Recebimento de cliente"
    ),
    JournalEntryInput(
        account_code="4100",  # Receita de Vendas
        entry_type=EntryType.CREDIT,
        amount=Decimal("1000.00"),
        memo="Venda à vista"
    )
]

# Criar transação
transaction = TransactionInput(
    business_event_type="SALE",
    description="Venda produto XYZ",
    transaction_date=datetime.now(timezone.utc),
    entries=entries,
    business_key="SALE-2024-001"
)

# Lançar
txn_id = ledger.post_transaction(
    transaction,
    created_by="sales@company.com",
    source_system="ERP_SALES"
)
```

### Exemplo 3: Reverter Transação

```python
# Reverter uma transação (criando lançamentos compensatórios)
reversal_id = ledger.reverse_transaction(
    original_transaction_id=txn_id,
    reversal_reason="Venda cancelada pelo cliente",
    created_by="manager@company.com",
    source_system="ERP_SALES"
)
```

### Exemplo 4: Gerar Relatórios

```python
from ledger_reporting import LedgerReportEngine

report_engine = LedgerReportEngine(ledger)

# Balancete
trial_balance = report_engine.generate_trial_balance(
    as_of_date=datetime.now(timezone.utc),
    generated_by="accountant@company.com"
)

# Balanço Patrimonial
balance_sheet = report_engine.generate_balance_sheet(
    as_of_date=datetime.now(timezone.utc),
    generated_by="accountant@company.com"
)

# Demonstração de Resultados
income_statement = report_engine.generate_income_statement(
    start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
    end_date=datetime(2024, 12, 31, tzinfo=timezone.utc),
    generated_by="accountant@company.com"
)

# Exportar
report_engine.export_to_csv(balance_sheet, "balanco_2024.csv")
report_engine.export_to_json(income_statement, "dre_2024.json")
```

---

## 🔧 Configuração Avançada

### Fechamentos Contábeis

```python
# Implementar lógica de fechamento mensal/anual
# TODO: Adicionar funcionalidade de closing_periods
```

### Integrações

O sistema pode ser integrado com:
- **ERP**: Via API ou arquivo em lote
- **BI/Analytics**: Exportação de dados
- **Reguladores**: Relatórios padronizados
- **Auditoria Externa**: Acesso somente leitura

### Performance

Para alto volume de transações:
- Use pool de conexões adequado
- Configure índices no banco de dados
- Implemente cache de consultas frequentes
- Considere particionamento de tabelas

---

## 📖 Conformidade Regulatória

### IFRS / GAAP
Sistema suporta princípios contábeis internacionais:
- Registro pelo regime de competência
- Dupla entrada obrigatória
- Conservadorismo
- Materialidade

### Auditoria
Preparado para auditoria com:
- Trilha completa de eventos
- Relatórios reproduzíveis
- Hash de integridade
- Não repúdio (criador identificado)

### Retenção de Dados
Configure período de retenção em `.env`:
```env
AUDIT_RETENTION_DAYS=2555  # 7 anos
REPORT_RETENTION_DAYS=2555
```

---

## 🧪 Testes

```bash
# Executar testes
pytest tests/

# Com cobertura
pytest --cov=. tests/

# Testes de integridade
python ledger_admin_cli.py verify
```

---

## 📝 Próximos Passos

Após instalação:

1. **Execute o Discovery Tool** para documentar seu domínio
2. **Configure o plano de contas** específico da sua empresa
3. **Defina processos de aprovação** para correções
4. **Configure integrações** com sistemas existentes
5. **Treine usuários** no processo de lançamento
6. **Estabeleça rotinas de auditoria** periódicas

---

## ⚠️  Limitações Conhecidas

- Sistema não implementa controle de câmbio múltiplo
- Fechamentos contábeis requerem implementação customizada
- Workflow de aprovação não incluído (implementar externamente)
- Interface web não incluída (use CLI ou desenvolva API REST)

---

## 🤝 Suporte

Para questões sobre contabilidade e regulamentação:
- Consulte seu contador
- Revise normas IFRS/GAAP aplicáveis
- Consulte regulador do seu setor

Para questões técnicas:
- Revise logs de auditoria
- Execute verificação de integridade
- Consulte documentação do código

---

## 📄 Licença

Sistema desenvolvido para fins profissionais e educacionais.

---

## ✨ Características Destacadas

✅ Imutabilidade total  
✅ Dupla entrada validada  
✅ Auditoria completa  
✅ Relatórios reproduzíveis  
✅ Hash de integridade  
✅ Reversão por compensação  
✅ Plano de contas hierárquico  
✅ Multi-dimensão (centro de custo, projeto, etc.)  
✅ Pronto para regulação  
✅ CLI administrativa  

---

**Versão**: 1.0.0  
**Última Atualização**: Janeiro 2026  
**Desenvolvido seguindo**: Princípios de Ledger de Nível Bancário
