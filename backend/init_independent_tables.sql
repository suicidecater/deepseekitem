-- 错题本表（适配三张独立题库表）
CREATE TABLE IF NOT EXISTS error_question (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '记录ID',
    student_id BIGINT NOT NULL COMMENT '关联student.id',
    question_id BIGINT NOT NULL COMMENT '关联题库表ID',
    source VARCHAR(20) NOT NULL DEFAULT 'subject1' COMMENT '来源: subject1/subject4/professional',
    error_type SMALLINT DEFAULT 4 COMMENT '错因: 1概念不清/2审题失误/3混淆记忆/4其他',
    error_count INT DEFAULT 1 COMMENT '错误次数',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_student (student_id),
    INDEX idx_question (question_id, source),
    UNIQUE INDEX uk_student_question (student_id, question_id, source)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='错题本表';

-- 学员题目记忆曲线表（适配三张独立题库表）
CREATE TABLE IF NOT EXISTS student_question_memory (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '记录ID',
    student_id BIGINT NOT NULL COMMENT '关联student.id',
    question_id BIGINT NOT NULL COMMENT '关联题库表ID',
    source VARCHAR(20) NOT NULL DEFAULT 'subject1' COMMENT '来源: subject1/subject4/professional',
    memory_strength DOUBLE DEFAULT 1.0 COMMENT '记忆强度(0-1)',
    review_count INT DEFAULT 0 COMMENT '复习次数',
    last_review_time DATETIME NULL,
    next_review_time DATETIME NULL,
    INDEX idx_student (student_id),
    UNIQUE INDEX uk_student_question (student_id, question_id, source)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学员题目记忆曲线表';
