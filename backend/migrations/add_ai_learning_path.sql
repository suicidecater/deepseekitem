-- 新建 AI学习路径缓存表（测评结果不变则不重调DeepSeek）
CREATE TABLE IF NOT EXISTS ai_learning_path (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '路径ID',
    student_id BIGINT NOT NULL COMMENT '学员ID',
    study_subject SMALLINT DEFAULT 1 COMMENT '学习方向: 1/4/5',
    evaluation_id BIGINT NULL COMMENT '关联的测评记录ID',
    content TEXT NOT NULL COMMENT 'AI生成的完整学习路径JSON',
    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '生成时间',
    INDEX idx_student_subject_path (student_id, study_subject)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='AI学习路径缓存表';
