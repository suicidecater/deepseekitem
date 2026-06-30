-- AI对话表
CREATE TABLE IF NOT EXISTS ai_chat (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '对话ID',
    student_id BIGINT NOT NULL COMMENT '关联student.id',
    user_msg TEXT NOT NULL COMMENT '用户提问',
    ai_msg TEXT NOT NULL COMMENT 'AI回复',
    is_collect TINYINT NOT NULL DEFAULT 0 COMMENT '1收藏 0未收藏',
    is_deleted TINYINT NOT NULL DEFAULT 0 COMMENT '1已删除 0正常',
    expire_time DATETIME NULL COMMENT '过期时间',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '对话时间',
    INDEX idx_student (student_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='AI对话表';
