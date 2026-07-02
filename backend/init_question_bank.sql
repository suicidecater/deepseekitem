-- ============================================================
-- 科目一、科目四、专业人员 题库建表 + 示例数据
-- ============================================================

-- 科目一题库
CREATE TABLE IF NOT EXISTS subject1_question (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '记录ID',
    question_number INT NOT NULL COMMENT '题号',
    question_type VARCHAR(16) NOT NULL COMMENT '题型: 判断题/单选题/多选题',
    question_text TEXT NOT NULL COMMENT '题干',
    option_a VARCHAR(255) NULL COMMENT 'A选项',
    option_b VARCHAR(255) NULL COMMENT 'B选项',
    option_c VARCHAR(255) NULL COMMENT 'C选项',
    option_d VARCHAR(255) NULL COMMENT 'D选项',
    correct_answer VARCHAR(16) NOT NULL COMMENT '正确答案',
    image_file VARCHAR(255) NULL COMMENT '附图文件名',
    difficulty INT DEFAULT 1 COMMENT '难度: 1-5',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_number (question_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='科目一题库';

-- 科目四题库
CREATE TABLE IF NOT EXISTS subject4_question (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '记录ID',
    question_number INT NOT NULL COMMENT '题号',
    question_type VARCHAR(16) NOT NULL COMMENT '题型: 判断题/单选题/多选题',
    question_text TEXT NOT NULL COMMENT '题干',
    option_a VARCHAR(255) NULL COMMENT 'A选项',
    option_b VARCHAR(255) NULL COMMENT 'B选项',
    option_c VARCHAR(255) NULL COMMENT 'C选项',
    option_d VARCHAR(255) NULL COMMENT 'D选项',
    correct_answer VARCHAR(16) NOT NULL COMMENT '正确答案',
    image_file VARCHAR(255) NULL COMMENT '附图文件名',
    difficulty INT DEFAULT 1 COMMENT '难度: 1-5',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_number (question_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='科目四题库';

-- 专业人员题库
CREATE TABLE IF NOT EXISTS professional_question (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '记录ID',
    question_number INT NOT NULL COMMENT '题号',
    question_type VARCHAR(16) NOT NULL COMMENT '题型: 判断题/单选题/多选题',
    question_text TEXT NOT NULL COMMENT '题干',
    option_a VARCHAR(255) NULL COMMENT 'A选项',
    option_b VARCHAR(255) NULL COMMENT 'B选项',
    option_c VARCHAR(255) NULL COMMENT 'C选项',
    option_d VARCHAR(255) NULL COMMENT 'D选项',
    correct_answer VARCHAR(16) NOT NULL COMMENT '正确答案',
    image_file VARCHAR(255) NULL COMMENT '附图文件名',
    difficulty INT DEFAULT 1 COMMENT '难度: 1-5',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_number (question_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='专业人员题库';

-- ============================================================
-- 示例数据（科目一）
-- ============================================================
INSERT INTO subject1_question (question_number, question_type, question_text, option_a, option_b, option_c, option_d, correct_answer, image_file, difficulty) VALUES
(1, '判断题', '驾驶机动车在道路上违反道路通行规定应当接受相应的处罚。', NULL, NULL, NULL, NULL, '√', '1_1.jpg', 1),
(2, '单选题', '机动车驾驶人违法驾驶造成重大交通事故构成犯罪的，依法追究什么责任？', '刑事责任', '民事责任', '经济责任', '直接责任', 'A', '1_2.jpg', 3);

-- ============================================================
-- 示例数据（科目四）
-- ============================================================
INSERT INTO subject4_question (question_number, question_type, question_text, option_a, option_b, option_c, option_d, correct_answer, image_file, difficulty) VALUES
(1, '判断题', '驾驶车辆汇入车流时，应提前开启转向灯，保持直线行驶，通过后视镜观察左右情况，确认安全后汇入合流。', NULL, NULL, NULL, NULL, '√', NULL, 2),
(2, '单选题', '当机动车转向失控行驶方向偏离，事故已经无可避免时，要采取什么措施？', '迅速转向调整', '全力制动减速', '迅速向相反方向转向', '抢挡减速', 'B', '4_2.jpg', 3);

-- ============================================================
-- 示例数据（专业人员）
-- ============================================================
INSERT INTO professional_question (question_number, question_type, question_text, option_a, option_b, option_c, option_d, correct_answer, image_file, difficulty) VALUES
(1, '判断题', '危险化学品运输车辆应当符合国家标准要求的安全技术条件，并定期进行安全技术检验。', NULL, NULL, NULL, NULL, '√', NULL, 1),
(2, '单选题', '危险化学品道路运输企业的驾驶人员未取得从业资格上岗作业的，由交通运输主管部门责令改正，处多少元罚款？', '1万元以上2万元以下', '2万元以上5万元以下', '5万元以上10万元以下', '10万元以上20万元以下', 'C', NULL, 4);
