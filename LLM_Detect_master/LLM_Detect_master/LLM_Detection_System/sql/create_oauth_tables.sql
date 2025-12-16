-- =====================================================
-- OAuth 2.0 数据库表结构设计
-- 用于工程制图检测模块的外部API访问控制
-- =====================================================

-- 1. OAuth客户端表 (oauth_clients)
-- 存储外部客户端的认证信息
CREATE TABLE IF NOT EXISTS `oauth_clients` (
  `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '客户端ID（主键）',
  `client_id` VARCHAR(255) NOT NULL UNIQUE COMMENT '客户端标识符（UUID）',
  `client_secret` VARCHAR(255) NOT NULL COMMENT '客户端密钥（加密存储）',
  `client_name` VARCHAR(255) NOT NULL COMMENT '客户端名称',
  `client_description` TEXT COMMENT '客户端描述',
  `contact_email` VARCHAR(255) COMMENT '联系邮箱',
  `contact_person` VARCHAR(255) COMMENT '联系人',
  `is_active` VARCHAR(10) DEFAULT '1' COMMENT '是否启用（1=启用，0=禁用）',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_by` VARCHAR(255) COMMENT '创建者（管理员用户名）',
  `rate_limit` INT DEFAULT 100 COMMENT '每小时请求限制（默认100次/小时）',
  `allowed_scopes` VARCHAR(500) DEFAULT 'drawing:upload,drawing:inspect,drawing:query' COMMENT '允许的权限范围',
  INDEX `idx_client_id` (`client_id`),
  INDEX `idx_is_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='OAuth 2.0 客户端表';

-- 2. OAuth访问令牌表 (oauth_tokens)
-- 存储已颁发的访问令牌
CREATE TABLE IF NOT EXISTS `oauth_tokens` (
  `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '令牌ID（主键）',
  `access_token` VARCHAR(500) NOT NULL UNIQUE COMMENT '访问令牌（JWT）',
  `client_id` VARCHAR(255) NOT NULL COMMENT '客户端标识符',
  `token_type` VARCHAR(50) DEFAULT 'Bearer' COMMENT '令牌类型',
  `expires_at` DATETIME NOT NULL COMMENT '过期时间',
  `scopes` VARCHAR(500) COMMENT '授权范围',
  `is_revoked` VARCHAR(10) DEFAULT '0' COMMENT '是否已撤销（1=已撤销，0=有效）',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `last_used_at` DATETIME COMMENT '最后使用时间',
  INDEX `idx_access_token` (`access_token`),
  INDEX `idx_client_id` (`client_id`),
  INDEX `idx_expires_at` (`expires_at`),
  INDEX `idx_is_revoked` (`is_revoked`),
  FOREIGN KEY (`client_id`) REFERENCES `oauth_clients`(`client_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='OAuth 2.0 访问令牌表';

-- 3. API调用日志表 (api_call_logs)
-- 记录所有API调用，用于审计和统计
CREATE TABLE IF NOT EXISTS `api_call_logs` (
  `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '日志ID（主键）',
  `client_id` VARCHAR(255) NOT NULL COMMENT '客户端标识符',
  `endpoint` VARCHAR(255) NOT NULL COMMENT 'API端点',
  `method` VARCHAR(10) NOT NULL COMMENT 'HTTP方法（GET/POST等）',
  `status_code` INT COMMENT 'HTTP状态码',
  `request_ip` VARCHAR(50) COMMENT '请求IP地址',
  `request_params` TEXT COMMENT '请求参数（JSON格式）',
  `response_time` INT COMMENT '响应时间（毫秒）',
  `error_message` TEXT COMMENT '错误信息（如果有）',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '调用时间',
  INDEX `idx_client_id` (`client_id`),
  INDEX `idx_endpoint` (`endpoint`),
  INDEX `idx_created_at` (`created_at`),
  FOREIGN KEY (`client_id`) REFERENCES `oauth_clients`(`client_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='API调用日志表';

-- 4. API频率限制表 (api_rate_limits)
-- 用于实现滑动窗口频率限制
CREATE TABLE IF NOT EXISTS `api_rate_limits` (
  `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT 'ID（主键）',
  `client_id` VARCHAR(255) NOT NULL COMMENT '客户端标识符',
  `window_start` DATETIME NOT NULL COMMENT '时间窗口开始时间',
  `request_count` INT DEFAULT 0 COMMENT '请求次数',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  UNIQUE KEY `unique_client_window` (`client_id`, `window_start`),
  INDEX `idx_client_id` (`client_id`),
  INDEX `idx_window_start` (`window_start`),
  FOREIGN KEY (`client_id`) REFERENCES `oauth_clients`(`client_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='API频率限制表';

-- =====================================================
-- 初始化数据
-- =====================================================

-- 插入一个测试客户端（仅用于开发测试）
-- 注意：生产环境中应该删除此测试数据
INSERT INTO `oauth_clients` (
  `client_id`, 
  `client_secret`, 
  `client_name`, 
  `client_description`, 
  `contact_email`,
  `contact_person`,
  `created_by`,
  `rate_limit`
) VALUES (
  'test_client_12345',
  -- 密钥: test_secret_67890 (实际使用时会被加密)
  'pbkdf2:sha256:600000$test$test',
  '测试客户端',
  '用于开发测试的OAuth客户端',
  'test@example.com',
  '测试人员',
  'admin',
  1000
) ON DUPLICATE KEY UPDATE `client_name` = `client_name`;

-- =====================================================
-- 查询语句示例
-- =====================================================

-- 查看所有活跃的客户端
-- SELECT * FROM oauth_clients WHERE is_active = '1';

-- 查看某个客户端的所有有效令牌
-- SELECT * FROM oauth_tokens WHERE client_id = 'xxx' AND is_revoked = '0' AND expires_at > NOW();

-- 查看某个客户端的API调用统计
-- SELECT 
--   DATE(created_at) as date,
--   COUNT(*) as total_calls,
--   AVG(response_time) as avg_response_time,
--   SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) as error_count
-- FROM api_call_logs
-- WHERE client_id = 'xxx'
-- GROUP BY DATE(created_at)
-- ORDER BY date DESC;

-- 查看当前小时的请求频率
-- SELECT client_id, SUM(request_count) as total_requests
-- FROM api_rate_limits
-- WHERE window_start >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
-- GROUP BY client_id;

-- =====================================================
-- 清理过期数据的定时任务（建议定期执行）
-- =====================================================

-- 删除过期的令牌（保留30天）
-- DELETE FROM oauth_tokens WHERE expires_at < DATE_SUB(NOW(), INTERVAL 30 DAY);

-- 删除旧的API调用日志（保留90天）
-- DELETE FROM api_call_logs WHERE created_at < DATE_SUB(NOW(), INTERVAL 90 DAY);

-- 删除旧的频率限制记录（保留7天）
-- DELETE FROM api_rate_limits WHERE window_start < DATE_SUB(NOW(), INTERVAL 7 DAY);

