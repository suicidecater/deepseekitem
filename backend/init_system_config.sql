-- 系统配置表（如不存在则创建）
CREATE TABLE IF NOT EXISTS system_config (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '配置ID',
    config_key VARCHAR(64) NOT NULL COMMENT '配置键',
    config_value TEXT NULL COMMENT '配置值（敏感项AES加密存储）',
    description VARCHAR(255) NULL COMMENT '配置说明',
    updated_by BIGINT NULL COMMENT '更新人ID',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    UNIQUE INDEX uk_config_key (config_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统配置表';

-- 初始化DeepSeek API Key
INSERT INTO system_config (config_key, config_value, description) VALUES
('deepseek_api_key', 'your-deepseek-api-key-here', 'DeepSeek API密钥，用于AI智能服务')
ON DUPLICATE KEY UPDATE config_value = VALUES(config_value);
