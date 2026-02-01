-- ============================================================================
-- LEDGER SYSTEM - DATA SEEDER
-- ============================================================================
-- Script para popular o banco de dados com dados de exemplo
-- Tabelas populadas: CHART_OF_ACCOUNTS, TRANSACTIONS, JOURNAL_ENTRIES
-- Tabelas NÃO populadas: CLOSING_PERIODS (criado pelo sistema), AUDIT_LOG (gerado automaticamente)
-- 
-- Versão: 1.0.0
-- Data: Janeiro 2026
-- ============================================================================

USE `ledger_db`;

-- Desabilitar verificações temporariamente
SET FOREIGN_KEY_CHECKS = 0;

-- ============================================================================
-- LIMPAR DADOS EXISTENTES (CUIDADO EM PRODUÇÃO!)
-- ============================================================================

-- Comentar as linhas abaixo se quiser preservar dados existentes
DELETE FROM `journal_entries`;
DELETE FROM `transactions`;
DELETE FROM `chart_of_accounts`;

-- ============================================================================
-- SEEDER 1: CHART_OF_ACCOUNTS (Plano de Contas)
-- ============================================================================

-- Contas de Nível 1 (Raiz)
-- -------------------------

INSERT INTO `chart_of_accounts` 
    (`account_id`, `account_code`, `account_name`, `account_type`, `parent_account_id`, `level`, `is_active`, `description`, `created_at`, `created_by`, `version`)
VALUES
    -- ATIVOS
    ('10000000-0000-0000-0000-000000000001', '1000', 'ATIVOS', 'ASSET', NULL, 1, TRUE, 
     'Grupo principal de contas de ativos', UTC_TIMESTAMP(), 'SEEDER', 1),
    
    -- PASSIVOS
    ('20000000-0000-0000-0000-000000000001', '2000', 'PASSIVOS', 'LIABILITY', NULL, 1, TRUE, 
     'Grupo principal de contas de passivos', UTC_TIMESTAMP(), 'SEEDER', 1),
    
    -- PATRIMÔNIO LÍQUIDO
    ('30000000-0000-0000-0000-000000000001', '3000', 'PATRIMÔNIO LÍQUIDO', 'EQUITY', NULL, 1, TRUE, 
     'Grupo principal de patrimônio líquido', UTC_TIMESTAMP(), 'SEEDER', 1),
    
    -- RECEITAS
    ('40000000-0000-0000-0000-000000000001', '4000', 'RECEITAS', 'REVENUE', NULL, 1, TRUE, 
     'Grupo principal de receitas', UTC_TIMESTAMP(), 'SEEDER', 1),
    
    -- DESPESAS
    ('50000000-0000-0000-0000-000000000001', '5000', 'DESPESAS', 'EXPENSE', NULL, 1, TRUE, 
     'Grupo principal de despesas', UTC_TIMESTAMP(), 'SEEDER', 1);


-- Contas de Nível 2 (Subgrupos)
-- ------------------------------

INSERT INTO `chart_of_accounts` 
    (`account_id`, `account_code`, `account_name`, `account_type`, `parent_account_id`, `level`, `is_active`, `description`, `created_at`, `created_by`, `version`)
VALUES
    -- ATIVOS - Subgrupos
    ('11000000-0000-0000-0000-000000000001', '1100', 'Ativo Circulante', 'ASSET', '10000000-0000-0000-0000-000000000001', 2, TRUE, 
     'Ativos de curto prazo', UTC_TIMESTAMP(), 'SEEDER', 1),
    ('12000000-0000-0000-0000-000000000001', '1200', 'Ativo Não Circulante', 'ASSET', '10000000-0000-0000-0000-000000000001', 2, TRUE, 
     'Ativos de longo prazo', UTC_TIMESTAMP(), 'SEEDER', 1),
    
    -- PASSIVOS - Subgrupos
    ('21000000-0000-0000-0000-000000000001', '2100', 'Passivo Circulante', 'LIABILITY', '20000000-0000-0000-0000-000000000001', 2, TRUE, 
     'Obrigações de curto prazo', UTC_TIMESTAMP(), 'SEEDER', 1),
    ('22000000-0000-0000-0000-000000000001', '2200', 'Passivo Não Circulante', 'LIABILITY', '20000000-0000-0000-0000-000000000001', 2, TRUE, 
     'Obrigações de longo prazo', UTC_TIMESTAMP(), 'SEEDER', 1),
    
    -- PATRIMÔNIO LÍQUIDO - Subgrupos
    ('31000000-0000-0000-0000-000000000001', '3100', 'Capital Social', 'EQUITY', '30000000-0000-0000-0000-000000000001', 2, TRUE, 
     'Capital investido pelos sócios', UTC_TIMESTAMP(), 'SEEDER', 1),
    ('32000000-0000-0000-0000-000000000001', '3200', 'Reservas', 'EQUITY', '30000000-0000-0000-0000-000000000001', 2, TRUE, 
     'Reservas de lucros', UTC_TIMESTAMP(), 'SEEDER', 1),
    
    -- RECEITAS - Subgrupos
    ('41000000-0000-0000-0000-000000000001', '4100', 'Receitas Operacionais', 'REVENUE', '40000000-0000-0000-0000-000000000001', 2, TRUE, 
     'Receitas das atividades principais', UTC_TIMESTAMP(), 'SEEDER', 1),
    ('42000000-0000-0000-0000-000000000001', '4200', 'Receitas Financeiras', 'REVENUE', '40000000-0000-0000-0000-000000000001', 2, TRUE, 
     'Receitas de aplicações financeiras', UTC_TIMESTAMP(), 'SEEDER', 1),
    
    -- DESPESAS - Subgrupos
    ('51000000-0000-0000-0000-000000000001', '5100', 'Custos Operacionais', 'EXPENSE', '50000000-0000-0000-0000-000000000001', 2, TRUE, 
     'Custos diretos da operação', UTC_TIMESTAMP(), 'SEEDER', 1),
    ('52000000-0000-0000-0000-000000000001', '5200', 'Despesas Administrativas', 'EXPENSE', '50000000-0000-0000-0000-000000000001', 2, TRUE, 
     'Despesas gerais e administrativas', UTC_TIMESTAMP(), 'SEEDER', 1),
    ('53000000-0000-0000-0000-000000000001', '5300', 'Despesas Financeiras', 'EXPENSE', '50000000-0000-0000-0000-000000000001', 2, TRUE, 
     'Juros e encargos financeiros', UTC_TIMESTAMP(), 'SEEDER', 1);


-- Contas de Nível 3 (Contas Analíticas - Detalhadas)
-- ----------------------------------------------------

INSERT INTO `chart_of_accounts` 
    (`account_id`, `account_code`, `account_name`, `account_type`, `parent_account_id`, `level`, `is_active`, `description`, `created_at`, `created_by`, `version`)
VALUES
    -- ATIVO CIRCULANTE - Contas detalhadas
    ('11010000-0000-0000-0000-000000000001', '1101', 'Caixa Geral', 'ASSET', '11000000-0000-0000-0000-000000000001', 3, TRUE, 
     'Dinheiro em espécie no caixa', UTC_TIMESTAMP(), 'SEEDER', 1),
    ('11020000-0000-0000-0000-000000000001', '1102', 'Bancos - Conta Corrente', 'ASSET', '11000000-0000-0000-0000-000000000001', 3, TRUE, 
     'Saldo em conta corrente bancária', UTC_TIMESTAMP(), 'SEEDER', 1),
    ('11030000-0000-0000-0000-000000000001', '1103', 'Aplicações Financeiras', 'ASSET', '11000000-0000-0000-0000-000000000001', 3, TRUE, 
     'Investimentos de curto prazo', UTC_TIMESTAMP(), 'SEEDER', 1),
    ('11040000-0000-0000-0000-000000000001', '1104', 'Clientes / Contas a Receber', 'ASSET', '11000000-0000-0000-0000-000000000001', 3, TRUE, 
     'Valores a receber de clientes', UTC_TIMESTAMP(), 'SEEDER', 1),
    ('11050000-0000-0000-0000-000000000001', '1105', 'Estoque de Mercadorias', 'ASSET', '11000000-0000-0000-0000-000000000001', 3, TRUE, 
     'Mercadorias para revenda', UTC_TIMESTAMP(), 'SEEDER', 1),
    
    -- ATIVO NÃO CIRCULANTE - Contas detalhadas
    ('12010000-0000-0000-0000-000000000001', '1201', 'Imóveis', 'ASSET', '12000000-0000-0000-0000-000000000001', 3, TRUE, 
     'Propriedades imobiliárias', UTC_TIMESTAMP(), 'SEEDER', 1),
    ('12020000-0000-0000-0000-000000000001', '1202', 'Veículos', 'ASSET', '12000000-0000-0000-0000-000000000001', 3, TRUE, 
     'Frota de veículos', UTC_TIMESTAMP(), 'SEEDER', 1),
    ('12030000-0000-0000-0000-000000000001', '1203', 'Equipamentos', 'ASSET', '12000000-0000-0000-0000-000000000001', 3, TRUE, 
     'Máquinas e equipamentos', UTC_TIMESTAMP(), 'SEEDER', 1),
    ('12040000-0000-0000-0000-000000000001', '1204', 'Móveis e Utensílios', 'ASSET', '12000000-0000-0000-0000-000000000001', 3, TRUE, 
     'Mobiliário do escritório', UTC_TIMESTAMP(), 'SEEDER', 1),
    
    -- PASSIVO CIRCULANTE - Contas detalhadas
    ('21010000-0000-0000-0000-000000000001', '2101', 'Fornecedores / Contas a Pagar', 'LIABILITY', '21000000-0000-0000-0000-000000000001', 3, TRUE, 
     'Valores a pagar a fornecedores', UTC_TIMESTAMP(), 'SEEDER', 1),
    ('21020000-0000-0000-0000-000000000001', '2102', 'Salários a Pagar', 'LIABILITY', '21000000-0000-0000-0000-000000000001', 3, TRUE, 
     'Folha de pagamento pendente', UTC_TIMESTAMP(), 'SEEDER', 1),
    ('21030000-0000-0000-0000-000000000001', '2103', 'Impostos a Recolher', 'LIABILITY', '21000000-0000-0000-0000-000000000001', 3, TRUE, 
     'Tributos a pagar', UTC_TIMESTAMP(), 'SEEDER', 1),
    ('21040000-0000-0000-0000-000000000001', '2104', 'Empréstimos Bancários CP', 'LIABILITY', '21000000-0000-0000-0000-000000000001', 3, TRUE, 
     'Empréstimos de curto prazo', UTC_TIMESTAMP(), 'SEEDER', 1),
    
    -- PASSIVO NÃO CIRCULANTE - Contas detalhadas
    ('22010000-0000-0000-0000-000000000001', '2201', 'Financiamentos LP', 'LIABILITY', '22000000-0000-0000-0000-000000000001', 3, TRUE, 
     'Financiamentos de longo prazo', UTC_TIMESTAMP(), 'SEEDER', 1),
    ('22020000-0000-0000-0000-000000000001', '2202', 'Debêntures', 'LIABILITY', '22000000-0000-0000-0000-000000000001', 3, TRUE, 
     'Títulos de dívida emitidos', UTC_TIMESTAMP(), 'SEEDER', 1),
    
    -- PATRIMÔNIO LÍQUIDO - Contas detalhadas
    ('31010000-0000-0000-0000-000000000001', '3101', 'Capital Social Integralizado', 'EQUITY', '31000000-0000-0000-0000-000000000001', 3, TRUE, 
     'Capital efetivamente integralizado', UTC_TIMESTAMP(), 'SEEDER', 1),
    ('32010000-0000-0000-0000-000000000001', '3201', 'Reserva Legal', 'EQUITY', '32000000-0000-0000-0000-000000000001', 3, TRUE, 
     'Reserva obrigatória por lei', UTC_TIMESTAMP(), 'SEEDER', 1),
    ('32020000-0000-0000-0000-000000000001', '3202', 'Lucros Acumulados', 'EQUITY', '32000000-0000-0000-0000-000000000001', 3, TRUE, 
     'Lucros retidos na empresa', UTC_TIMESTAMP(), 'SEEDER', 1),
    
    -- RECEITAS OPERACIONAIS - Contas detalhadas
    ('41010000-0000-0000-0000-000000000001', '4101', 'Receita de Vendas à Vista', 'REVENUE', '41000000-0000-0000-0000-000000000001', 3, TRUE, 
     'Vendas recebidas imediatamente', UTC_TIMESTAMP(), 'SEEDER', 1),
    ('41020000-0000-0000-0000-000000000001', '4102', 'Receita de Vendas a Prazo', 'REVENUE', '41000000-0000-0000-0000-000000000001', 3, TRUE, 
     'Vendas com pagamento futuro', UTC_TIMESTAMP(), 'SEEDER', 1),
    ('41030000-0000-0000-0000-000000000001', '4103', 'Receita de Serviços', 'REVENUE', '41000000-0000-0000-0000-000000000001', 3, TRUE, 
     'Prestação de serviços', UTC_TIMESTAMP(), 'SEEDER', 1),
    
    -- RECEITAS FINANCEIRAS - Contas detalhadas
    ('42010000-0000-0000-0000-000000000001', '4201', 'Juros Recebidos', 'REVENUE', '42000000-0000-0000-0000-000000000001', 3, TRUE, 
     'Rendimentos de aplicações', UTC_TIMESTAMP(), 'SEEDER', 1),
    ('42020000-0000-0000-0000-000000000001', '4202', 'Descontos Obtidos', 'REVENUE', '42000000-0000-0000-0000-000000000001', 3, TRUE, 
     'Descontos em pagamentos antecipados', UTC_TIMESTAMP(), 'SEEDER', 1),
    
    -- CUSTOS OPERACIONAIS - Contas detalhadas
    ('51010000-0000-0000-0000-000000000001', '5101', 'Custo de Mercadorias Vendidas (CMV)', 'EXPENSE', '51000000-0000-0000-0000-000000000001', 3, TRUE, 
     'Custo direto das vendas', UTC_TIMESTAMP(), 'SEEDER', 1),
    ('51020000-0000-0000-0000-000000000001', '5102', 'Custo de Serviços Prestados', 'EXPENSE', '51000000-0000-0000-0000-000000000001', 3, TRUE, 
     'Custo direto dos serviços', UTC_TIMESTAMP(), 'SEEDER', 1),
    
    -- DESPESAS ADMINISTRATIVAS - Contas detalhadas
    ('52010000-0000-0000-0000-000000000001', '5201', 'Salários e Encargos', 'EXPENSE', '52000000-0000-0000-0000-000000000001', 3, TRUE, 
     'Folha de pagamento administrativa', UTC_TIMESTAMP(), 'SEEDER', 1),
    ('52020000-0000-0000-0000-000000000001', '5202', 'Aluguel', 'EXPENSE', '52000000-0000-0000-0000-000000000001', 3, TRUE, 
     'Aluguel do escritório/loja', UTC_TIMESTAMP(), 'SEEDER', 1),
    ('52030000-0000-0000-0000-000000000001', '5203', 'Energia Elétrica', 'EXPENSE', '52000000-0000-0000-0000-000000000001', 3, TRUE, 
     'Consumo de energia', UTC_TIMESTAMP(), 'SEEDER', 1),
    ('52040000-0000-0000-0000-000000000001', '5204', 'Telefone e Internet', 'EXPENSE', '52000000-0000-0000-0000-000000000001', 3, TRUE, 
     'Serviços de telecomunicações', UTC_TIMESTAMP(), 'SEEDER', 1),
    ('52050000-0000-0000-0000-000000000001', '5205', 'Material de Escritório', 'EXPENSE', '52000000-0000-0000-0000-000000000001', 3, TRUE, 
     'Papelaria e suprimentos', UTC_TIMESTAMP(), 'SEEDER', 1),
    ('52060000-0000-0000-0000-000000000001', '5206', 'Manutenção e Reparos', 'EXPENSE', '52000000-0000-0000-0000-000000000001', 3, TRUE, 
     'Manutenção de equipamentos', UTC_TIMESTAMP(), 'SEEDER', 1),
    ('52070000-0000-0000-0000-000000000001', '5207', 'Depreciação', 'EXPENSE', '52000000-0000-0000-0000-000000000001', 3, TRUE, 
     'Depreciação de ativos', UTC_TIMESTAMP(), 'SEEDER', 1),
    
    -- DESPESAS FINANCEIRAS - Contas detalhadas
    ('53010000-0000-0000-0000-000000000001', '5301', 'Juros Pagos', 'EXPENSE', '53000000-0000-0000-0000-000000000001', 3, TRUE, 
     'Juros de empréstimos e financiamentos', UTC_TIMESTAMP(), 'SEEDER', 1),
    ('53020000-0000-0000-0000-000000000001', '5302', 'Tarifas Bancárias', 'EXPENSE', '53000000-0000-0000-0000-000000000001', 3, TRUE, 
     'Tarifas e taxas bancárias', UTC_TIMESTAMP(), 'SEEDER', 1),
    ('53030000-0000-0000-0000-000000000001', '5303', 'Descontos Concedidos', 'EXPENSE', '53000000-0000-0000-0000-000000000001', 3, TRUE, 
     'Descontos dados a clientes', UTC_TIMESTAMP(), 'SEEDER', 1);


-- ============================================================================
-- SEEDER 2: TRANSACTIONS & JOURNAL_ENTRIES (Transações de Exemplo)
-- ============================================================================

-- Transação 1: Capital Inicial
-- -----------------------------
INSERT INTO `transactions` 
    (`transaction_id`, `transaction_number`, `transaction_date`, `posting_date`, `business_event_type`, `business_key`, `description`, `status`, `created_at`, `created_by`, `source_system`, `transaction_hash`)
VALUES
    ('T0000001-0000-0000-0000-000000000001', '20260101-000001', '2026-01-01 08:00:00', '2026-01-01 08:00:00', 
     'CAPITAL_INICIAL', 'CAP-2026-001', 'Integralização de capital social inicial', 'POSTED', 
     UTC_TIMESTAMP(), 'admin@empresa.com', 'SEEDER_SYSTEM', 
     'a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6');

INSERT INTO `journal_entries` 
    (`entry_id`, `transaction_id`, `entry_number`, `account_id`, `account_code`, `entry_type`, `amount`, `currency`, `memo`, `created_at`)
VALUES
    ('E0000001-0000-0001', 'T0000001-0000-0000-0000-000000000001', 1, 
     '11020000-0000-0000-0000-000000000001', '1102', 'DEBIT', 100000.00, 'AOA', 
     'Entrada de capital em conta corrente', UTC_TIMESTAMP()),
    ('E0000001-0000-0002', 'T0000001-0000-0000-0000-000000000001', 2, 
     '31010000-0000-0000-0000-000000000001', '3101', 'CREDIT', 100000.00, 'AOA', 
     'Capital social integralizado', UTC_TIMESTAMP());


-- Transação 2: Compra de Estoque à Vista
-- ----------------------------------------
INSERT INTO `transactions` 
    (`transaction_id`, `transaction_number`, `transaction_date`, `posting_date`, `business_event_type`, `business_key`, `description`, `status`, `created_at`, `created_by`, `source_system`, `transaction_hash`)
VALUES
    ('T0000002-0000-0000-0000-000000000001', '20260102-000001', '2026-01-02 10:30:00', '2026-01-02 10:30:00', 
     'PURCHASE', 'COMP-2026-001', 'Compra de mercadorias para estoque', 'POSTED', 
     UTC_TIMESTAMP(), 'compras@empresa.com', 'SEEDER_SYSTEM', 
     'b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a1');

INSERT INTO `journal_entries` 
    (`entry_id`, `transaction_id`, `entry_number`, `account_id`, `account_code`, `entry_type`, `amount`, `currency`, `cost_center`, `memo`, `created_at`)
VALUES
    ('E0000002-0000-0001', 'T0000002-0000-0000-0000-000000000001', 1, 
     '11050000-0000-0000-0000-000000000001', '1105', 'DEBIT', 25000.00, 'AOA', 
     'CC-COMERCIAL', 'Aquisição de mercadorias', UTC_TIMESTAMP()),
    ('E0000002-0000-0002', 'T0000002-0000-0000-0000-000000000001', 2, 
     '11020000-0000-0000-0000-000000000001', '1102', 'CREDIT', 25000.00, 'AOA', 
     'CC-COMERCIAL', 'Pagamento à vista via banco', UTC_TIMESTAMP());


-- Transação 3: Venda à Vista
-- ---------------------------
INSERT INTO `transactions` 
    (`transaction_id`, `transaction_number`, `transaction_date`, `posting_date`, `business_event_type`, `business_key`, `reference_number`, `description`, `status`, `created_at`, `created_by`, `source_system`, `transaction_hash`)
VALUES
    ('T0000003-0000-0000-0000-000000000001', '20260105-000001', '2026-01-05 14:15:00', '2026-01-05 14:15:00', 
     'SALE', 'VEND-2026-001', 'NF-00001', 'Venda de produtos à vista', 'POSTED', 
     UTC_TIMESTAMP(), 'vendas@empresa.com', 'SEEDER_SYSTEM', 
     'c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a1b2');

INSERT INTO `journal_entries` 
    (`entry_id`, `transaction_id`, `entry_number`, `account_id`, `account_code`, `entry_type`, `amount`, `currency`, `cost_center`, `business_unit`, `memo`, `created_at`)
VALUES
    ('E0000003-0000-0001', 'T0000003-0000-0000-0000-000000000001', 1, 
     '11010000-0000-0000-0000-000000000001', '1101', 'DEBIT', 15000.00, 'AOA', 
     'CC-COMERCIAL', 'BU-VENDAS', 'Recebimento em dinheiro', UTC_TIMESTAMP()),
    ('E0000003-0000-0002', 'T0000003-0000-0000-0000-000000000001', 2, 
     '41010000-0000-0000-0000-000000000001', '4101', 'CREDIT', 15000.00, 'AOA', 
     'CC-COMERCIAL', 'BU-VENDAS', 'Receita de venda à vista', UTC_TIMESTAMP());


-- Transação 4: Registro do CMV (Custo da Venda)
-- ----------------------------------------------
INSERT INTO `transactions` 
    (`transaction_id`, `transaction_number`, `transaction_date`, `posting_date`, `business_event_type`, `business_key`, `reference_number`, `description`, `status`, `created_at`, `created_by`, `source_system`, `transaction_hash`)
VALUES
    ('T0000004-0000-0000-0000-000000000001', '20260105-000002', '2026-01-05 14:15:00', '2026-01-05 14:15:00', 
     'CMV', 'CMV-2026-001', 'NF-00001', 'Baixa de estoque - CMV da venda', 'POSTED', 
     UTC_TIMESTAMP(), 'vendas@empresa.com', 'SEEDER_SYSTEM', 
     'd4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a1b2c3');

INSERT INTO `journal_entries` 
    (`entry_id`, `transaction_id`, `entry_number`, `account_id`, `account_code`, `entry_type`, `amount`, `currency`, `cost_center`, `memo`, `created_at`)
VALUES
    ('E0000004-0000-0001', 'T0000004-0000-0000-0000-000000000001', 1, 
     '51010000-0000-0000-0000-000000000001', '5101', 'DEBIT', 9000.00, 'AOA', 
     'CC-COMERCIAL', 'Custo das mercadorias vendidas', UTC_TIMESTAMP()),
    ('E0000004-0000-0002', 'T0000004-0000-0000-0000-000000000001', 2, 
     '11050000-0000-0000-0000-000000000001', '1105', 'CREDIT', 9000.00, 'AOA', 
     'CC-COMERCIAL', 'Baixa do estoque', UTC_TIMESTAMP());


-- Transação 5: Venda a Prazo
-- ---------------------------
INSERT INTO `transactions` 
    (`transaction_id`, `transaction_number`, `transaction_date`, `posting_date`, `business_event_type`, `business_key`, `reference_number`, `description`, `status`, `created_at`, `created_by`, `source_system`, `transaction_hash`)
VALUES
    ('T0000005-0000-0000-0000-000000000001', '20260108-000001', '2026-01-08 11:00:00', '2026-01-08 11:00:00', 
     'SALE_CREDIT', 'VEND-2026-002', 'NF-00002', 'Venda a prazo (30 dias)', 'POSTED', 
     UTC_TIMESTAMP(), 'vendas@empresa.com', 'SEEDER_SYSTEM', 
     'e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a1b2c3d4');

INSERT INTO `journal_entries` 
    (`entry_id`, `transaction_id`, `entry_number`, `account_id`, `account_code`, `entry_type`, `amount`, `currency`, `cost_center`, `business_unit`, `memo`, `created_at`)
VALUES
    ('E0000005-0000-0001', 'T0000005-0000-0000-0000-000000000001', 1, 
     '11040000-0000-0000-0000-000000000001', '1104', 'DEBIT', 20000.00, 'AOA', 
     'CC-COMERCIAL', 'BU-VENDAS', 'Contas a receber - Cliente ABC', UTC_TIMESTAMP()),
    ('E0000005-0000-0002', 'T0000005-0000-0000-0000-000000000001', 2, 
     '41020000-0000-0000-0000-000000000001', '4102', 'CREDIT', 20000.00, 'AOA', 
     'CC-COMERCIAL', 'BU-VENDAS', 'Receita de venda a prazo', UTC_TIMESTAMP());


-- Transação 6: Pagamento de Aluguel
-- ----------------------------------
INSERT INTO `transactions` 
    (`transaction_id`, `transaction_number`, `transaction_date`, `posting_date`, `business_event_type`, `business_key`, `reference_number`, `description`, `status`, `created_at`, `created_by`, `source_system`, `transaction_hash`)
VALUES
    ('T0000006-0000-0000-0000-000000000001', '20260110-000001', '2026-01-10 09:00:00', '2026-01-10 09:00:00', 
     'PAYMENT', 'PAG-2026-001', 'RECIBO-ALG-JAN', 'Pagamento de aluguel - Janeiro 2026', 'POSTED', 
     UTC_TIMESTAMP(), 'financeiro@empresa.com', 'SEEDER_SYSTEM', 
     'f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a1b2c3d4e5');

INSERT INTO `journal_entries` 
    (`entry_id`, `transaction_id`, `entry_number`, `account_id`, `account_code`, `entry_type`, `amount`, `currency`, `cost_center`, `memo`, `created_at`)
VALUES
    ('E0000006-0000-0001', 'T0000006-0000-0000-0000-000000000001', 1, 
     '52020000-0000-0000-0000-000000000001', '5202', 'DEBIT', 5000.00, 'AOA', 
     'CC-ADMIN', 'Despesa de aluguel mensal', UTC_TIMESTAMP()),
    ('E0000006-0000-0002', 'T0000006-0000-0000-0000-000000000001', 2, 
     '11020000-0000-0000-0000-000000000001', '1102', 'CREDIT', 5000.00, 'AOA', 
     'CC-ADMIN', 'Pagamento via transferência bancária', UTC_TIMESTAMP());


-- Transação 7: Pagamento de Salários
-- -----------------------------------
INSERT INTO `transactions` 
    (`transaction_id`, `transaction_number`, `transaction_date`, `posting_date`, `business_event_type`, `business_key`, `description`, `status`, `created_at`, `created_by`, `source_system`, `transaction_hash`)
VALUES
    ('T0000007-0000-0000-0000-000000000001', '20260115-000001', '2026-01-15 16:00:00', '2026-01-15 16:00:00', 
     'PAYROLL', 'FOLHA-2026-01', 'Pagamento de salários - Janeiro 2026', 'POSTED', 
     UTC_TIMESTAMP(), 'rh@empresa.com', 'SEEDER_SYSTEM', 
     'g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a1b2c3d4e5f6');

INSERT INTO `journal_entries` 
    (`entry_id`, `transaction_id`, `entry_number`, `account_id`, `account_code`, `entry_type`, `amount`, `currency`, `cost_center`, `memo`, `created_at`)
VALUES
    ('E0000007-0000-0001', 'T0000007-0000-0000-0000-000000000001', 1, 
     '52010000-0000-0000-0000-000000000001', '5201', 'DEBIT', 35000.00, 'AOA', 
     'CC-ADMIN', 'Salários e encargos do mês', UTC_TIMESTAMP()),
    ('E0000007-0000-0002', 'T0000007-0000-0000-0000-000000000001', 2, 
     '11020000-0000-0000-0000-000000000001', '1102', 'CREDIT', 35000.00, 'AOA', 
     'CC-ADMIN', 'Pagamento via banco', UTC_TIMESTAMP());


-- Transação 8: Pagamento de Energia Elétrica
-- -------------------------------------------
INSERT INTO `transactions` 
    (`transaction_id`, `transaction_number`, `transaction_date`, `posting_date`, `business_event_type`, `business_key`, `reference_number`, `description`, `status`, `created_at`, `created_by`, `source_system`, `transaction_hash`)
VALUES
    ('T0000008-0000-0000-0000-000000000001', '20260120-000001', '2026-01-20 10:30:00', '2026-01-20 10:30:00', 
     'PAYMENT', 'PAG-2026-002', 'FATURA-ENER-JAN', 'Pagamento de energia elétrica', 'POSTED', 
     UTC_TIMESTAMP(), 'financeiro@empresa.com', 'SEEDER_SYSTEM', 
     'h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a1b2c3d4e5f6g7');

INSERT INTO `journal_ENTRIES` 
    (`entry_id`, `transaction_id`, `entry_number`, `account_id`, `account_code`, `entry_type`, `amount`, `currency`, `cost_center`, `memo`, `created_at`)
VALUES
    ('E0000008-0000-0001', 'T0000008-0000-0000-0000-000000000001', 1, 
     '52030000-0000-0000-0000-000000000001', '5203', 'DEBIT', 1500.00, 'AOA', 
     'CC-ADMIN', 'Consumo de energia do mês', UTC_TIMESTAMP()),
    ('E0000008-0000-0002', 'T0000008-0000-0000-0000-000000000001', 2, 
     '11020000-0000-0000-0000-000000000001', '1102', 'CREDIT', 1500.00, 'AOA', 
     'CC-ADMIN', 'Pagamento via débito automático', UTC_TIMESTAMP());


-- Transação 9: Recebimento de Cliente (Venda a Prazo)
-- ----------------------------------------------------
INSERT INTO `transactions` 
    (`transaction_id`, `transaction_number`, `transaction_date`, `posting_date`, `business_event_type`, `business_key`, `reference_number`, `description`, `status`, `created_at`, `created_by`, `source_system`, `transaction_hash`)
VALUES
    ('T0000009-0000-0000-0000-000000000001', '20260125-000001', '2026-01-25 15:45:00', '2026-01-25 15:45:00', 
     'RECEIPT', 'REC-2026-001', 'VEND-2026-002', 'Recebimento de cliente - Venda NF-00002', 'POSTED', 
     UTC_TIMESTAMP(), 'financeiro@empresa.com', 'SEEDER_SYSTEM', 
     'i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a1b2c3d4e5f6g7h8');

INSERT INTO `journal_entries` 
    (`entry_id`, `transaction_id`, `entry_number`, `account_id`, `account_code`, `entry_type`, `amount`, `currency`, `business_unit`, `memo`, `created_at`)
VALUES
    ('E0000009-0000-0001', 'T0000009-0000-0000-0000-000000000001', 1, 
     '11020000-0000-0000-0000-000000000001', '1102', 'DEBIT', 20000.00, 'AOA', 
     'BU-VENDAS', 'Recebimento via transferência bancária', UTC_TIMESTAMP()),
    ('E0000009-0000-0002', 'T0000009-0000-0000-0000-000000000001', 2, 
     '11040000-0000-0000-0000-000000000001', '1104', 'CREDIT', 20000.00, 'AOA', 
     'BU-VENDAS', 'Baixa de contas a receber - Cliente ABC', UTC_TIMESTAMP());


-- Transação 10: Compra de Equipamento a Prazo
-- --------------------------------------------
INSERT INTO `transactions` 
    (`transaction_id`, `transaction_number`, `transaction_date`, `posting_date`, `business_event_type`, `business_key`, `reference_number`, `description`, `status`, `created_at`, `created_by`, `source_system`, `transaction_hash`)
VALUES
    ('T0000010-0000-0000-0000-000000000001', '20260128-000001', '2026-01-28 13:00:00', '2026-01-28 13:00:00', 
     'PURCHASE_ASSET', 'COMP-EQUIP-001', 'NF-EQUIP-001', 'Aquisição de computador - 3x sem juros', 'POSTED', 
     UTC_TIMESTAMP(), 'compras@empresa.com', 'SEEDER_SYSTEM', 
     'j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a1b2c3d4e5f6g7h8i9');

INSERT INTO `journal_entries` 
    (`entry_id`, `transaction_id`, `entry_number`, `account_id`, `account_code`, `entry_type`, `amount`, `currency`, `cost_center`, `memo`, `created_at`)
VALUES
    ('E0000010-0000-0001', 'T0000010-0000-0000-0000-000000000001', 1, 
     '12030000-0000-0000-0000-000000000001', '1203', 'DEBIT', 12000.00, 'AOA', 
     'CC-TI', 'Aquisição de equipamento de informática', UTC_TIMESTAMP()),
    ('E0000010-0000-0002', 'T0000010-0000-0000-0000-000000000001', 2, 
     '21010000-0000-0000-0000-000000000001', '2101', 'CREDIT', 12000.00, 'AOA', 
     'CC-TI', 'Fornecedor a pagar - 3 parcelas', UTC_TIMESTAMP());


-- ============================================================================
-- VERIFICAÇÕES E RESUMO
-- ============================================================================

-- Verificar total de contas criadas
SELECT 
    'CHART_OF_ACCOUNTS' AS Tabela,
    COUNT(*) AS Total_Registros,
    COUNT(DISTINCT account_type) AS Tipos_Conta,
    MAX(level) AS Niveis_Hierarquia
FROM chart_of_accounts;

-- Verificar transações criadas
SELECT 
    'TRANSACTIONS' AS Tabela,
    COUNT(*) AS Total_Transacoes,
    MIN(transaction_date) AS Primeira_Transacao,
    MAX(transaction_date) AS Ultima_Transacao
FROM transactions
WHERE status = 'POSTED';

-- Verificar lançamentos criados
SELECT 
    'JOURNAL_ENTRIES' AS Tabela,
    COUNT(*) AS Total_Lancamentos,
    SUM(CASE WHEN entry_type = 'DEBIT' THEN amount ELSE 0 END) AS Total_Debitos,
    SUM(CASE WHEN entry_type = 'CREDIT' THEN amount ELSE 0 END) AS Total_Creditos,
    (SUM(CASE WHEN entry_type = 'DEBIT' THEN amount ELSE 0 END) = 
     SUM(CASE WHEN entry_type = 'CREDIT' THEN amount ELSE 0 END)) AS Balanceado
FROM journal_entries;

-- Verificar balancete resumido
SELECT 
    account_type AS Tipo_Conta,
    COUNT(*) AS Qtd_Contas_Com_Movimento,
    SUM(total_debits) AS Total_Debitos,
    SUM(total_credits) AS Total_Creditos,
    SUM(balance) AS Saldo_Total
FROM v_account_balances
GROUP BY account_type
ORDER BY account_type;

-- Restaurar verificações
SET FOREIGN_KEY_CHECKS = 1;

-- ============================================================================
-- FIM DO SEEDER
-- ============================================================================

SELECT 
    'Seeder executado com sucesso!' AS Status,
    (SELECT COUNT(*) FROM chart_of_accounts) AS Contas_Criadas,
    (SELECT COUNT(*) FROM transactions) AS Transacoes_Criadas,
    (SELECT COUNT(*) FROM journal_entries) AS Lancamentos_Criados;
