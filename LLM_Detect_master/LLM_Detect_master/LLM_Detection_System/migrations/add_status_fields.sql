-- 数据库迁移脚本：为 drawing_data 表添加状态字段
-- 执行时间：2025-11-21
-- 用途：支持检测任务队列和状态跟踪

USE angel;

-- 1. 添加 status 字段（检测状态）
ALTER TABLE drawing_data 
ADD COLUMN status VARCHAR(50) DEFAULT 'pending' COMMENT '检测状态: pending/processing/completed/failed';

-- 2. 添加 error_message 字段（错误信息）
ALTER TABLE drawing_data 
ADD COLUMN error_message TEXT COMMENT '检测失败时的错误信息';

-- 3. 添加 completed_at 字段（检测完成时间）
ALTER TABLE drawing_data 
ADD COLUMN completed_at VARCHAR(255) COMMENT '检测完成时间';

-- 4. 为已存在的记录设置默认状态为 completed（因为它们已经有检测结果）
UPDATE drawing_data 
SET status = 'completed' 
WHERE conclusion IS NOT NULL AND conclusion != '';

-- 5. 创建索引以提高查询性能
CREATE INDEX idx_status ON drawing_data(status);
CREATE INDEX idx_engineering_drawing_id ON drawing_data(engineering_drawing_id);

-- 6. 查看表结构
DESCRIBE drawing_data;

-- 7. 查看数据统计
SELECT 
    status,
    COUNT(*) as count
FROM drawing_data
GROUP BY status;

