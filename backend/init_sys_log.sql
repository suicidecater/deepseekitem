-- 系统日志表
CREATE TABLE IF NOT EXISTS sys_log (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '日志ID',
    user_type TINYINT NOT NULL COMMENT '用户类型: 1学员 2教练 3管理员',
    user_id BIGINT NOT NULL COMMENT '用户ID',
    log_type TINYINT NOT NULL COMMENT '日志类型: 1登录 2操作',
    module VARCHAR(64) NULL COMMENT '操作模块',
    content VARCHAR(255) NOT NULL COMMENT '日志内容',
    ip VARCHAR(32) NULL COMMENT '登录IP',
    device VARCHAR(64) NULL COMMENT '设备信息',
    oper_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '操作时间',
    INDEX idx_user (user_type, user_id),
    INDEX idx_oper_time (oper_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统日志表';
