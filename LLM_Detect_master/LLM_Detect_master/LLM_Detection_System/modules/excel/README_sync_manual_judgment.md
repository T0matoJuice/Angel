# 人工判断工单性质数据同步工具

## 功能说明

该工具用于从远程API获取人工判断的工单性质数据，并更新到本地数据库的 `workorder_data` 表中。

### 主要功能

1. **获取Token认证**：通过登录API获取Bearer Token
2. **获取人工判断数据**：调用数据查询API获取指定日期范围内的工单数据
3. **更新数据库**：根据工单单号（workAlone）匹配本地数据库记录，更新 `workOrderNature_correct` 字段

## 文件说明

### 1. `sync_manual_judgment.py`
主要的同步脚本，负责完整的数据同步流程。

**功能**：
- 获取Bearer Token认证
- 调用API获取人工判断的工单数据
- 更新数据库中对应工单的 `workOrderNature_correct` 字段

### 2. `add_workorder_nature_correct_field.py`
数据库迁移脚本，用于添加新字段。

**功能**：
- 在 `workorder_data` 表中添加 `workOrderNature_correct` 字段

### 3. `models.py`（已更新）
数据库模型文件，已添加 `workOrderNature_correct` 字段定义。

## 使用步骤

### 步骤1：添加数据库字段（首次使用）

首次使用前需要在数据库中添加新字段：

```bash
# 进入项目目录
cd d:\work\angel\Angel\LLM_Detect_master\LLM_Detect_master\LLM_Detection_System

# 执行数据库迁移
python modules\excel\add_workorder_nature_correct_field.py
```

### 步骤2：连接VPN

**重要**：由于API接口需要连接内部VPN，请确保在执行同步前已连接VPN。

### 步骤3：执行数据同步

```bash
# 同步指定日期的数据
python modules\excel\sync_manual_judgment.py --start-date 2025-01-01 --end-date 2025-01-01

# 同步日期范围的数据
python modules\excel\sync_manual_judgment.py --start-date 2025-01-01 --end-date 2025-01-31
```

### 参数说明

- `--start-date`：开始日期，格式：YYYY-MM-DD（必填）
- `--end-date`：结束日期，格式：YYYY-MM-DD（必填）

## API接口说明

### 1. 登录接口（获取Token）

- **URL**：`http://qmstest.angelgroup.com.cn:8080/ssoServer/oauth/login`
- **方法**：POST
- **Header**：
  - `Authorization`: `Basic cXVhbGl0eURhdGE6JDJhJDEwJGZDOU40WUxOWUlCLzgyM3ZQcjd2b2U3dWtndUtHSkRNYzdya210UmkxeHVCQ0lZZUcwMkJX`
- **Body**：
  ```json
  {
    "username": "ai",
    "password": "Ai@2025."
  }
  ```
- **响应**：包含 `access_token` 字段

### 2. 数据查询接口

- **URL**：`http://qmstest.angelgroup.com.cn:8080/qualityDataAnalysis/baseData/crmMaintenanceData/selectJudgedOriginal`
- **方法**：GET
- **Header**：
  - `Authorization`: `Bearer {token}`（从登录接口获取）
- **Query参数**：
  - `maintenanceTimeStart`: 开始日期（YYYY-MM-DD）
  - `maintenanceTimeEnd`: 结束日期（YYYY-MM-DD）
- **响应**：包含工单数据数组，每条数据包含：
  - `workAlone`: 工单单号
  - `workOrderNature`: 工单性质（人工判断结果）

## 数据库字段说明

### workorder_data 表新增字段

| 字段名 | 类型 | 说明 | 备注 |
|--------|------|------|------|
| `workOrderNature_correct` | VARCHAR(255) | 工单性质（人工判断结果） | 从API获取的人工判断数据 |

### 字段对比

- `workOrderNature`：AI判断的工单性质（原有字段）
- `workOrderNature_correct`：人工判断的工单性质（新增字段）

## 执行流程

```
1. 连接VPN
   ↓
2. 执行脚本
   ↓
3. 获取Bearer Token
   ↓
4. 调用API获取人工判断数据
   ↓
5. 遍历每条数据
   ↓
6. 根据 workAlone 查找数据库记录
   ↓
7. 更新 workOrderNature_correct 字段
   ↓
8. 提交数据库更改
   ↓
9. 输出统计信息
```

## 输出示例

```
============================================================
人工判断工单性质数据同步工具
============================================================
正在获取Bearer Token...
✓ Token获取成功: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

正在获取人工判断数据 (2025-01-01 ~ 2025-01-01)...
✓ 成功获取 150 条人工判断数据

正在更新数据库...
  已更新 100 条记录...
  ⚠ 未找到工单: WO0014674999

✓ 数据库更新完成

============================================================
同步完成统计
============================================================
总记录数:     150
成功更新:     145
未找到工单:   5
更新失败:     0
============================================================
```

## 注意事项

1. **VPN连接**：必须连接内部VPN才能访问API接口
2. **数据库连接**：确保 `.env` 文件中的数据库配置正确
3. **首次使用**：首次使用前必须执行数据库迁移脚本添加新字段
4. **工单匹配**：只会更新数据库中已存在的工单记录，API返回的新工单不会被插入
5. **重复执行**：可以重复执行同步，会覆盖已有的 `workOrderNature_correct` 值

## 错误处理

### 常见错误及解决方案

| 错误信息 | 原因 | 解决方案 |
|---------|------|---------|
| `Connection refused` | 未连接VPN | 连接内部VPN后重试 |
| `Unauthorized` | Token过期或无效 | 脚本会自动重新获取Token |
| `未找到工单` | 数据库中不存在该工单 | 正常情况，会在统计中显示 |
| `Duplicate column name` | 字段已存在 | 无需重复执行迁移脚本 |

## 开发说明

### 依赖包

- `requests`：HTTP请求库
- `sqlalchemy`：数据库ORM
- `flask`：Web框架（用于应用上下文）

### 扩展功能

如需扩展功能，可以修改 `ManualJudgmentSyncer` 类：

1. **添加更多字段**：在 `fetch_manual_judgment_data` 方法中提取更多字段
2. **修改查询条件**：在 `update_database` 方法中修改查询逻辑
3. **添加日志记录**：集成日志系统记录详细操作

## 版本历史

- **v1.0**（2025-01-23）：初始版本
  - 实现基本的数据同步功能
  - 支持按日期范围查询
  - 添加统计信息输出
