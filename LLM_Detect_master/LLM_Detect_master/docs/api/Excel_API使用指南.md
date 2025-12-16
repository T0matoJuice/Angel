# Excel质量工单检测 API 使用指南

## 📋 概述

Excel质量工单检测API提供了与Drawing模块相同的OAuth 2.0认证机制，允许外部系统安全地上传Excel文件并获取AI检测结果。

---

## 🔐 认证流程

### 1. 获取访问令牌

**接口地址**: `POST /api/oauth/token`

**请求示例**:
```bash
curl -X POST http://localhost:5000/api/oauth/token \
  -d "client_id=your_client_id" \
  -d "client_secret=your_client_secret" \
  -d "grant_type=client_credentials"
```

**响应示例**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "scope": "excel:upload excel:query"
}
```

---

## 📤 API接口列表

### 1. 上传Excel文件

**接口地址**: `POST /api/v1/excel/upload`

**请求头**:
```
Authorization: Bearer {access_token}
Content-Type: multipart/form-data
```

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | 是 | Excel文件(.xlsx, .xls) |
| batch_size | Integer | 否 | 批量处理大小(1-200)，默认50 |

**请求示例**:
```bash
curl -X POST http://localhost:5000/api/v1/excel/upload \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -F "file=@workorder.xlsx" \
  -F "batch_size=50"
```

**成功响应** (200):
```json
{
  "success": true,
  "task_id": "20251201_120000_workorder.xlsx",
  "filename": "workorder.xlsx",
  "rows_count": 100,
  "batch_size": 50,
  "status": "pending",
  "message": "文件上传成功，检测任务已加入队列"
}
```

**错误响应**:
```json
{
  "error": "invalid_file_type",
  "error_description": "只支持Excel格式文件(.xlsx, .xls)"
}
```

---

### 2. 查询检测状态

**接口地址**: `GET /api/v1/excel/status/{task_id}`

**请求头**:
```
Authorization: Bearer {access_token}
```

**请求示例**:
```bash
curl -X GET http://localhost:5000/api/v1/excel/status/20251201_120000_workorder.xlsx \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**响应示例 - 排队中**:
```json
{
  "success": true,
  "task_id": "20251201_120000_workorder.xlsx",
  "status": "pending",
  "rows_total": 100,
  "rows_processed": 0,
  "progress": 0,
  "queue_size": 3,
  "message": "任务排队中，请稍候..."
}
```

**响应示例 - 处理中**:
```json
{
  "success": true,
  "task_id": "20251201_120000_workorder.xlsx",
  "status": "processing",
  "rows_total": 100,
  "rows_processed": 50,
  "progress": 50,
  "message": "正在检测中，请稍候..."
}
```

**响应示例 - 完成**:
```json
{
  "success": true,
  "task_id": "20251201_120000_workorder.xlsx",
  "status": "completed",
  "rows_total": 100,
  "rows_processed": 100,
  "progress": 100,
  "result_files": {
    "csv": "quality_result_20251201_120030.csv",
    "excel": "quality_result_20251201_120030.xlsx"
  },
  "message": "检测完成"
}
```

---

### 3. 获取检测结果

**接口地址**: `GET /api/v1/excel/result/{task_id}`

**请求头**:
```
Authorization: Bearer {access_token}
```

**请求示例**:
```bash
curl -X GET http://localhost:5000/api/v1/excel/result/20251201_120000_workorder.xlsx \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**响应示例**:
```json
{
  "success": true,
  "task_id": "20251201_120000_workorder.xlsx",
  "rows_total": 100,
  "columns": [
    "工单单号", "工单性质", "判定依据", "保内保外", 
    "批次入库日期", "安装日期", "购机日期", "产品名称",
    "开发主体", "故障部位名称", "故障组", "故障类别",
    "服务项目或故障现象", "维修方式", "旧件名称", "新件名称",
    "来电内容", "现场诊断故障现象", "处理方案简述或备注"
  ],
  "results": [
    {
      "工单单号": "WO001",
      "工单性质": "质量问题",
      "判定依据": "根据GB/T 19001标准，该故障属于产品质量问题...",
      "保内保外": "保内",
      "批次入库日期": "2024-01-15",
      "安装日期": "2024-02-01",
      "购机日期": "2024-01-20",
      "产品名称": "洗衣机XQG80-B1426",
      "开发主体": "海尔",
      "故障部位名称": "电机",
      "故障组": "电气故障",
      "故障类别": "电机不转",
      "服务项目或故障现象": "洗衣机无法启动，电机不转",
      "维修方式": "更换电机",
      "旧件名称": "电机组件A型",
      "新件名称": "电机组件B型",
      "来电内容": "用户反馈洗衣机无法工作",
      "现场诊断故障现象": "检查发现电机烧毁",
      "处理方案简述或备注": "更换电机后测试正常"
    }
  ]
}
```

---

### 4. 下载结果文件

**接口地址**: `GET /api/v1/excel/download/{task_id}`

**请求头**:
```
Authorization: Bearer {access_token}
```

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| format | String | 否 | 文件格式: excel(默认) 或 csv |

**请求示例 - 下载Excel**:
```bash
curl -X GET "http://localhost:5000/api/v1/excel/download/20251201_120000_workorder.xlsx?format=excel" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -o result.xlsx
```

**请求示例 - 下载CSV**:
```bash
curl -X GET "http://localhost:5000/api/v1/excel/download/20251201_120000_workorder.xlsx?format=csv" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -o result.csv
```

---

### 5. 健康检查

**接口地址**: `GET /api/v1/excel/health`

**说明**: 无需认证

**请求示例**:
```bash
curl -X GET http://localhost:5000/api/v1/excel/health
```

**响应示例**:
```json
{
  "status": "ok",
  "service": "Excel Quality Inspection API",
  "version": "1.0.0"
}
```

---

## 🔄 完整调用流程示例

### Python示例

```python
import requests
import time

# 配置
BASE_URL = "http://localhost:5000"
CLIENT_ID = "your_client_id"
CLIENT_SECRET = "your_client_secret"

# 1. 获取访问令牌
def get_access_token():
    response = requests.post(
        f"{BASE_URL}/api/oauth/token",
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "client_credentials"
        }
    )
    return response.json()["access_token"]

# 2. 上传Excel文件
def upload_excel(access_token, file_path):
    headers = {"Authorization": f"Bearer {access_token}"}
    files = {"file": open(file_path, "rb")}
    data = {"batch_size": 50}
    
    response = requests.post(
        f"{BASE_URL}/api/v1/excel/upload",
        headers=headers,
        files=files,
        data=data
    )
    return response.json()

# 3. 轮询检测状态
def wait_for_completion(access_token, task_id):
    headers = {"Authorization": f"Bearer {access_token}"}
    
    while True:
        response = requests.get(
            f"{BASE_URL}/api/v1/excel/status/{task_id}",
            headers=headers
        )
        data = response.json()
        
        print(f"状态: {data['status']}, 进度: {data['progress']}%")
        
        if data['status'] == 'completed':
            return data
        elif data['status'] == 'failed':
            raise Exception("检测失败")
        
        time.sleep(5)  # 每5秒查询一次

# 4. 获取结果
def get_result(access_token, task_id):
    headers = {"Authorization": f"Bearer {access_token}"}
    
    response = requests.get(
        f"{BASE_URL}/api/v1/excel/result/{task_id}",
        headers=headers
    )
    return response.json()

# 5. 下载结果文件
def download_result(access_token, task_id, output_path):
    headers = {"Authorization": f"Bearer {access_token}"}
    
    response = requests.get(
        f"{BASE_URL}/api/v1/excel/download/{task_id}?format=excel",
        headers=headers
    )
    
    with open(output_path, "wb") as f:
        f.write(response.content)

# 主流程
if __name__ == "__main__":
    # 步骤1: 获取令牌
    token = get_access_token()
    print(f"✅ 获取令牌成功")
    
    # 步骤2: 上传文件
    upload_result = upload_excel(token, "workorder.xlsx")
    task_id = upload_result["task_id"]
    print(f"✅ 上传成功，任务ID: {task_id}")
    
    # 步骤3: 等待完成
    completion_data = wait_for_completion(token, task_id)
    print(f"✅ 检测完成")
    
    # 步骤4: 获取结果
    result = get_result(token, task_id)
    print(f"✅ 获取结果成功，共 {result['rows_total']} 条记录")
    
    # 步骤5: 下载文件
    download_result(token, task_id, "result.xlsx")
    print(f"✅ 下载结果文件成功")
```

---

## ⚠️ 错误码说明

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| missing_file | 400 | 请求中没有文件 |
| empty_filename | 400 | 文件名为空 |
| invalid_file_type | 400 | 文件类型不支持 |
| invalid_batch_size | 400 | 批量处理大小超出范围 |
| empty_file | 400 | Excel文件为空 |
| invalid_format | 400 | Excel格式不正确 |
| parse_failed | 400 | 解析Excel失败 |
| database_error | 500 | 数据入库失败 |
| queue_failed | 500 | 任务加入队列失败 |
| upload_failed | 500 | 文件上传失败 |
| task_not_found | 404 | 任务不存在 |
| result_not_found | 404 | 结果文件不存在 |
| query_failed | 500 | 查询失败 |
| invalid_token | 401 | 令牌无效 |
| token_expired | 401 | 令牌已过期 |
| missing_token | 401 | 缺少令牌 |

---

## 📊 Excel文件格式要求

### 必需字段

Excel文件必须包含以下字段（83字段标准格式）：

1. **核心字段**（必填）:
   - 工单单号
   - 工单性质（AI检测后填充）
   - 判定依据（AI检测后填充）

2. **基础信息**:
   - 保内保外
   - 批次入库日期
   - 安装日期
   - 购机日期
   - 产品名称
   - 开发主体

3. **故障信息**:
   - 故障部位名称
   - 故障组
   - 故障类别
   - 服务项目或故障现象

4. **维修信息**:
   - 维修方式
   - 旧件名称
   - 新件名称

5. **详细描述**:
   - 来电内容
   - 现场诊断故障现象
   - 处理方案简述或备注

---

## 🔒 权限范围 (Scopes)

| Scope | 说明 |
|-------|------|
| excel:upload | 上传Excel文件权限 |
| excel:query | 查询检测结果权限 |

---

## 💡 最佳实践

### 1. 令牌管理
```python
class TokenManager:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = None
        self.expires_at = 0
    
    def get_token(self):
        # 检查令牌是否过期
        if time.time() >= self.expires_at:
            # 重新获取令牌
            self.refresh_token()
        return self.token
    
    def refresh_token(self):
        # 获取新令牌
        response = get_access_token(self.client_id, self.client_secret)
        self.token = response["access_token"]
        self.expires_at = time.time() + response["expires_in"] - 60  # 提前60秒刷新
```

### 2. 错误重试
```python
def upload_with_retry(file_path, max_retries=3):
    for i in range(max_retries):
        try:
            return upload_excel(get_token(), file_path)
        except Exception as e:
            if i == max_retries - 1:
                raise
            time.sleep(2 ** i)  # 指数退避
```

### 3. 批量处理
- 小文件(<50行): batch_size=50
- 中等文件(50-200行): batch_size=100
- 大文件(>200行): batch_size=200

---

## 🆚 与Drawing模块的对比

| 特性 | Drawing API | Excel API |
|------|-------------|-----------|
| 认证方式 | OAuth 2.0 | OAuth 2.0 |
| 文件类型 | PDF | Excel (.xlsx, .xls) |
| 上传接口 | /api/v1/drawing/upload | /api/v1/excel/upload |
| 状态查询 | /api/v1/drawing/status/{id} | /api/v1/excel/status/{id} |
| 结果获取 | /api/v1/drawing/result/{id} | /api/v1/excel/result/{id} |
| 队列机制 | ✅ | ✅ |
| 批量处理 | ❌ | ✅ (支持batch_size参数) |
| 返回格式 | 结论+详细报告 | 19字段数据 |

---

## 📞 技术支持

如有问题，请联系技术支持团队。
