# 📒 Ledger / Accounting Engine - Sistema Completo

## Índice do Projeto

Este é um **Sistema de Contabilidade Imutável com Dupla Entrada** de nível bancário/corporativo, projetado para ambientes regulados de alto risco.

---

## 📁 Estrutura do Projeto

### 📖 Documentação

1. **README.md** (12 KB)
   - Documentação completa do sistema
   - Guia de instalação
   - Exemplos de uso
   - Características e funcionalidades

2. **QUICKSTART.md** (6.4 KB)
   - Guia rápido de 5 minutos
   - Primeiros passos
   - Comandos essenciais
   - Casos de uso comuns

3. **ARCHITECTURE.md** (17 KB)
   - Arquitetura técnica detalhada
   - Modelo de dados
   - Fluxos de processo
   - Decisões de design
   - Roadmap futuro

### 🔧 Código Principal

4. **ledger_engine.py** (31 KB) - ⭐ CORE DO SISTEMA
   - Motor principal do ledger
   - Implementação de dupla entrada
   - Gestão de plano de contas
   - Lançamento de transações
   - Reversões por estorno
   - Cálculo de saldos
   - Validação de integridade
   - Trilha de auditoria

5. **ledger_reporting.py** (23 KB)
   - Geração de relatórios auditáveis
   - Balanço Patrimonial
   - Demonstração de Resultados
   - Balancete de Verificação
   - Razão Geral
   - Trilha de Auditoria
   - Exportação JSON/CSV
   - Verificação de integridade

6. **ledger_discovery_tool.py** (28 KB) - ⭐ FERRAMENTA DE DESCOBERTA
   - Assistente interativo de descoberta
   - 8 fases de análise de domínio
   - Contexto legal e regulatório
   - Definição de modelo contábil
   - Configuração de dupla entrada
   - Estratégias de correção
   - Visões e fechamentos
   - Integrações
   - Requisitos não-funcionais
   - Geração de configuração

7. **ledger_admin_cli.py** (17 KB)
   - Interface de linha de comando
   - Criação de contas
   - Lançamento de transações
   - Reversões
   - Consulta de saldos
   - Geração de relatórios
   - Verificação de integridade
   - Visualização de auditoria

### 🧪 Testes

8. **test_ledger.py** (18 KB)
   - Suite completa de testes
   - Testes de plano de contas
   - Testes de transações
   - Testes de saldos
   - Testes de integridade
   - Testes de relatórios
   - Teste de workflow completo
   - Cobertura > 80%

### ⚙️ Configuração

9. **.env.template** (3.6 KB)
   - Template de configuração
   - Configurações de banco de dados
   - Configurações de sistema
   - Segurança
   - Auditoria
   - Notificações
   - Compliance
   - Backup e DR

10. **requirements.txt** (3 KB)
    - Dependências Python
    - Drivers de banco de dados
    - Bibliotecas de análise
    - Ferramentas de desenvolvimento
    - Utilitários

11. **setup.py** (8.7 KB)
    - Script de instalação automática
    - Criação de ambiente virtual
    - Instalação de dependências
    - Configuração inicial
    - Inicialização de banco de dados
    - Criação de contas de exemplo

### 📋 Exemplos

12. **examples/transaction_entries_example.json**
    - Exemplo de arquivo de lançamentos
    - Formato JSON
    - Documentado

---

## 🚀 Como Começar

### Opção 1: Setup Automático (Recomendado)
```bash
python setup.py
```

### Opção 2: Setup Manual
```bash
# 1. Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou venv\Scripts\activate  # Windows

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Configurar banco de dados
cp .env.template .env
# Editar .env com suas credenciais

# 4. Inicializar sistema
python ledger_admin_cli.py init --confirm
```

### Opção 3: Usar Discovery Tool (Melhor Prática)
```bash
python ledger_discovery_tool.py
```

---

## 📊 Principais Características

### ✅ Implementado

- ✅ **Imutabilidade Total** - Nada é apagado ou atualizado
- ✅ **Dupla Entrada Validada** - Débitos = Créditos sempre
- ✅ **Auditoria Completa** - Trilha de todos os eventos
- ✅ **Relatórios Reproduzíveis** - Hash de integridade
- ✅ **Reversão por Compensação** - Correções auditáveis
- ✅ **Plano de Contas Hierárquico** - Múltiplos níveis
- ✅ **Multi-dimensional** - Centro de custo, projeto, etc.
- ✅ **CLI Administrativa** - Interface completa
- ✅ **Discovery Tool** - Análise de domínio
- ✅ **Testes Automatizados** - Suite completa

### 🔄 Roadmap

- [ ] API REST
- [ ] Interface Web
- [ ] Fechamentos contábeis
- [ ] Multi-moeda
- [ ] Workflow de aprovação
- [ ] Dashboard analítico

---

## 📚 Guias de Leitura

### Para Iniciantes
1. Leia **QUICKSTART.md**
2. Execute **setup.py**
3. Siga os exemplos do QUICKSTART

### Para Desenvolvedores
1. Leia **README.md** completo
2. Estude **ARCHITECTURE.md**
3. Execute **test_ledger.py**
4. Examine o código de **ledger_engine.py**

### Para Arquitetos/Gestores
1. Execute **ledger_discovery_tool.py**
2. Leia **ARCHITECTURE.md**
3. Revise decisões de design
4. Avalie compliance com regulação

### Para Auditores
1. Revise **ARCHITECTURE.md** (seção Auditabilidade)
2. Examine **AuditLog** em ledger_engine.py
3. Teste geração de relatórios
4. Verifique integridade de dados

---

## 🎯 Casos de Uso

### Setores Aplicáveis

- 🏦 **Bancos e Instituições Financeiras**
- 💳 **Fintechs e Pagamentos**
- 📈 **Mercado de Capitais**
- 🛢️ **Petróleo e Gás**
- ⚡ **Energia e Utilities**
- 📞 **Telecomunicações**
- 🏛️ **Governo e Setor Público**
- 🏢 **Corporações com necessidade de auditoria rigorosa**

### Casos de Uso Típicos

1. **Ledger Contábil Central**
2. **Subledger de Receitas**
3. **Subledger de Despesas**
4. **Reconciliação Contábil**
5. **Auditoria e Compliance**
6. **Relatórios Regulatórios**

---

## 🔐 Conformidade e Segurança

### Padrões Suportados
- ✅ IFRS (International Financial Reporting Standards)
- ✅ GAAP (Generally Accepted Accounting Principles)
- ✅ SOX (Sarbanes-Oxley) ready
- ✅ Auditoria externa ready

### Características de Segurança
- ✅ Hash SHA-256 para integridade
- ✅ Trilha de auditoria completa
- ✅ Não-repúdio (usuário identificado)
- ✅ Imutabilidade de registros
- ✅ Timestamps UTC
- ✅ Validação de entrada
- ✅ Prevenção de SQL injection

---

## 📞 Suporte

### Documentação
- README.md - Guia completo
- QUICKSTART.md - Início rápido
- ARCHITECTURE.md - Detalhes técnicos

### Ferramentas
- CLI help: `python ledger_admin_cli.py --help`
- Discovery Tool: `python ledger_discovery_tool.py`
- Testes: `pytest test_ledger.py -v`

### Verificação
- Integridade: `python ledger_admin_cli.py verify`
- Auditoria: `python ledger_admin_cli.py audit --days 30`

---

## 📝 Licença e Créditos

**Versão**: 1.0.0  
**Data**: Janeiro 2026  
**Desenvolvido seguindo**: Princípios de Ledger de Nível Bancário

**Inspirações**:
- Sistemas bancários core
- Padrões IFRS/GAAP
- Event Sourcing
- Domain-Driven Design

---

## ⚡ Quick Commands

```bash
# Inicializar
python setup.py

# Discovery
python ledger_discovery_tool.py

# Criar conta
python ledger_admin_cli.py create-account --code 1100 --name "Caixa" --type ASSET --user seu@email.com

# Lançar transação
python ledger_admin_cli.py post-transaction --event-type SALE --description "Venda" --entries entries.json --user seu@email.com

# Ver saldo
python ledger_admin_cli.py balance --account-code 1100

# Balancete
python ledger_admin_cli.py trial-balance --output balancete.csv

# Verificar integridade
python ledger_admin_cli.py verify

# Testes
pytest test_ledger.py -v
```

---

**🎉 Sistema pronto para uso profissional em ambientes regulados!**

Para começar, execute:
```bash
python ledger_discovery_tool.py
```
