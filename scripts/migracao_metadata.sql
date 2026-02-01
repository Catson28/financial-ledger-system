-- ========================================
-- MIGRAÇÃO: Renomear coluna metadata
-- ========================================
-- Data: 2026-02-01
-- Descrição: Renomear coluna 'metadata' para 'event_metadata' 
--            na tabela audit_log devido a conflito com SQLAlchemy
-- ========================================

-- Para MySQL/MariaDB:
ALTER TABLE audit_log CHANGE COLUMN metadata event_metadata TEXT NULL;

-- OU, se preferir RENAME COLUMN (MySQL 8.0+):
-- ALTER TABLE audit_log RENAME COLUMN metadata TO event_metadata;

-- Para PostgreSQL:
-- ALTER TABLE audit_log RENAME COLUMN metadata TO event_metadata;

-- Para SQLite:
-- SQLite não suporta RENAME COLUMN diretamente em versões antigas
-- Será necessário recriar a tabela:
-- 
-- BEGIN TRANSACTION;
-- 
-- CREATE TABLE audit_log_new (
--     audit_id VARCHAR(36) PRIMARY KEY,
--     event_timestamp DATETIME NOT NULL,
--     event_type VARCHAR(100) NOT NULL,
--     severity VARCHAR(20) NOT NULL,
--     transaction_id VARCHAR(36),
--     user_id VARCHAR(200) NOT NULL,
--     source_system VARCHAR(100) NOT NULL,
--     source_ip VARCHAR(45),
--     action VARCHAR(100) NOT NULL,
--     entity_type VARCHAR(50),
--     entity_id VARCHAR(36),
--     description TEXT NOT NULL,
--     event_metadata TEXT
-- );
-- 
-- INSERT INTO audit_log_new 
-- SELECT 
--     audit_id,
--     event_timestamp,
--     event_type,
--     severity,
--     transaction_id,
--     user_id,
--     source_system,
--     source_ip,
--     action,
--     entity_type,
--     entity_id,
--     description,
--     metadata as event_metadata
-- FROM audit_log;
-- 
-- DROP TABLE audit_log;
-- 
-- ALTER TABLE audit_log_new RENAME TO audit_log;
-- 
-- -- Recriar índices
-- CREATE INDEX idx_event_timestamp ON audit_log(event_timestamp);
-- CREATE INDEX idx_transaction_id ON audit_log(transaction_id);
-- CREATE INDEX idx_user_id ON audit_log(user_id);
-- CREATE INDEX idx_severity ON audit_log(severity);
-- 
-- COMMIT;

-- ========================================
-- VERIFICAÇÃO
-- ========================================

-- Verificar estrutura da tabela após migração:
DESCRIBE audit_log;

-- OU para outros bancos:
-- SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'audit_log';

-- Verificar dados:
SELECT COUNT(*) as total_registros FROM audit_log;
SELECT COUNT(*) as registros_com_metadata FROM audit_log WHERE event_metadata IS NOT NULL;

-- ========================================
-- ROLLBACK (se necessário)
-- ========================================

-- Para MySQL/MariaDB:
-- ALTER TABLE audit_log CHANGE COLUMN event_metadata metadata TEXT NULL;

-- Para PostgreSQL:
-- ALTER TABLE audit_log RENAME COLUMN event_metadata TO metadata;
