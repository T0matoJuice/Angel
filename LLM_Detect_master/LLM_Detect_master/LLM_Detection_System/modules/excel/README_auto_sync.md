# 自动定时同步功能说明

## 功能概述

系统已集成自动定时同步功能，每天凌晨自动同步前一天的人工判断工单性质数据，确保数据始终保持最新。

## 核心特性

### ✅ 自动同步
- **执行时间**：每天凌晨 01:00（可配置）
- **同步范围**：前一天的所有人工判断数据
- **自动重试**：失败后会在下次定时任务时重新尝试
- **日志记录**：完整的执行日志和状态追踪

### ✅ 手动触发
- 支持通过API手动触发同步
- 可指定任意日期范围
- 适用于补充历史数据或紧急同步

### ✅ 状态监控
- 实时查询同步状态
- 查看上次同步时间和结果
- 查看下次执行时间

## 配置说明

### 配置文件位置
`modules/common/config.py`

### 配置项说明

```python
# 定时同步任务配置
app.config['AUTO_SYNC_ENABLED'] = True  # 是否启用自动同步
app.config['AUTO_SYNC_HOUR'] = 1        # 每天执行时间：小时（0-23）
app.config['AUTO_SYNC_MINUTE'] = 0      # 每天执行时间：分钟（0-59）
```

### 配置示例

**示例1：每天凌晨1点执行**（默认）
```python
app.config['AUTO_SYNC_HOUR'] = 1
app.config['AUTO_SYNC_MINUTE'] = 0
```

**示例2：每天凌晨3点30分执行**
```python
app.config['AUTO_SYNC_HOUR'] = 3
app.config['AUTO_SYNC_MINUTE'] = 30
```

**示例3：禁用自动同步**
```python
app.config['AUTO_SYNC_ENABLED'] = False
```

## API接口

### 1. 查询同步状态

**接口**: `GET /api/sync/status`

**响应示例**:
```json
{
  "success": true,
  "data": {
    "last_sync_time": "2025-01-23 01:00:00",
    "last_sync_status": "success",
    "last_sync_stats": {
      "total": 158950,
      "updated": 91,
      "not_found": 158865,
      "errors": 0
    },
    "scheduler_running": true,
    "next_run_time": "2025-01-24 01:00:00"
  }
}
```

**字段说明**:
- `last_sync_time`: 上次同步时间
- `last_sync_status`: 上次同步状态（success/warning/error）
- `last_sync_stats`: 上次同步统计信息
- `scheduler_running`: 调度器是否运行中
- `next_run_time`: 下次执行时间

### 2. 手动触发同步

**接口**: `POST /api/sync/trigger`

**请求示例**:
```json
{
  "start_date": "2025-01-22",  // 可选，默认为昨天
  "end_date": "2025-01-22"      // 可选，默认为昨天
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "同步完成 (2025-01-22 ~ 2025-01-22)",
  "data": {
    "total": 150,
    "updated": 145,
    "not_found": 5,
    "errors": 0
  }
}
```

### 3. 查询同步配置

**接口**: `GET /api/sync/config`

**响应示例**:
```json
{
  "success": true,
  "data": {
    "enabled": true,
    "schedule_hour": 1,
    "schedule_minute": 0
  }
}
```

## 使用示例

### 使用curl测试API

**1. 查询同步状态**
```bash
curl http://localhost:5000/api/sync/status
```

**2. 手动触发同步（昨天的数据）**
```bash
curl -X POST http://localhost:5000/api/sync/trigger \
  -H "Content-Type: application/json"
```

**3. 手动触发同步（指定日期）**
```bash
curl -X POST http://localhost:5000/api/sync/trigger \
  -H "Content-Type: application/json" \
  -d '{"start_date": "2025-01-20", "end_date": "2025-01-22"}'
```

**4. 查询同步配置**
```bash
curl http://localhost:5000/api/sync/config
```

### 使用Python调用API

```python
import requests

# 查询同步状态
response = requests.get('http://localhost:5000/api/sync/status')
print(response.json())

# 手动触发同步
response = requests.post(
    'http://localhost:5000/api/sync/trigger',
    json={
        'start_date': '2025-01-22',
        'end_date': '2025-01-22'
    }
)
print(response.json())
```

## 系统启动

### 安装依赖

首次使用需要安装APScheduler：

```bash
pip install apscheduler>=3.10.0
```

或使用requirements.txt：

```bash
pip install -r requirements.txt
```

### 启动应用

```bash
cd d:\work\angel\Angel\LLM_Detect_master\LLM_Detect_master\LLM_Detection_System
python app.py
```

### 启动日志

系统启动时会显示：

```
============================================================
环境变量加载状态
============================================================
...
✅ Drawing检测队列管理器已初始化
✅ Excel检测队列管理器已初始化
✅ 定时同步任务调度器已初始化
✅ 定时同步任务已启动，每天 01:00 自动同步前一天数据
============================================================
==== 大模型智能检测系统 ====
访问地址: http://localhost:5000
============================================================
```

## 执行流程

### 自动同步流程

```
每天 01:00
    ↓
触发定时任务
    ↓
计算昨天日期（例如：2025-01-22）
    ↓
获取Bearer Token
    ↓
调用API获取人工判断数据
    ↓
遍历数据，更新数据库
    ↓
记录执行结果和统计信息
    ↓
等待下次执行（明天 01:00）
```

### 手动同步流程

```
调用 /api/sync/trigger
    ↓
解析请求参数（日期范围）
    ↓
获取Bearer Token
    ↓
调用API获取人工判断数据
    ↓
遍历数据，更新数据库
    ↓
返回执行结果
```

## 日志查看

### 控制台日志

定时任务执行时会在控制台输出：

```
============================================================
🕐 定时任务触发: 2025-01-23 01:00:00
📅 同步日期: 2025-01-22
============================================================
正在获取Bearer Token...
✓ Token获取成功: Bearer eyJhbGci...

正在获取人工判断数据 (2025-01-22 ~ 2025-01-22)...
✓ 成功获取 150 条人工判断数据

正在更新数据库...
✓ 数据库更新完成

✅ 同步完成:
   总记录数: 150
   成功更新: 145
   未找到工单: 5
   更新失败: 0
============================================================
```

### 应用日志

可以配置日志文件记录详细信息（可选）。

## 故障处理

### 常见问题

**Q1: 定时任务没有执行？**

检查项：
1. 确认 `AUTO_SYNC_ENABLED = True`
2. 查看控制台是否有错误信息
3. 调用 `/api/sync/status` 查看调度器状态

**Q2: 同步失败怎么办？**

解决方案：
1. 检查VPN连接是否正常
2. 查看错误日志确定失败原因
3. 使用手动触发API重新同步
4. 下次定时任务会自动重试

**Q3: 如何修改执行时间？**

步骤：
1. 修改 `config.py` 中的配置
2. 重启应用使配置生效

**Q4: 如何临时禁用自动同步？**

方法：
1. 设置 `AUTO_SYNC_ENABLED = False`
2. 重启应用

## 最佳实践

### 1. 监控同步状态

建议定期检查同步状态：

```bash
# 每天上午检查昨晚的同步结果
curl http://localhost:5000/api/sync/status
```

### 2. 补充历史数据

首次启用时，可以手动同步历史数据：

```bash
# 同步最近一周的数据
for i in {1..7}; do
  date=$(date -d "$i days ago" +%Y-%m-%d)
  curl -X POST http://localhost:5000/api/sync/trigger \
    -H "Content-Type: application/json" \
    -d "{\"start_date\": \"$date\", \"end_date\": \"$date\"}"
  sleep 5
done
```

### 3. 设置合理的执行时间

建议选择：
- **凌晨1-5点**：系统负载较低
- **避开业务高峰期**
- **确保VPN稳定时段**

### 4. 定期检查日志

建议：
- 每周检查一次同步日志
- 关注失败记录
- 及时处理异常情况

## 技术架构

### 核心组件

1. **scheduler.py**: 定时任务调度器
   - 使用APScheduler实现
   - 支持Cron表达式
   - 后台运行，不阻塞主线程

2. **sync_api.py**: 同步管理API
   - 提供RESTful接口
   - 支持状态查询和手动触发

3. **sync_manual_judgment.py**: 同步逻辑
   - API调用和数据处理
   - 数据库更新

### 依赖关系

```
app.py
  ↓
scheduler.py (初始化调度器)
  ↓
sync_manual_judgment.py (执行同步)
  ↓
API接口 + 数据库
```

## 版本历史

- **v1.0**（2025-01-23）：初始版本
  - 实现每日自动同步
  - 提供手动触发API
  - 支持状态查询

## 总结

✅ **自动化**：每天自动同步，无需人工干预  
✅ **可靠性**：失败自动重试，完整日志记录  
✅ **灵活性**：支持手动触发和配置调整  
✅ **可监控**：实时状态查询，执行结果追踪  

现在你的系统已经具备完整的自动同步能力！🎉
