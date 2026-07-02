-- 新增专项训练提交记录表
CREATE TABLE IF NOT EXISTS special_training_session (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '记录ID',
    student_id BIGINT NOT NULL COMMENT '学员ID',
    category VARCHAR(20) NOT NULL COMMENT '分类: 交通标志/交通法规/安全常识/驾驶理论',
    question_count INT DEFAULT 0 COMMENT '题目数量',
    correct_count INT DEFAULT 0 COMMENT '正确题数',
    correct_rate FLOAT DEFAULT 0.0 COMMENT '正确率',
    submit_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '提交时间',
    INDEX idx_session_student_time (student_id, submit_time),
    CONSTRAINT fk_session_student FOREIGN KEY (student_id) REFERENCES student(id)
) COMMENT='专项训练提交记录表';
