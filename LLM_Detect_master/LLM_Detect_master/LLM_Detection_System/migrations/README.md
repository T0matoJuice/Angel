# 数据库迁移说明

## 概述

本目录包含数据库迁移脚本，用于更新数据库结构以支持新功能。

## 迁移脚本列表

### 1. add_status_fields.sql

**执行时间**: 2025-11-21
**用途**: 为 `drawing_data` 表添加状态跟踪字段，支持检测任务队列功能

**新增字段**:
- `status` (VARCHAR(50)): 检测状态 (pending/processing/completed/failed)
- `error_message` (TEXT): 检测失败时的错误信息
- `completed_at` (VARCHAR(255)): 检测完成时间

**索引**:
- `idx_status`: 状态字段索引，提高查询性能
- `idx_engineering_drawing_id`: 记录ID索引，提高查询性能

### 2. add_source_field.sql

**执行时间**: 2025-11-21
**用途**: 为 `drawing_data` 表添加数据来源字段，区分Web界面和API调用

**新增字段**:
- `source` (VARCHAR(50)): 数据来源 (Web/API)，默认值 'Web'

**影响范围**:
- Web界面上传：`source='Web'`
- API调用上传：`source='API'`

## 执行迁移

### 方法1：使用MySQL命令行

```bash
# 执行状态字段迁移
mysql -u root -p angel < migrations/add_status_fields.sql

# 执行来源字段迁移
mysql -u root -p angel < migrations/add_source_field.sql
```

### 方法2：使用MySQL Workbench

1. 打开MySQL Workbench
2. 连接到数据库
3. 打开 `add_status_fields.sql` 文件
4. 执行SQL脚本

### 方法3：使用Python脚本

```python
import mysql.connector
from pathlib import Path

# 连接数据库
conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='your_password',
    database='angel'
)

# 读取SQL文件
sql_file = Path('migrations/add_status_fields.sql')
sql_script = sql_file.read_text(encoding='utf-8')

# 执行SQL脚本
cursor = conn.cursor()
for statement in sql_script.split(';'):
    if statement.strip():
        cursor.execute(statement)

conn.commit()
cursor.close()
conn.close()

print("✅ 数据库迁移完成")
```

## 验证迁移

执行迁移后，可以使用以下SQL验证：

```sql
-- 查看表结构
DESCRIBE drawing_data;

-- 查看索引
SHOW INDEX FROM drawing_data;

-- 查看状态统计
SELECT
    status,
    COUNT(*) as count
FROM drawing_data
GROUP BY status;

-- 查看来源统计
SELECT
    source,
    COUNT(*) as count
FROM drawing_data
GROUP BY source;
```

## 回滚迁移

如果需要回滚迁移，可以执行以下SQL：

```sql
USE angel;

-- 回滚 add_status_fields.sql
DROP INDEX idx_status ON drawing_data;
DROP INDEX idx_engineering_drawing_id ON drawing_data;
ALTER TABLE drawing_data DROP COLUMN status;
ALTER TABLE drawing_data DROP COLUMN error_message;
ALTER TABLE drawing_data DROP COLUMN completed_at;

-- 回滚 add_source_field.sql
ALTER TABLE drawing_data DROP COLUMN source;
```

## 注意事项

1. **备份数据**: 执行迁移前请务必备份数据库
2. **测试环境**: 建议先在测试环境执行迁移，确认无误后再在生产环境执行
3. **权限检查**: 确保数据库用户有 ALTER TABLE 权限
4. **数据一致性**: 迁移脚本会将已有记录的状态设置为 'completed'（因为它们已经有检测结果）

## 相关文件

- `add_status_fields.sql`: 状态字段迁移SQL脚本
- `add_source_field.sql`: 来源字段迁移SQL脚本
- `../modules/drawing/models.py`: 更新后的数据模型
- `../modules/drawing/queue_manager.py`: 队列管理器实现
- `../modules/drawing/routes.py`: Web界面路由（设置 source='Web'）
- `../modules/api/drawing_api.py`: OAuth API路由（设置 source='API'）

