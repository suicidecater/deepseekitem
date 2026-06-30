-- 为 evaluation 表添加难度分层字段
ALTER TABLE evaluation ADD COLUMN simple_rate INT DEFAULT 0 COMMENT '简单题全局正确率(%)';
ALTER TABLE evaluation ADD COLUMN mid_rate INT DEFAULT 0 COMMENT '中等题全局正确率(%)';
ALTER TABLE evaluation ADD COLUMN diff_detail TEXT COMMENT '难度分层详情(JSON)';
