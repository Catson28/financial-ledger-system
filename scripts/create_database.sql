-- ============================================================================
-- LEDGER / ACCOUNTING ENGINE - DATABASE SCHEMA
-- ============================================================================
-- Sistema de Contabilidade Imutável com Dupla Entrada
-- Versão: 1.0.0
-- Data: Janeiro 2026
-- Database: MySQL 8.0+ / MariaDB 10.5+
-- ============================================================================

-- Configurações iniciais
SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='TRADITIONAL,ALLOW_INVALID_DATES';

-- ============================================================================
-- CRIAR DATABASE (se não existir)
-- ============================================================================

CREATE DATABASE IF NOT EXISTS `ledger_db` 
    DEFAULT CHARACTER SET utf8mb4 
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE `ledger_db`;

-- ============================================================================
-- TABELA: chart_of_accounts
-- Plano de Contas Hierárquico
-- ============================================================================

DROP TABLE IF EXISTS `chart_of_accounts`;

CREATE TABLE `chart_of_accounts` (
    -- Chaves
    `account_id` VARCHAR(36) NOT NULL COMMENT 'UUID único da conta',
    `account_code` VARCHAR(50) NOT NULL COMMENT 'Código único da conta',
    
    -- Dados da Conta
    `account_name` VARCHAR(200) NOT NULL COMMENT 'Nome descritivo da conta',
    `account_type` VARCHAR(20) NOT NULL COMMENT 'Tipo: ASSET, LIABILITY, EQUITY, REVENUE, EXPENSE',
    `parent_account_id` VARCHAR(36) NULL COMMENT 'Referência à conta pai (hierarquia)',
    `level` DECIMAL(2,0) NOT NULL COMMENT 'Nível na hierarquia (1-99)',
    `is_active` BOOLEAN NOT NULL DEFAULT TRUE COMMENT 'Status ativo/inativo',
    `description` TEXT NULL COMMENT 'Descrição detalhada da conta',
    
    -- Auditoria
    `created_at` DATETIME NOT NULL COMMENT 'Data/hora de criação (UTC)',
    `created_by` VARCHAR(200) NOT NULL COMMENT 'Usuário criador',
    `version` DECIMAL(10,0) NOT NULL DEFAULT 1 COMMENT 'Versão do registro',
    
    -- Constraints
    PRIMARY KEY (`account_id`),
    UNIQUE KEY `uk_account_code` (`account_code`),
    CONSTRAINT `fk_parent_account` 
        FOREIGN KEY (`parent_account_id`) 
        REFERENCES `chart_of_accounts` (`account_id`)
        ON DELETE RESTRICT 
        ON UPDATE CASCADE,
    CONSTRAINT `chk_account_type` 
        CHECK (`account_type` IN ('ASSET', 'LIABILITY', 'EQUITY', 'REVENUE', 'EXPENSE'))
) ENGINE=InnoDB 
  DEFAULT CHARSET=utf8mb4 
  COLLATE=utf8mb4_unicode_ci
  COMMENT='Plano de Contas - Imutável após criação';

-- Índices
CREATE INDEX `idx_account_code` ON `chart_of_accounts` (`account_code`);
CREATE INDEX `idx_account_type` ON `chart_of_accounts` (`account_type`);
CREATE INDEX `idx_parent_account` ON `chart_of_accounts` (`parent_account_id`);
CREATE INDEX `idx_account_active` ON `chart_of_accounts` (`is_active`);

-- ============================================================================
-- TABELA: transactions
-- Cabeçalho de Transações Contábeis
-- ============================================================================

DROP TABLE IF EXISTS `transactions`;

CREATE TABLE `transactions` (
    -- Chaves
    `transaction_id` VARCHAR(36) NOT NULL COMMENT 'UUID único da transação',
    `transaction_number` VARCHAR(50) NOT NULL COMMENT 'Número sequencial YYYYMMDD-NNNNNN',
    
    -- Datas
    `transaction_date` DATETIME NOT NULL COMMENT 'Data do evento econômico (UTC)',
    `posting_date` DATETIME NULL COMMENT 'Data de lançamento contábil (UTC)',
    
    -- Dados de Negócio
    `business_event_type` VARCHAR(100) NOT NULL COMMENT 'Tipo de evento (SALE, PAYMENT, etc)',
    `business_key` VARCHAR(200) NULL COMMENT 'Chave de negócio para rastreamento',
    `reference_number` VARCHAR(100) NULL COMMENT 'Número de referência externo',
    `description` TEXT NOT NULL COMMENT 'Descrição da transação',
    
    -- Status e Controle
    `status` VARCHAR(20) NOT NULL DEFAULT 'PENDING' COMMENT 'PENDING, POSTED, REVERSED, CANCELLED',
    
    -- Reversão
    `is_reversal` BOOLEAN NOT NULL DEFAULT FALSE COMMENT 'Flag de reversão',
    `reverses_transaction_id` VARCHAR(36) NULL COMMENT 'ID da transação original',
    `reversed_by_transaction_id` VARCHAR(36) NULL COMMENT 'ID da transação que reverteu',
    `reversal_reason` TEXT NULL COMMENT 'Motivo da reversão',
    
    -- Auditoria
    `created_at` DATETIME NOT NULL COMMENT 'Data/hora de criação (UTC)',
    `created_by` VARCHAR(200) NOT NULL COMMENT 'Usuário criador',
    `source_system` VARCHAR(100) NOT NULL COMMENT 'Sistema de origem',
    `source_ip` VARCHAR(45) NULL COMMENT 'IP de origem',
    
    -- Integridade
    `transaction_hash` VARCHAR(64) NOT NULL COMMENT 'SHA-256 para integridade',
    
    -- Constraints
    PRIMARY KEY (`transaction_id`),
    UNIQUE KEY `uk_transaction_number` (`transaction_number`),
    CONSTRAINT `fk_reverses_transaction` 
        FOREIGN KEY (`reverses_transaction_id`) 
        REFERENCES `transactions` (`transaction_id`)
        ON DELETE RESTRICT 
        ON UPDATE CASCADE,
    CONSTRAINT `chk_transaction_status` 
        CHECK (`status` IN ('PENDING', 'POSTED', 'REVERSED', 'CANCELLED'))
) ENGINE=InnoDB 
  DEFAULT CHARSET=utf8mb4 
  COLLATE=utf8mb4_unicode_ci
  COMMENT='Transações Contábeis - Imutável após POSTED';

-- Índices
CREATE INDEX `idx_transaction_number` ON `transactions` (`transaction_number`);
CREATE INDEX `idx_transaction_date` ON `transactions` (`transaction_date`);
CREATE INDEX `idx_posting_date` ON `transactions` (`posting_date`);
CREATE INDEX `idx_business_key` ON `transactions` (`business_key`);
CREATE INDEX `idx_business_event_type` ON `transactions` (`business_event_type`);
CREATE INDEX `idx_status` ON `transactions` (`status`);
CREATE INDEX `idx_reversal` ON `transactions` (`is_reversal`, `reverses_transaction_id`);
CREATE INDEX `idx_created_at` ON `transactions` (`created_at`);
CREATE INDEX `idx_created_by` ON `transactions` (`created_by`);

-- ============================================================================
-- TABELA: journal_entries
-- Lançamentos Contábeis (Linhas de Transação)
-- ============================================================================

DROP TABLE IF EXISTS `journal_entries`;

CREATE TABLE `journal_entries` (
    -- Chaves
    `entry_id` VARCHAR(36) NOT NULL COMMENT 'UUID único do lançamento',
    `transaction_id` VARCHAR(36) NOT NULL COMMENT 'Referência à transação',
    `entry_number` DECIMAL(5,0) NOT NULL COMMENT 'Número da linha (1, 2, 3...)',
    
    -- Conta
    `account_id` VARCHAR(36) NOT NULL COMMENT 'Referência à conta',
    `account_code` VARCHAR(50) NOT NULL COMMENT 'Código da conta (desnormalizado)',
    
    -- Valores
    `entry_type` VARCHAR(10) NOT NULL COMMENT 'DEBIT ou CREDIT',
    `amount` DECIMAL(20,2) NOT NULL COMMENT 'Valor do lançamento (sempre positivo)',
    `currency` VARCHAR(3) NOT NULL DEFAULT 'AOA' COMMENT 'Código ISO 4217',
    
    -- Dimensões Analíticas
    `cost_center` VARCHAR(50) NULL COMMENT 'Centro de custo',
    `business_unit` VARCHAR(50) NULL COMMENT 'Unidade de negócio',
    `project_code` VARCHAR(50) NULL COMMENT 'Código do projeto',
    `memo` TEXT NULL COMMENT 'Observações do lançamento',
    
    -- Auditoria
    `created_at` DATETIME NOT NULL COMMENT 'Data/hora de criação (UTC)',
    
    -- Constraints
    PRIMARY KEY (`entry_id`),
    CONSTRAINT `fk_journal_transaction` 
        FOREIGN KEY (`transaction_id`) 
        REFERENCES `transactions` (`transaction_id`)
        ON DELETE RESTRICT 
        ON UPDATE CASCADE,
    CONSTRAINT `fk_journal_account` 
        FOREIGN KEY (`account_id`) 
        REFERENCES `chart_of_accounts` (`account_id`)
        ON DELETE RESTRICT 
        ON UPDATE CASCADE,
    CONSTRAINT `chk_amount_positive` 
        CHECK (`amount` > 0),
    CONSTRAINT `chk_entry_type` 
        CHECK (`entry_type` IN ('DEBIT', 'CREDIT'))
) ENGINE=InnoDB 
  DEFAULT CHARSET=utf8mb4 
  COLLATE=utf8mb4_unicode_ci
  COMMENT='Lançamentos Contábeis - Imutável';

-- Índices
CREATE INDEX `idx_transaction_entry` ON `journal_entries` (`transaction_id`, `entry_number`);
CREATE INDEX `idx_account_id` ON `journal_entries` (`account_id`);
CREATE INDEX `idx_account_code` ON `journal_entries` (`account_code`);
CREATE INDEX `idx_entry_type` ON `journal_entries` (`entry_type`);
CREATE INDEX `idx_cost_center` ON `journal_entries` (`cost_center`);
CREATE INDEX `idx_business_unit` ON `journal_entries` (`business_unit`);
CREATE INDEX `idx_project_code` ON `journal_entries` (`project_code`);
CREATE INDEX `idx_created_at` ON `journal_entries` (`created_at`);

-- ============================================================================
-- TABELA: closing_periods
-- Períodos de Fechamento Contábil
-- ============================================================================

DROP TABLE IF EXISTS `closing_periods`;

CREATE TABLE `closing_periods` (
    -- Chaves
    `closing_id` VARCHAR(36) NOT NULL COMMENT 'UUID único do fechamento',
    
    -- Período
    `period_type` VARCHAR(20) NOT NULL COMMENT 'DAILY, MONTHLY, QUARTERLY, ANNUAL',
    `period_start` DATETIME NOT NULL COMMENT 'Início do período (UTC)',
    `period_end` DATETIME NOT NULL COMMENT 'Fim do período (UTC)',
    
    -- Status
    `is_closed` BOOLEAN NOT NULL DEFAULT FALSE COMMENT 'Período fechado?',
    `closed_at` DATETIME NULL COMMENT 'Data/hora do fechamento (UTC)',
    `closed_by` VARCHAR(200) NULL COMMENT 'Usuário que fechou',
    
    -- Snapshot de Saldos
    `total_debits` DECIMAL(20,2) NULL COMMENT 'Total de débitos',
    `total_credits` DECIMAL(20,2) NULL COMMENT 'Total de créditos',
    `balance_check` BOOLEAN NULL COMMENT 'Verificação: débitos = créditos',
    
    -- Auditoria
    `created_at` DATETIME NOT NULL COMMENT 'Data/hora de criação (UTC)',
    
    -- Constraints
    PRIMARY KEY (`closing_id`),
    CONSTRAINT `chk_period_type` 
        CHECK (`period_type` IN ('DAILY', 'MONTHLY', 'QUARTERLY', 'ANNUAL'))
) ENGINE=InnoDB 
  DEFAULT CHARSET=utf8mb4 
  COLLATE=utf8mb4_unicode_ci
  COMMENT='Fechamentos Contábeis';

-- Índices
CREATE INDEX `idx_period_type` ON `closing_periods` (`period_type`);
CREATE INDEX `idx_period_dates` ON `closing_periods` (`period_start`, `period_end`);
CREATE INDEX `idx_is_closed` ON `closing_periods` (`is_closed`);

-- ============================================================================
-- TABELA: audit_log
-- Log de Auditoria Completo
-- ============================================================================

DROP TABLE IF EXISTS `audit_log`;

CREATE TABLE `audit_log` (
    -- Chaves
    `audit_id` VARCHAR(36) NOT NULL COMMENT 'UUID único do log',
    
    -- Evento
    `event_timestamp` DATETIME NOT NULL COMMENT 'Data/hora do evento (UTC)',
    `event_type` VARCHAR(100) NOT NULL COMMENT 'Tipo de evento',
    `severity` VARCHAR(20) NOT NULL COMMENT 'INFO, WARNING, ERROR, CRITICAL',
    
    -- Referências
    `transaction_id` VARCHAR(36) NULL COMMENT 'ID da transação (se aplicável)',
    `user_id` VARCHAR(200) NOT NULL COMMENT 'Identificação do usuário',
    `source_system` VARCHAR(100) NOT NULL COMMENT 'Sistema de origem',
    `source_ip` VARCHAR(45) NULL COMMENT 'IP de origem',
    
    -- Detalhes
    `action` VARCHAR(100) NOT NULL COMMENT 'Ação executada',
    `entity_type` VARCHAR(50) NULL COMMENT 'Tipo de entidade',
    `entity_id` VARCHAR(36) NULL COMMENT 'ID da entidade',
    `description` TEXT NOT NULL COMMENT 'Descrição do evento',
    `metadata` TEXT NULL COMMENT 'Contexto adicional (JSON)',
    
    -- Constraints
    PRIMARY KEY (`audit_id`),
    CONSTRAINT `fk_audit_transaction` 
        FOREIGN KEY (`transaction_id`) 
        REFERENCES `transactions` (`transaction_id`)
        ON DELETE SET NULL 
        ON UPDATE CASCADE,
    CONSTRAINT `chk_severity` 
        CHECK (`severity` IN ('INFO', 'WARNING', 'ERROR', 'CRITICAL'))
) ENGINE=InnoDB 
  DEFAULT CHARSET=utf8mb4 
  COLLATE=utf8mb4_unicode_ci
  COMMENT='Log de Auditoria - Imutável';

-- Índices
CREATE INDEX `idx_event_timestamp` ON `audit_log` (`event_timestamp`);
CREATE INDEX `idx_event_type` ON `audit_log` (`event_type`);
CREATE INDEX `idx_severity` ON `audit_log` (`severity`);
CREATE INDEX `idx_transaction_id` ON `audit_log` (`transaction_id`);
CREATE INDEX `idx_user_id` ON `audit_log` (`user_id`);
CREATE INDEX `idx_source_system` ON `audit_log` (`source_system`);
CREATE INDEX `idx_entity` ON `audit_log` (`entity_type`, `entity_id`);

-- ============================================================================
-- VIEWS: Visões de Consulta
-- ============================================================================

-- View: Saldos por Conta
DROP VIEW IF EXISTS `v_account_balances`;

CREATE VIEW `v_account_balances` AS
SELECT 
    coa.account_id,
    coa.account_code,
    coa.account_name,
    coa.account_type,
    COALESCE(SUM(CASE WHEN je.entry_type = 'DEBIT' THEN je.amount ELSE 0 END), 0) AS total_debits,
    COALESCE(SUM(CASE WHEN je.entry_type = 'CREDIT' THEN je.amount ELSE 0 END), 0) AS total_credits,
    CASE 
        WHEN coa.account_type IN ('ASSET', 'EXPENSE') THEN
            COALESCE(SUM(CASE WHEN je.entry_type = 'DEBIT' THEN je.amount ELSE 0 END), 0) -
            COALESCE(SUM(CASE WHEN je.entry_type = 'CREDIT' THEN je.amount ELSE 0 END), 0)
        ELSE
            COALESCE(SUM(CASE WHEN je.entry_type = 'CREDIT' THEN je.amount ELSE 0 END), 0) -
            COALESCE(SUM(CASE WHEN je.entry_type = 'DEBIT' THEN je.amount ELSE 0 END), 0)
    END AS balance
FROM chart_of_accounts coa
LEFT JOIN journal_entries je ON coa.account_id = je.account_id
LEFT JOIN transactions t ON je.transaction_id = t.transaction_id
WHERE (t.status = 'POSTED' OR t.status IS NULL)
  AND coa.is_active = TRUE
GROUP BY coa.account_id, coa.account_code, coa.account_name, coa.account_type;

-- View: Resumo de Transações
DROP VIEW IF EXISTS `v_transactions_summary`;

CREATE VIEW `v_transactions_summary` AS
SELECT 
    t.transaction_id,
    t.transaction_number,
    t.transaction_date,
    t.posting_date,
    t.business_event_type,
    t.business_key,
    t.description,
    t.status,
    t.is_reversal,
    COUNT(je.entry_id) AS entry_count,
    SUM(CASE WHEN je.entry_type = 'DEBIT' THEN je.amount ELSE 0 END) AS total_debits,
    SUM(CASE WHEN je.entry_type = 'CREDIT' THEN je.amount ELSE 0 END) AS total_credits,
    t.created_by,
    t.created_at
FROM transactions t
LEFT JOIN journal_entries je ON t.transaction_id = je.transaction_id
GROUP BY 
    t.transaction_id, t.transaction_number, t.transaction_date, t.posting_date,
    t.business_event_type, t.business_key, t.description, t.status, 
    t.is_reversal, t.created_by, t.created_at;

-- View: Balancete de Verificação
DROP VIEW IF EXISTS `v_trial_balance`;

CREATE VIEW `v_trial_balance` AS
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

-- ============================================================================
-- TRIGGERS: Garantir Imutabilidade e Integridade
-- ============================================================================

-- Trigger: Prevenir UPDATE em transações POSTED
DELIMITER //

DROP TRIGGER IF EXISTS `trg_prevent_transaction_update`//

CREATE TRIGGER `trg_prevent_transaction_update`
BEFORE UPDATE ON `transactions`
FOR EACH ROW
BEGIN
    IF OLD.status = 'POSTED' AND NEW.status NOT IN ('REVERSED', 'POSTED') THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Cannot modify posted transaction. Use reversal instead.';
    END IF;
    
    -- Permitir apenas mudança de status para REVERSED
    IF OLD.status = 'POSTED' AND NEW.status = 'POSTED' THEN
        IF OLD.transaction_number != NEW.transaction_number OR
           OLD.transaction_date != NEW.transaction_date OR
           OLD.business_event_type != NEW.business_event_type THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Posted transaction is immutable.';
        END IF;
    END IF;
END//

-- Trigger: Prevenir DELETE em transações
DROP TRIGGER IF EXISTS `trg_prevent_transaction_delete`//

CREATE TRIGGER `trg_prevent_transaction_delete`
BEFORE DELETE ON `transactions`
FOR EACH ROW
BEGIN
    SIGNAL SQLSTATE '45000'
    SET MESSAGE_TEXT = 'Cannot delete transactions. Use reversal instead.';
END//

-- Trigger: Prevenir DELETE em lançamentos
DROP TRIGGER IF EXISTS `trg_prevent_entry_delete`//

CREATE TRIGGER `trg_prevent_entry_delete`
BEFORE DELETE ON `journal_entries`
FOR EACH ROW
BEGIN
    SIGNAL SQLSTATE '45000'
    SET MESSAGE_TEXT = 'Cannot delete journal entries. Entries are immutable.';
END//

DELIMITER ;

-- ============================================================================
-- STORED PROCEDURES: Operações Comuns
-- ============================================================================

-- Procedure: Verificar Integridade de Dupla Entrada
DELIMITER //

DROP PROCEDURE IF EXISTS `sp_verify_double_entry`//

CREATE PROCEDURE `sp_verify_double_entry`(
    IN p_transaction_id VARCHAR(36)
)
BEGIN
    DECLARE v_debits DECIMAL(20,2);
    DECLARE v_credits DECIMAL(20,2);
    DECLARE v_balanced BOOLEAN;
    
    SELECT 
        SUM(CASE WHEN entry_type = 'DEBIT' THEN amount ELSE 0 END),
        SUM(CASE WHEN entry_type = 'CREDIT' THEN amount ELSE 0 END)
    INTO v_debits, v_credits
    FROM journal_entries
    WHERE transaction_id = p_transaction_id;
    
    SET v_balanced = (v_debits = v_credits);
    
    SELECT 
        p_transaction_id AS transaction_id,
        v_debits AS total_debits,
        v_credits AS total_credits,
        v_balanced AS is_balanced;
END//

DELIMITER ;

-- ============================================================================
-- DADOS INICIAIS: Contas Básicas
-- ============================================================================

-- Inserir contas raiz (exemplos)
INSERT INTO `chart_of_accounts` 
    (`account_id`, `account_code`, `account_name`, `account_type`, `level`, `created_at`, `created_by`)
VALUES
    (UUID(), '1000', 'ATIVOS', 'ASSET', 1, UTC_TIMESTAMP(), 'SYSTEM'),
    (UUID(), '2000', 'PASSIVOS', 'LIABILITY', 1, UTC_TIMESTAMP(), 'SYSTEM'),
    (UUID(), '3000', 'PATRIMÔNIO LÍQUIDO', 'EQUITY', 1, UTC_TIMESTAMP(), 'SYSTEM'),
    (UUID(), '4000', 'RECEITAS', 'REVENUE', 1, UTC_TIMESTAMP(), 'SYSTEM'),
    (UUID(), '5000', 'DESPESAS', 'EXPENSE', 1, UTC_TIMESTAMP(), 'SYSTEM');

-- ============================================================================
-- VERIFICAÇÕES FINAIS
-- ============================================================================

-- Verificar estrutura
SELECT 
    TABLE_NAME,
    TABLE_ROWS,
    DATA_LENGTH,
    INDEX_LENGTH
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = 'ledger_db'
ORDER BY TABLE_NAME;

-- Restaurar configurações
SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;

-- ============================================================================
-- FIM DO SCRIPT
-- ============================================================================

SELECT 'Database schema created successfully!' AS Status;
