# 🚀 Quick Start Guide - Ledger / Accounting Engine

Este guia rápido mostra como começar a usar o sistema de ledger em 5 minutos.

---

## Instalação Rápida

### Passo 1: Requisitos
Certifique-se de ter instalado:
- Python 3.10 ou superior
- MySQL 8.0+ ou MariaDB 10.5+

### Passo 2: Setup Automático
```bash
# Execute o script de setup
python setup.py

# Ative o ambiente virtual
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows
```

### Passo 3: Configure o Banco de Dados
Edite o arquivo `.env`:
```env
LEDGER_DB_URI=mysql+pymysql://seu_usuario:sua_senha@localhost:3306/ledger_db
```

### Passo 4: Inicialize o Sistema
```bash
python ledger_admin_cli.py init --confirm
```

---

## Primeiros Passos

### 1. Execute o Discovery Tool (Recomendado)

```bash
python ledger_discovery_tool.py
```

Este assistente interativo irá guiá-lo através de 8 fases de descoberta para entender completamente seu domínio contábil.

### 2. Ou Crie Contas Manualmente

```bash
# Criar conta de Caixa
python ledger_admin_cli.py create-account \
  --code 1100 \
  --name "Caixa" \
  --type ASSET \
  --user seu_email@company.com

# Criar conta de Receitas
python ledger_admin_cli.py create-account \
  --code 4100 \
  --name "Receitas de Vendas" \
  --type REVENUE \
  --user seu_email@company.com
```

### 3. Lançar Primeira Transação

Crie um arquivo `minha_transacao.json`:
```json
[
  {
    "account_code": "1100",
    "entry_type": "DEBIT",
    "amount": "1000.00",
    "memo": "Recebimento de venda"
  },
  {
    "account_code": "4100",
    "entry_type": "CREDIT",
    "amount": "1000.00",
    "memo": "Receita de venda"
  }
]
```

Poste a transação:
```bash
python ledger_admin_cli.py post-transaction \
  --event-type SALE \
  --description "Venda de produto" \
  --entries minha_transacao.json \
  --user seu_email@company.com
```

### 4. Verificar Saldo

```bash
python ledger_admin_cli.py balance --account-code 1100
```

### 5. Gerar Balancete

```bash
python ledger_admin_cli.py trial-balance --output balancete.csv
```

---

## Uso Programático

### Exemplo Python

```python
from ledger_engine import (
    LedgerEngine, AccountDefinition, AccountType,
    TransactionInput, JournalEntryInput, EntryType
)
from decimal import Decimal
from datetime import datetime, timezone

# Inicializar engine
ledger = LedgerEngine()

# Criar conta
account_def = AccountDefinition(
    account_code="1100",
    account_name="Caixa",
    account_type=AccountType.ASSET
)
ledger.create_account(account_def, created_by="admin@example.com")

# Lançar transação
entries = [
    JournalEntryInput(
        account_code="1100",
        entry_type=EntryType.DEBIT,
        amount=Decimal("1000.00")
    ),
    JournalEntryInput(
        account_code="4100",
        entry_type=EntryType.CREDIT,
        amount=Decimal("1000.00")
    )
]

transaction = TransactionInput(
    business_event_type="SALE",
    description="Venda",
    transaction_date=datetime.now(timezone.utc),
    entries=entries
)

txn_id = ledger.post_transaction(
    transaction,
    created_by="sales@example.com",
    source_system="MY_APP"
)

# Consultar saldo
balance = ledger.get_account_balance("1100")
print(f"Saldo: {balance}")
```

---

## Comandos Úteis

### Verificação de Integridade
```bash
python ledger_admin_cli.py verify
```

### Ver Logs de Auditoria
```bash
python ledger_admin_cli.py audit --days 7
```

### Gerar Relatórios
```bash
# Balanço Patrimonial
python ledger_admin_cli.py report \
  --type balance-sheet \
  --output balanco.json \
  --user accountant@example.com

# Demonstração de Resultados
python ledger_admin_cli.py report \
  --type income-statement \
  --start-date 2024-01-01 \
  --end-date 2024-12-31 \
  --output dre.csv \
  --user accountant@example.com
```

---

## Casos de Uso Comuns

### Caso 1: Venda à Vista
```json
[
  {"account_code": "1100", "entry_type": "DEBIT", "amount": "500.00"},
  {"account_code": "4100", "entry_type": "CREDIT", "amount": "500.00"}
]
```

### Caso 2: Venda a Prazo
```json
[
  {"account_code": "1200", "entry_type": "DEBIT", "amount": "1000.00"},
  {"account_code": "4100", "entry_type": "CREDIT", "amount": "1000.00"}
]
```

### Caso 3: Pagamento de Fornecedor
```json
[
  {"account_code": "2100", "entry_type": "DEBIT", "amount": "750.00"},
  {"account_code": "1100", "entry_type": "CREDIT", "amount": "750.00"}
]
```

### Caso 4: Despesa Administrativa
```json
[
  {"account_code": "5200", "entry_type": "DEBIT", "amount": "300.00"},
  {"account_code": "1100", "entry_type": "CREDIT", "amount": "300.00"}
]
```

---

## Dicas Importantes

### ✅ Boas Práticas

1. **Sempre use o Discovery Tool** primeiro para documentar seu domínio
2. **Mantenha business_key** em todas as transações para rastreamento
3. **Use descrições claras** em transações e lançamentos
4. **Execute verificação de integridade** regularmente
5. **Faça backup** do banco de dados diariamente

### ⚠️ Evite

1. **Nunca** tente atualizar ou deletar diretamente no banco
2. **Nunca** desabilite validação de dupla entrada
3. **Nunca** faça reversões manuais (use o comando `reverse`)
4. **Nunca** modifique hashes de integridade
5. **Nunca** ignore logs de auditoria

### 🔐 Segurança

1. Configure senhas fortes no banco de dados
2. Use HTTPS para conexões remotas
3. Limite acesso ao CLI para usuários autorizados
4. Revise logs de auditoria regularmente
5. Configure retention policies adequadas

---

## Troubleshooting

### Erro: "Database not configured"
**Solução**: Edite `.env` e configure `LEDGER_DB_URI`

### Erro: "Debits != Credits"
**Solução**: Verifique seu arquivo de entries - débitos devem igualar créditos

### Erro: "Account not found"
**Solução**: Crie a conta primeiro com `create-account`

### Erro: "Connection refused"
**Solução**: Verifique se o banco de dados está rodando

### Erro: "Permission denied"
**Solução**: Verifique permissões do usuário do banco de dados

---

## Próximos Passos

Depois de concluir este guia:

1. 📖 Leia o [README.md](README.md) completo
2. 🔍 Execute o Discovery Tool para seu caso específico
3. 📊 Configure seu plano de contas completo
4. 🔗 Integre com seus sistemas existentes
5. 👥 Treine sua equipe

---

## Ajuda

- **Documentação Completa**: Ver [README.md](README.md)
- **Exemplos**: Ver pasta `examples/`
- **Problemas**: Verifique logs de auditoria

---

**Pronto para começar!** 🚀

Execute o Discovery Tool agora:
```bash
python ledger_discovery_tool.py
```
