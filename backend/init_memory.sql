-- 学员题目记忆曲线表（艾宾浩斯遗忘曲线）
CREATE TABLE IF NOT EXISTS student_question_memory (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '记录ID',
    student_id BIGINT NOT NULL COMMENT '学员ID',
    question_id BIGINT NOT NULL COMMENT '题目ID',
    memory_strength DOUBLE DEFAULT 1.0 COMMENT '记忆强度(0-1)',
    review_count INT DEFAULT 0 COMMENT '复习次数',
    last_review_time DATETIME NULL COMMENT '最后复习时间',
    next_review_time DATETIME NULL COMMENT '下次复习时间',
    UNIQUE INDEX uk_student_question (student_id, question_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学员题目记忆曲线表';
