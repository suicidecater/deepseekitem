-- ============================================================
-- 核心业务表（exam, knowledge, question, study, memory）
-- ============================================================

-- 知识点表
CREATE TABLE IF NOT EXISTS knowledge (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '知识点ID',
    category_name VARCHAR(64) NULL COMMENT '分类名称',
    category_code VARCHAR(64) NULL COMMENT '分类编码',
    name VARCHAR(128) NOT NULL COMMENT '知识点名称',
    content TEXT NULL COMMENT '知识点内容',
    parent_id BIGINT NULL COMMENT '父知识点ID',
    status TINYINT DEFAULT 1 COMMENT '状态: 1正常/2禁用',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    UNIQUE INDEX uk_category_code (category_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='知识点表';

-- 课程表
CREATE TABLE IF NOT EXISTS course (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '课程ID',
    name VARCHAR(128) NOT NULL COMMENT '课程名称',
    description TEXT NULL COMMENT '课程描述',
    train_type TINYINT DEFAULT 1 COMMENT '培训类型',
    status TINYINT DEFAULT 1 COMMENT '状态: 1正常/2禁用',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='课程表';

-- 学习资料表
CREATE TABLE IF NOT EXISTS material (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '资料ID',
    course_id BIGINT NULL COMMENT '关联course.id',
    know_id BIGINT NULL COMMENT '关联knowledge.id',
    title VARCHAR(128) NOT NULL COMMENT '资料标题',
    url VARCHAR(255) NULL COMMENT '资料URL',
    file_type VARCHAR(16) NULL COMMENT '文件类型',
    status TINYINT DEFAULT 1 COMMENT '状态: 1正常/2禁用',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_course (course_id),
    INDEX idx_know (know_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学习资料表';

-- 题目表（统一题库）
CREATE TABLE IF NOT EXISTS question (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '题目ID',
    know_id BIGINT NULL COMMENT '关联knowledge.id',
    type SMALLINT NOT NULL COMMENT '题型: 1单选/2多选/3判断/4图片/5情景',
    difficulty SMALLINT DEFAULT 1 COMMENT '难度: 1简单/2中等/3困难',
    train_type SMALLINT DEFAULT 1 COMMENT '培训类型',
    subject SMALLINT NOT NULL COMMENT '科目: 1科一/4科四',
    content TEXT NOT NULL COMMENT '题干',
    image VARCHAR(255) NULL COMMENT '题目图片URL',
    options TEXT NULL COMMENT '选项(JSON数组)',
    answer VARCHAR(64) NOT NULL COMMENT '正确答案',
    analysis TEXT NULL COMMENT '解析',
    law TEXT NULL COMMENT '法规原文',
    status SMALLINT DEFAULT 1 COMMENT '状态: 1草稿/2待审核/3已上线/4作废',
    version INT DEFAULT 1 COMMENT '版本号',
    tags VARCHAR(255) NULL COMMENT '标签',
    variant_ids VARCHAR(255) NULL COMMENT '变体题目ID',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_know (know_id),
    INDEX idx_subject (subject)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='题目表';

-- 错题本表
CREATE TABLE IF NOT EXISTS error_question (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '记录ID',
    student_id BIGINT NOT NULL COMMENT '关联student.id',
    question_id BIGINT NOT NULL COMMENT '关联question.id',
    error_type SMALLINT DEFAULT 4 COMMENT '错因: 1概念不清/2审题失误/3混淆记忆/4其他',
    error_count INT DEFAULT 1 COMMENT '错误次数',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_student (student_id),
    INDEX idx_question (question_id),
    UNIQUE INDEX uk_student_question (student_id, question_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='错题本表';

-- 能力测评表（旧版Evaluation）
CREATE TABLE IF NOT EXISTS evaluation (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '测评ID',
    student_id BIGINT NOT NULL COMMENT '关联student.id',
    total_score INT DEFAULT 0 COMMENT '总分',
    sign_score INT NULL COMMENT '交通标志得分',
    law_score INT NULL COMMENT '交通法规得分',
    safe_score INT NULL COMMENT '安全常识得分',
    drive_score INT NULL COMMENT '驾驶理论得分',
    level VARCHAR(16) NULL COMMENT '能力等级',
    weak_know TEXT NULL COMMENT '薄弱知识点(JSON)',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '测评时间',
    INDEX idx_student (student_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='能力测评表';

-- 练习考试记录表
CREATE TABLE IF NOT EXISTS practice_exam (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '记录ID',
    student_id BIGINT NOT NULL COMMENT '关联student.id',
    biz_type SMALLINT DEFAULT 1 COMMENT '类型: 1练习/2考试',
    subject SMALLINT DEFAULT 1 COMMENT '科目',
    question_ids TEXT NULL COMMENT '题目ID列表(逗号分隔)',
    user_answers TEXT NULL COMMENT '用户答案(JSON)',
    total_time INT DEFAULT 0 COMMENT '总用时(秒)',
    score INT DEFAULT 0 COMMENT '得分',
    correct_rate DECIMAL(5,2) DEFAULT 0 COMMENT '正确率(%)',
    status SMALLINT DEFAULT 1 COMMENT '状态: 1进行中/2已完成/3已交卷',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '开始时间',
    end_time DATETIME NULL COMMENT '结束时间',
    INDEX idx_student (student_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='练习考试记录表';

-- 学习计划表
CREATE TABLE IF NOT EXISTS study_plan (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '计划ID',
    student_id BIGINT NOT NULL COMMENT '关联student.id',
    study_subject SMALLINT DEFAULT 1 COMMENT '学习方向: 1=科目一/4=科目四/5=专业人员',
    plan_type SMALLINT DEFAULT 1 COMMENT '计划类型: 1长期/2每日任务',
    content VARCHAR(255) NULL COMMENT '计划内容',
    task_date DATE NULL COMMENT '任务日期',
    status SMALLINT DEFAULT 1 COMMENT '状态: 1未开始/2进行中/3已完成/4逾期',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_student_subject (student_id, study_subject),
    INDEX idx_task_date (task_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学习计划表';

-- 已有数据库迁移脚本（如果 study_plan 表已存在，执行以下SQL）：
-- ALTER TABLE study_plan ADD COLUMN study_subject SMALLINT DEFAULT 1 COMMENT '学习方向: 1/4/5' AFTER student_id;
-- CREATE INDEX idx_student_subject ON study_plan(student_id, study_subject);
