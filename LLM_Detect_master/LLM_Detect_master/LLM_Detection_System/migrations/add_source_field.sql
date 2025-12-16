-- ============================================================
-- 数据库迁移脚本：添加 source 字段
-- 日期：2025-11-21
-- 目的：区分数据来源（Web界面 vs API调用）
-- ============================================================

USE angel;

-- 1. 添加 source 字段
ALTER TABLE drawing_data 
ADD COLUMN source VARCHAR(50) DEFAULT 'Web' COMMENT '数据来源: Web/API';

-- 2. 为已存在的记录设置默认值
UPDATE drawing_data 
SET source = 'Web' 
WHERE source IS NULL;

-- 3. 验证字段添加成功
SELECT 
    COLUMN_NAME, 
    COLUMN_TYPE, 
    COLUMN_DEFAULT, 
    COLUMN_COMMENT 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_SCHEMA = 'angel' 
  AND TABLE_NAME = 'drawing_data' 
  AND COLUMN_NAME = 'source';

-- 4. 查看数据分布
SELECT source, COUNT(*) as count 
FROM drawing_data 
GROUP BY source;

