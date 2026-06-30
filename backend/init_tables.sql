-- ============================================================
-- 交通知识培训平台 - 用户体系建表脚本（无 phone 字段）
-- 数据库: traffic_training (utf8mb4)
-- ============================================================

-- 教练表（先创建，因为学员表外键依赖它）
CREATE TABLE IF NOT EXISTS coach (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '教练ID',
    email VARCHAR(64) NOT NULL COMMENT '登录邮箱',
    password VARCHAR(64) NOT NULL COMMENT '密码(bcrypt加密)',
    school_name VARCHAR(64) NOT NULL COMMENT '所属驾校名称',
    school_address VARCHAR(255) NULL COMMENT '驾校地址',
    school_phone VARCHAR(20) NULL COMMENT '驾校联系电话',
    train_type TINYINT NOT NULL DEFAULT 1 COMMENT '培训类型: 1驾考/2客运/3货运/4危险品',
    status TINYINT NOT NULL DEFAULT 1 COMMENT '状态: 1正常/2离职/3禁用',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE INDEX uk_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='教练表';

-- 学员表
CREATE TABLE IF NOT EXISTS student (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '学员ID',
    email VARCHAR(64) NOT NULL COMMENT '登录邮箱',
    password VARCHAR(64) NOT NULL COMMENT '密码(bcrypt加密)',
    name VARCHAR(32) NULL COMMENT '姓名',
    coach_id BIGINT NULL COMMENT '专属教练ID',
    train_type TINYINT NOT NULL DEFAULT 1 COMMENT '培训类型: 1驾考/2客运/3货运/4危险品',
    car_type VARCHAR(8) NULL COMMENT '报考车型: C1/C2/A1/A2',
    status TINYINT NOT NULL DEFAULT 1 COMMENT '状态: 1正常/2结业/3弃学/4禁用',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE INDEX uk_email (email),
    INDEX idx_coach_id (coach_id),
    CONSTRAINT fk_student_coach FOREIGN KEY (coach_id) REFERENCES coach(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学员表';

-- 平台管理员表
CREATE TABLE IF NOT EXISTS platform_admin (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '平台管理员ID',
    email VARCHAR(64) NOT NULL COMMENT '登录邮箱',
    password VARCHAR(64) NOT NULL COMMENT '密码(bcrypt加密)',
    admin_type TINYINT NOT NULL DEFAULT 2 COMMENT '管理员类型: 1超级/2内容/3运营',
    status TINYINT NOT NULL DEFAULT 1 COMMENT '状态: 1正常/2禁用',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE INDEX uk_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='平台管理员表';

-- 如果旧表存在 phone 列，执行删除
-- ALTER TABLE student DROP COLUMN IF EXISTS phone;
-- ALTER TABLE coach DROP COLUMN IF EXISTS phone;
-- ALTER TABLE platform_admin DROP COLUMN IF EXISTS phone;
