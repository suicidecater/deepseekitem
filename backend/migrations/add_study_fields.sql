-- 新增学习方向 + 测评状态字段
ALTER TABLE student ADD COLUMN study_subject SMALLINT DEFAULT 1 COMMENT '学习方向: 1科目一/4科目四/3专业人员';
ALTER TABLE student ADD COLUMN evaluation_status TINYINT DEFAULT 0 COMMENT '测评状态: 0未测评/1已完成';
