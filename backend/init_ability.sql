-- 能力测评表
CREATE TABLE IF NOT EXISTS ability_assessment (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '测评ID',
    student_id BIGINT NOT NULL COMMENT '关联student.id',
    total_score INT NOT NULL COMMENT '总分',
    sign_score INT NOT NULL COMMENT '交通标志得分',
    law_score INT NOT NULL COMMENT '交通法规得分',
    safe_score INT NOT NULL COMMENT '安全常识得分',
    drive_score INT NOT NULL COMMENT '驾驶理论得分',
    level VARCHAR(16) NULL COMMENT '能力等级',
    weak_know TEXT NULL COMMENT '薄弱方面',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '测评时间',
    INDEX idx_student (student_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='能力测评表';
