**`ledger_discovery_tool.py`**

É o ponto de entrada principal para começar a usar o sistema. Ele executa um assistente interativo que guia você por todo o processo de configuração e descoberta do domínio contábil.

---

**Mas se você quer executar operações do dia-a-dia:**

**`ledger_admin_cli.py`**

É o CLI administrativo que você usa para:

- Criar contas
- Lançar transações
- Consultar saldos
- Gerar relatórios
- Verificar integridade

---

**Resumindo:**

- **Primeira vez/Setup**: `ledger_discovery_tool.py`
- **Uso diário**: `ledger_admin_cli.py`

Os outros arquivos (`.py`) são **bibliotecas/módulos** que esses dois importam:

- `ledger_engine.py` - Motor do sistema
- `ledger_reporting.py` - Geração de relatórios
- `setup.py` - Instalação
- `test_ledger.py` - Testes
