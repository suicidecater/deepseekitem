-- 消息通知表
CREATE TABLE IF NOT EXISTS message (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '消息ID',
    receive_type TINYINT NOT NULL COMMENT '接收者类型: 1学员/2教练/3管理员',
    receive_id BIGINT NOT NULL COMMENT '接收者ID',
    title VARCHAR(64) NOT NULL COMMENT '消息标题',
    content TEXT NULL COMMENT '消息内容',
    type TINYINT DEFAULT 1 COMMENT '消息类型: 1提醒/2公告/3成绩/4任务',
    channel TINYINT DEFAULT 1 COMMENT '渠道: 1站内/2邮箱',
    status TINYINT DEFAULT 1 COMMENT '状态: 1未读/2已读/3删除',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_receive (receive_type, receive_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='消息通知表';

-- 笔记互动表
CREATE TABLE IF NOT EXISTS note (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '笔记ID',
    student_id BIGINT NOT NULL COMMENT '关联student.id',
    content TEXT NULL COMMENT '笔记内容',
    status TINYINT DEFAULT 1 COMMENT '状态: 1待审核/2已上线/3驳回',
    like_count INT DEFAULT 0 COMMENT '点赞数',
    collect_count INT DEFAULT 0 COMMENT '收藏数',
    comment TEXT NULL COMMENT '评论(JSON)',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_student (student_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='笔记互动表';

-- 用户反馈表
CREATE TABLE IF NOT EXISTS feedback (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '反馈ID',
    user_type TINYINT NOT NULL COMMENT '用户类型: 1学员/2教练',
    user_id BIGINT NOT NULL COMMENT '用户ID',
    type TINYINT DEFAULT 3 COMMENT '反馈类型: 1故障/2学习/3建议/4投诉',
    content TEXT NULL COMMENT '反馈内容',
    handler_id BIGINT NULL COMMENT '处理人ID(关联admin.id)',
    reply TEXT NULL COMMENT '回复内容',
    status TINYINT DEFAULT 1 COMMENT '状态: 1待处理/2处理中/3已办结',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_user (user_type, user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户反馈表';
