-- ============================================
-- 教练-学员对话系统 数据库表
-- 方案2: 新建 conversation + chat_message 表
-- ============================================

-- 会话表
CREATE TABLE IF NOT EXISTS `conversation` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '会话ID',
  `coach_id` bigint NOT NULL COMMENT '教练ID',
  `student_id` bigint NOT NULL COMMENT '学员ID',
  `last_message` varchar(500) DEFAULT NULL COMMENT '最后一条消息摘要',
  `last_message_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '最后消息时间',
  `unread_coach` int DEFAULT 0 COMMENT '教练未读数',
  `unread_student` int DEFAULT 0 COMMENT '学员未读数',
  `status` tinyint DEFAULT 1 COMMENT '状态: 1正常/2已归档',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_coach_student` (`coach_id`, `student_id`),
  KEY `idx_coach` (`coach_id`),
  KEY `idx_student` (`student_id`),
  KEY `idx_last_msg_time` (`last_message_time`),
  CONSTRAINT `fk_conv_coach` FOREIGN KEY (`coach_id`) REFERENCES `coach`(`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_conv_student` FOREIGN KEY (`student_id`) REFERENCES `student`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='教练-学员会话表';

-- 聊天消息表
CREATE TABLE IF NOT EXISTS `chat_message` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '消息ID',
  `conversation_id` bigint NOT NULL COMMENT '会话ID',
  `sender_type` varchar(20) NOT NULL COMMENT '发送者类型: student/coach',
  `sender_id` bigint NOT NULL COMMENT '发送者ID',
  `content` text NOT NULL COMMENT '消息内容',
  `message_type` tinyint DEFAULT 1 COMMENT '消息类型: 1文本/2图片/3文件',
  `status` tinyint DEFAULT 1 COMMENT '状态: 1已发送/2已读/3已撤回',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_conversation` (`conversation_id`, `create_time`),
  CONSTRAINT `fk_msg_conv` FOREIGN KEY (`conversation_id`) REFERENCES `conversation`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='聊天消息表';
