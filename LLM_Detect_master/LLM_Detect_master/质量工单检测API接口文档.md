# 质量工单检测 API 接口文档

## 概述

本文档提供质量工单检测系统的外部API接口说明，包括Excel文件上传和JSON数据批量上传两种方式。

**基础信息：**
- 基础URL：`http://<服务器地址>:5000`
- 认证方式：OAuth 2.0 Bearer Token
- 请求编码：UTF-8
- 响应格式：JSON

---

## 认证说明

### 获取访问令牌

**接口地址：** `POST /api/oauth/token`

**请求参数：**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| client_id | string | 是 | 客户端ID |
| client_secret | string | 是 | 客户端密钥 |
| grant_type | string | 是 | 固定值：`client_credentials` |

**请求示例：**

```http
POST /api/oauth/token HTTP/1.1
Content-Type: application/x-www-form-urlencoded

client_id=your_client_id&client_secret=your_client_secret&grant_type=client_credentials
```

**响应示例：**

```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 3600,
    "scope": "excel:upload"
}
```

---

## 接口一：Excel文件上传

### 基本信息

**接口地址：** `POST /api/v1/excel/upload`

**接口说明：** 上传Excel格式的质量工单文件，系统自动解析、入库并启动AI检测任务

**认证方式：** OAuth 2.0 Bearer Token

### 请求参数

**Headers:**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| Authorization | string | 是 | Bearer <access_token> |
| Content-Type | string | 是 | multipart/form-data |

**Form Data:**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| file | file | 是 | Excel文件（.xlsx或.xls格式） |
| batch_size | integer | 否 | 批量处理大小，默认50，范围1-200 |
| account | string | 否 | 操作账号，用于记录 |
| datatime | string | 否 | 数据时间，格式：YYYY-MM-DD HH:MM:SS |

**Excel文件要求：**

- 文件格式：`.xlsx` 或 `.xls`
- 文件大小：建议不超过50MB
- 数据列数：83列（系统会自动映射字段）
- 必填字段：19个核心字段（见下文）

**19个必填字段清单：**

1. 工单单号
2. 工单性质
3. 判定依据
4. 保内保外
5. 批次入库日期
6. 安装日期
7. 购机日期
8. 产品名称
9. 开发主体
10. 故障部位名称
11. 故障组
12. 故障类别
13. 服务项目或故障现象
14. 维修方式
15. 旧件名称
16. 新件名称
17. 来电内容
18. 现场诊断故障现象
19. 处理方案简述或备注

### 请求示例

**Python 示例：**

```python
import requests

# 1. 获取访问令牌
token_response = requests.post(
    'http://your-server:5000/api/oauth/token',
    data={
        'client_id': 'your_client_id',
        'client_secret': 'your_client_secret',
        'grant_type': 'client_credentials'
    }
)
access_token = token_response.json()['access_token']

# 2. 上传Excel文件
with open('workorder.xlsx', 'rb') as f:
    response = requests.post(
        'http://your-server:5000/api/v1/excel/upload',
        headers={
            'Authorization': f'Bearer {access_token}'
        },
        files={
            'file': ('workorder.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        },
        data={
            'batch_size': 50,
            'account': '张三',
            'datatime': '2024-12-02 15:00:00'
        }
    )
    
print(response.json())
```

**cURL 示例：**

```bash
# 1. 获取访问令牌
TOKEN=$(curl -X POST http://your-server:5000/api/oauth/token \
  -d "client_id=your_client_id" \
  -d "client_secret=your_client_secret" \
  -d "grant_type=client_credentials" \
  | jq -r '.access_token')

# 2. 上传文件
curl -X POST http://your-server:5000/api/v1/excel/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@workorder.xlsx" \
  -F "batch_size=50" \
  -F "account=张三" \
  -F "datatime=2024-12-02 15:00:00"
```

### 响应说明

**成功响应（200 OK）：**

```json
{
    "success": true,
    "task_id": "20241202_150000_workorder.xlsx",
    "filename": "workorder.xlsx",
    "rows_count": 100,
    "status": "pending",
    "message": "文件上传成功，检测任务已加入队列"
}
```

**响应字段说明：**

| 字段名 | 类型 | 说明 |
|--------|------|------|
| success | boolean | 是否成功 |
| task_id | string | 任务ID，用于查询检测状态 |
| filename | string | 原始文件名 |
| rows_count | integer | 数据行数 |
| status | string | 任务状态：pending（排队中） |
| message | string | 提示信息 |

**错误响应：**

```json
{
    "error": "invalid_file_type",
    "error_description": "只支持Excel格式文件(.xlsx, .xls)"
}
```

**常见错误代码：**

| 错误代码 | HTTP状态码 | 说明 |
|----------|-----------|------|
| invalid_token | 401 | Token无效或已过期 |
| missing_file | 400 | 请求中没有文件 |
| empty_filename | 400 | 文件名为空 |
| invalid_file_type | 400 | 文件格式不支持 |
| invalid_batch_size | 400 | batch_size参数超出范围 |
| excel_parse_error | 400 | Excel文件格式错误 |

---

## 接口二：JSON数据批量上传

### 基本信息

**接口地址：** `POST /excel/quality-dataupload`

**接口说明：** 直接提交JSON格式的工单数据，无需Excel文件，适合系统间数据对接

**认证方式：** OAuth 2.0 Bearer Token

### 请求参数

**Headers:**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| Authorization | string | 是 | Bearer <access_token> |
| Content-Type | string | 是 | application/json |

**Request Body (JSON):**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| account | string | 否 | 操作账号，用于记录（默认：api_user） |
| filename | string | 否 | 批次标识名称（默认：api_upload） |
| workorders | array | 是 | 工单数据数组，每个元素包含19个必填字段 |

**workorders数组元素（每条工单）必填字段：**

| 字段名 | 类型 | 必填 | 示例值 |
|--------|------|------|--------|
| 工单单号 | string | 是 | WO001 |
| 工单性质 | string | 是 | 质量问题 |
| 判定依据 | string | 是 | 技术鉴定 |
| 保内保外 | string | 是 | 保内 |
| 批次入库日期 | string | 是 | 2024-12-02 15:00:00 |
| 安装日期 | string | 是 | 2024-01-15 |
| 购机日期 | string | 是 | 2024-01-10 |
| 产品名称 | string | 是 | 净水机A型 |
| 开发主体 | string | 是 | 研发部 |
| 故障部位名称 | string | 是 | 滤芯 |
| 故障组 | string | 是 | 净水机 |
| 故障类别 | string | 是 | 滤芯类 |
| 服务项目或故障现象 | string | 是 | 滤芯堵塞 |
| 维修方式 | string | 是 | 上门维修 |
| 旧件名称 | string | 是 | 复合滤芯A |
| 新件名称 | string | 是 | 复合滤芯B |
| 来电内容 | string | 是 | 机器不出水 |
| 现场诊断故障现象 | string | 是 | 滤芯严重堵塞 |
| 处理方案简述或备注 | string | 是 | 更换滤芯后恢复正常 |

**注意事项：**
- 可以一次性上传任意数量的工单数据（建议单次不超过1000条）
- 系统会自动分批处理（每批50条）
- 所有字段值类型必须为字符串
- 空字符串 `""` 也是合法值

### 请求示例

**Python 示例：**

```python
import requests
from datetime import datetime

# 1. 获取访问令牌
token_response = requests.post(
    'http://your-server:5000/api/oauth/token',
    data={
        'client_id': 'your_client_id',
        'client_secret': 'your_client_secret',
        'grant_type': 'client_credentials'
    }
)
access_token = token_response.json()['access_token']

# 2. 准备工单数据
data = {
    "account": "张三",
    "filename": "batch_001",
    "workorders": [
        {
            "工单单号": "WO001",
            "工单性质": "质量问题",
            "判定依据": "技术鉴定",
            "保内保外": "保内",
            "批次入库日期": "2024-12-02 15:00:00",
            "安装日期": "2024-01-15",
            "购机日期": "2024-01-10",
            "产品名称": "净水设备 反渗透厨下式净水机",
            "开发主体": "电商事业部",
            "故障部位名称": "复合滤芯",
            "故障组": "净水机",
            "故障类别": "滤芯类",
            "服务项目或故障现象": "滤芯堵塞",
            "维修方式": "上门维修",
            "旧件名称": "复合滤芯A",
            "新件名称": "复合滤芯B",
            "来电内容": "机器不出水，请师傅上门检查",
            "现场诊断故障现象": "滤芯严重堵塞",
            "处理方案简述或备注": "更换滤芯后机器恢复正常"
        },
        # 可以添加更多工单...
    ]
}

# 3. 提交数据
response = requests.post(
    'http://your-server:5000/excel/quality-dataupload',
    headers={
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    },
    json=data
)

result = response.json()
print(f"批次ID: {result['batch_id']}")
print(f"成功入库: {result['success_count']} 条")
```

**cURL 示例：**

```bash
curl -X POST http://your-server:5000/excel/quality-dataupload \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "account": "张三",
    "filename": "batch_001",
    "workorders": [
        {
            "工单单号": "WO001",
            "工单性质": "质量问题",
            "判定依据": "技术鉴定",
            "保内保外": "保内",
            "批次入库日期": "2024-12-02 15:00:00",
            "安装日期": "2024-01-15",
            "购机日期": "2024-01-10",
            "产品名称": "净水设备 反渗透厨下式净水机",
            "开发主体": "电商事业部",
            "故障部位名称": "复合滤芯",
            "故障组": "净水机",
            "故障类别": "滤芯类",
            "服务项目或故障现象": "滤芯堵塞",
            "维修方式": "上门维修",
            "旧件名称": "复合滤芯A",
            "新件名称": "复合滤芯B",
            "来电内容": "机器不出水",
            "现场诊断故障现象": "滤芯严重堵塞",
            "处理方案简述或备注": "更换滤芯后机器恢复正常"
        }
    ]
}'
```

### 响应说明

**成功响应（200 OK）：**

```json
{
    "success": true,
    "batch_id": "batch_001_20241202_150000",
    "total_received": 100,
    "success_count": 100,
    "failed_count": 0,
    "errors": null,
    "message": "成功入库 100 条工单，检测任务已启动（每批50条）",
    "queue_status": "added"
}
```

**响应字段说明：**

| 字段名 | 类型 | 说明 |
|--------|------|------|
| success | boolean | 是否成功 |
| batch_id | string | 批次ID，用于查询检测状态 |
| total_received | integer | 接收到的工单总数 |
| success_count | integer | 成功入库的数量 |
| failed_count | integer | 失败数量 |
| errors | array/null | 错误详情（如有） |
| message | string | 提示信息 |
| queue_status | string | 队列状态：added（已加入） |

**部分失败响应（200 OK）：**

```json
{
    "success": true,
    "batch_id": "batch_001_20241202_150000",
    "total_received": 100,
    "success_count": 98,
    "failed_count": 2,
    "errors": [
        {
            "index": 5,
            "workorder_no": "WO006",
            "error": "缺少必填字段: 产品名称"
        },
        {
            "index": 23,
            "workorder_no": "WO024",
            "error": "工单单号重复"
        }
    ],
    "message": "成功入库 98 条工单，检测任务已启动（每批50条）",
    "queue_status": "added"
}
```

**错误响应：**

```json
{
    "error": "missing_required_field",
    "error_description": "第1条工单缺少必填字段: 工单单号",
    "workorder_index": 0
}
```

**常见错误代码：**

| 错误代码 | HTTP状态码 | 说明 |
|----------|-----------|------|
| invalid_token | 401 | Token无效或已过期 |
| missing_data | 400 | 请求体为空 |
| missing_workorders | 400 | 缺少workorders字段 |
| invalid_format | 400 | workorders不是数组格式 |
| empty_workorders | 400 | 工单数据为空 |
| missing_required_field | 400 | 缺少必填字段 |
| upload_failed | 500 | 服务器处理失败 |

---

## 接口三：查询检测状态

### 基本信息

**接口地址：** `POST /excel/quality-process`

**接口说明：** 查询工单检测任务的执行状态和进度

**认证方式：** OAuth 2.0 Bearer Token（API调用）或 Web登录（网页调用）

### 请求参数

**Headers:**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| Authorization | string | 是* | Bearer <access_token>（API调用时必填） |
| Content-Type | string | 是 | application/json |

**Request Body (JSON):**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| filename | string | 是 | 批次ID或任务ID |
| unique_filename | string | 否 | 唯一文件名（推荐传递，避免解析错误） |

**参数说明：**
- Excel上传返回的 `task_id` → 传给 `filename`
- JSON上传返回的 `batch_id` → 同时传给 `filename` 和 `unique_filename`

### 请求示例

**Python 示例：**

```python
import requests
import time

# 查询状态
response = requests.post(
    'http://your-server:5000/excel/quality-process',
    headers={
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    },
    json={
        'filename': 'batch_001_20241202_150000',
        'unique_filename': 'batch_001_20241202_150000'  # JSON上传必须传此参数
    }
)

result = response.json()
print(f"状态: {result['status']}")

# 轮询等待完成
while result.get('status') in ['pending', 'processing']:
    time.sleep(2)
    response = requests.post(...)
    result = response.json()
    
if result.get('status') == 'completed':
    print(f"检测完成！")
    print(f"结果文件: {result['excel_filename']}")
```

### 响应说明

**排队中（200 OK）：**

```json
{
    "success": false,
    "status": "pending",
    "message": "检测任务排队中，请稍候..."
}
```

**检测中（200 OK）：**

```json
{
    "success": false,
    "status": "processing",
    "message": "正在检测中，请稍候..."
}
```

**检测完成（200 OK）：**

```json
{
    "success": true,
    "status": "completed",
    "message": "质量工单检测完成",
    "excel_filename": "quality_result_20241202_150520.xlsx",
    "csv_filename": "quality_result_20241202_150520.csv",
    "rows_processed": 100,
    "completed_count": 100,
    "total_count": 100,
    "unique_filename": "batch_001_20241202_150000"
}
```

**检测失败（200 OK）：**

```json
{
    "success": false,
    "status": "failed",
    "message": "检测失败，请重新上传文件"
}
```

**状态说明：**

| 状态值 | 说明 | 建议操作 |
|--------|------|---------|
| pending | 队列中等待 | 继续轮询 |
| processing | 正在检测中 | 继续轮询 |
| completed | 检测完成 | 下载结果文件 |
| failed | 检测失败 | 查看日志或重新提交 |

---

## 下载检测结果

### 基本信息

**接口地址：** `GET /excel/download/<filename>`

**接口说明：** 下载检测完成后生成的结果文件

**认证方式：** 需要Web登录会话（建议通过网页界面下载）

### 请求示例

**浏览器访问：**

```
http://your-server:5000/excel/download/quality_result_20241202_150520.xlsx
```

**Python 示例：**

```python
import requests

# 注意：此接口需要Web登录会话，不支持OAuth Token
# 建议先通过Web界面登录，然后使用session下载

session = requests.Session()
# 先登录...

response = session.get(
    'http://your-server:5000/excel/download/quality_result_20241202_150520.xlsx'
)

with open('result.xlsx', 'wb') as f:
    f.write(response.content)
```

---

## 完整工作流程示例

### Python完整流程

```python
import requests
import time

BASE_URL = "http://your-server:5000"
CLIENT_ID = "your_client_id"
CLIENT_SECRET = "your_client_secret"

# ========== 步骤1：获取访问令牌 ==========
print("步骤1：获取访问令牌")
token_response = requests.post(
    f"{BASE_URL}/api/oauth/token",
    data={
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'client_credentials'
    }
)
access_token = token_response.json()['access_token']
print(f"✓ Token获取成功")

# ========== 步骤2：上传数据 ==========
print("\n步骤2：上传工单数据")
upload_data = {
    "account": "测试用户",
    "filename": "test_batch",
    "workorders": [
        {
            "工单单号": "WO001",
            "工单性质": "质量问题",
            "判定依据": "技术鉴定",
            "保内保外": "保内",
            "批次入库日期": "2024-12-02 15:00:00",
            "安装日期": "2024-01-15",
            "购机日期": "2024-01-10",
            "产品名称": "净水设备",
            "开发主体": "电商事业部",
            "故障部位名称": "复合滤芯",
            "故障组": "净水机",
            "故障类别": "滤芯类",
            "服务项目或故障现象": "滤芯堵塞",
            "维修方式": "上门维修",
            "旧件名称": "复合滤芯A",
            "新件名称": "复合滤芯B",
            "来电内容": "机器不出水",
            "现场诊断故障现象": "滤芯严重堵塞",
            "处理方案简述或备注": "更换滤芯后恢复正常"
        }
    ]
}

upload_response = requests.post(
    f"{BASE_URL}/excel/quality-dataupload",
    headers={
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    },
    json=upload_data
)

result = upload_response.json()
batch_id = result['batch_id']
print(f"✓ 数据上传成功，批次ID: {batch_id}")
print(f"  入库: {result['success_count']} 条")

# ========== 步骤3：轮询检测状态 ==========
print("\n步骤3：查询检测状态")
max_attempts = 60  # 最多查询60次（2分钟）
attempt = 0

while attempt < max_attempts:
    status_response = requests.post(
        f"{BASE_URL}/excel/quality-process",
        headers={
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        },
        json={
            'filename': batch_id,
            'unique_filename': batch_id
        }
    )
    
    status_result = status_response.json()
    status = status_result.get('status')
    
    if status == 'pending':
        print(f"  [{attempt + 1}] 队列中等待...")
    elif status == 'processing':
        print(f"  [{attempt + 1}] 检测中...")
    elif status == 'completed':
        print(f"✓ 检测完成！")
        print(f"  结果文件: {status_result['excel_filename']}")
        break
    elif status == 'failed':
        print(f"✗ 检测失败")
        break
    
    attempt += 1
    time.sleep(2)

print("\n流程完成")
```

---

## 错误处理建议

### 1. Token过期处理

```python
def call_api_with_retry(url, headers, **kwargs):
    """自动重试的API调用"""
    response = requests.post(url, headers=headers, **kwargs)
    
    if response.status_code == 401:
        # Token过期，重新获取
        new_token = get_new_token()
        headers['Authorization'] = f'Bearer {new_token}'
        response = requests.post(url, headers=headers, **kwargs)
    
    return response
```

### 2. 网络异常处理

```python
import time
from requests.exceptions import RequestException

def upload_with_retry(data, max_retries=3):
    """带重试的上传"""
    for attempt in range(max_retries):
        try:
            response = requests.post(url, json=data, timeout=30)
            return response.json()
        except RequestException as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # 指数退避
                continue
            raise
```

### 3. 部分失败处理

```python
result = upload_response.json()

if result.get('failed_count', 0) > 0:
    print(f"警告：{result['failed_count']} 条数据入库失败")
    
    # 记录失败的工单
    failed_orders = []
    for error in result.get('errors', []):
        failed_orders.append({
            'index': error['index'],
            'workorder_no': error['workorder_no'],
            'reason': error['error']
        })
    
    # 可以选择重试失败的工单
    retry_upload(failed_orders)
```

---

## 附录

### A. 字段映射说明

系统使用83字段的Excel格式，自动映射到3张数据表：
- `WorkorderData`：核心检测字段
- `WorkorderUselessdata1`：辅助字段（第1组）
- `WorkorderUselessdata2`：辅助字段（第2组）

详细字段映射请参考：`modules/excel/field_mapping.py`

### B. 检测规则说明

AI检测基于以下3个核心字段：
1. **故障现象**（服务项目或故障现象）
2. **客户投诉内容**（来电内容）
3. **问题描述**（现场诊断故障现象、处理方案简述或备注）

检测结果包含：
- 检测结论（有效/无效）
- 依据说明
- 相似工单参考

### C. 性能建议

- 单次上传建议不超过1000条工单
- 批处理大小建议保持默认50条
- 查询状态建议间隔2-5秒
- 大批量数据建议分多次上传

### D. 联系支持

如有问题，请联系技术支持：
- 邮箱：support@example.com
- 文档更新日期：2024-12-02
