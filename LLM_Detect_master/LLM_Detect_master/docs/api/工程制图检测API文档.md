# 工程制图检测 API 文档

## 📋 概述

本文档描述了工程制图检测模块的RESTful API接口，允许外部系统通过OAuth 2.0认证调用检测服务。

**API版本**: v1.0.0  
**基础URL**: `http://localhost:5000/api/v1/drawing`  
**认证方式**: OAuth 2.0 (Client Credentials Grant)

---

## 🔐 认证流程

### 1. 获取客户端凭证

联系系统管理员获取：
- `client_id`: 客户端标识符
- `client_secret`: 客户端密钥（请妥善保管）

### 2. 获取访问令牌

**端点**: `POST /api/oauth/token`

**请求头**:
```
Content-Type: application/x-www-form-urlencoded
```

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| grant_type | string | 是 | 固定值: `client_credentials` |
| client_id | string | 是 | 客户端ID |
| client_secret | string | 是 | 客户端密钥 |
| scope | string | 否 | 权限范围，多个用逗号分隔 |

**请求示例**:
```bash
curl -X POST http://localhost:5000/api/oauth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials" \
  -d "client_id=client_abc123" \
  -d "client_secret=secret_xyz789" \
  -d "scope=drawing:upload,drawing:inspect,drawing:query"
```

**成功响应** (200 OK):
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "scopes": [
    "drawing:upload",
    "drawing:inspect",
    "drawing:query"
  ]
}
```

**错误响应**:
```json
{
  "error": "invalid_client",
  "error_description": "客户端密钥错误"
}
```

### 3. 使用访问令牌

在后续API请求中，将访问令牌添加到请求头：
```
Authorization: Bearer <access_token>
```

---

## 📡 API接口

### 1. 上传工程图纸

**端点**: `POST /api/v1/drawing/upload`

**权限**: `drawing:upload`

**请求头**:
```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | file | 是 | PDF格式的工程图纸文件 |
| checker_name | string | 是 | 检入者姓名 |
| version | string | 是 | 版本号（如：V1.0） |

**请求示例** (Python):
```python
import requests

url = "http://localhost:5000/api/v1/drawing/upload"
headers = {
    "Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
}
files = {
    "file": open("drawing.pdf", "rb")
}
data = {
    "checker_name": "张三",
    "version": "V1.0"
}

response = requests.post(url, headers=headers, files=files, data=data)
print(response.json())
```

**请求示例** (curl):
```bash
curl -X POST http://localhost:5000/api/v1/drawing/upload \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..." \
  -F "file=@drawing.pdf" \
  -F "checker_name=张三" \
  -F "version=V1.0"
```

**成功响应** (200 OK):
```json
{
  "success": true,
  "filename": "1732012345_drawing.pdf",
  "file_id": "1732012345",
  "original_filename": "drawing.pdf",
  "checker_name": "张三",
  "version": "V1.0",
  "message": "文件上传成功"
}
```

**错误响应**:
```json
{
  "error": "invalid_file_type",
  "error_description": "只支持PDF格式文件"
}
```

---

### 2. 执行检测

**端点**: `POST /api/v1/drawing/inspect`

**权限**: `drawing:inspect`

**请求头**:
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| filename | string | 是 | 上传接口返回的filename |

**请求示例** (Python):
```python
import requests

url = "http://localhost:5000/api/v1/drawing/inspect"
headers = {
    "Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGc...",
    "Content-Type": "application/json"
}
data = {
    "filename": "1732012345_drawing.pdf"
}

response = requests.post(url, headers=headers, json=data)
print(response.json())
```

**请求示例** (curl):
```bash
curl -X POST http://localhost:5000/api/v1/drawing/inspect \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{"filename": "1732012345_drawing.pdf"}'
```

**成功响应** (200 OK):
```json
{
  "success": true,
  "inspection_id": "1732012345678",
  "filename": "drawing.pdf",
  "conclusion": "合格",
  "detailed_report": "检测详细报告内容...",
  "checker_name": "张三",
  "version": "V1.0",
  "timestamp": "2025-11-19 10:30:00"
}
```

**错误响应**:
```json
{
  "error": "file_not_found",
  "error_description": "文件不存在，请先上传文件"
}
```

---

### 3. 查询检测结果

**端点**: `GET /api/v1/drawing/result/<inspection_id>`

**权限**: `drawing:query`

**请求头**:
```
Authorization: Bearer <access_token>
```

**路径参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| inspection_id | string | 是 | 检测记录ID |

**请求示例** (Python):
```python
import requests

inspection_id = "1732012345678"
url = f"http://localhost:5000/api/v1/drawing/result/{inspection_id}"
headers = {
    "Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
}

response = requests.get(url, headers=headers)
print(response.json())
```

**请求示例** (curl):
```bash
curl -X GET http://localhost:5000/api/v1/drawing/result/1732012345678 \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

**成功响应** (200 OK):
```json
{
  "success": true,
  "inspection_id": "1732012345678",
  "filename": "drawing.pdf",
  "conclusion": "合格",
  "detailed_report": "检测详细报告内容...",
  "checker_name": "张三",
  "version": "V1.0",
  "created_at": "2025-11-19 10:30:00"
}
```

**错误响应**:
```json
{
  "error": "not_found",
  "error_description": "检测记录不存在"
}
```

---

### 4. 查询历史记录

**端点**: `GET /api/v1/drawing/history`

**权限**: `drawing:query`

**请求头**:
```
Authorization: Bearer <access_token>
```

**查询参数**:
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| page | integer | 否 | 1 | 页码 |
| per_page | integer | 否 | 10 | 每页记录数（最大100） |

**请求示例** (Python):
```python
import requests

url = "http://localhost:5000/api/v1/drawing/history"
headers = {
    "Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
}
params = {
    "page": 1,
    "per_page": 10
}

response = requests.get(url, headers=headers, params=params)
print(response.json())
```

**请求示例** (curl):
```bash
curl -X GET "http://localhost:5000/api/v1/drawing/history?page=1&per_page=10" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

**成功响应** (200 OK):
```json
{
  "success": true,
  "total": 100,
  "page": 1,
  "per_page": 10,
  "total_pages": 10,
  "records": [
    {
      "inspection_id": "1732012345678",
      "filename": "drawing1.pdf",
      "conclusion": "合格",
      "checker_name": "张三",
      "version": "V1.0",
      "created_at": "2025-11-19 10:30:00"
    },
    {
      "inspection_id": "1732012345679",
      "filename": "drawing2.pdf",
      "conclusion": "不合格",
      "checker_name": "李四",
      "version": "V2.0",
      "created_at": "2025-11-19 11:00:00"
    }
  ]
}
```

---

### 5. 健康检查

**端点**: `GET /api/v1/drawing/health`

**权限**: 无需认证

**请求示例**:
```bash
curl -X GET http://localhost:5000/api/v1/drawing/health
```

**成功响应** (200 OK):
```json
{
  "status": "ok",
  "service": "Drawing Inspection API",
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
CLIENT_ID = "client_abc123"
CLIENT_SECRET = "secret_xyz789"

# 1. 获取访问令牌
def get_access_token():
    url = f"{BASE_URL}/api/oauth/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": "drawing:upload,drawing:inspect,drawing:query"
    }
    response = requests.post(url, data=data)
    response.raise_for_status()
    return response.json()["access_token"]

# 2. 上传文件
def upload_file(access_token, file_path, checker_name, version):
    url = f"{BASE_URL}/api/v1/drawing/upload"
    headers = {"Authorization": f"Bearer {access_token}"}
    files = {"file": open(file_path, "rb")}
    data = {
        "checker_name": checker_name,
        "version": version
    }
    response = requests.post(url, headers=headers, files=files, data=data)
    response.raise_for_status()
    return response.json()

# 3. 执行检测
def inspect_drawing(access_token, filename):
    url = f"{BASE_URL}/api/v1/drawing/inspect"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    data = {"filename": filename}
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()

# 4. 查询结果
def get_result(access_token, inspection_id):
    url = f"{BASE_URL}/api/v1/drawing/result/{inspection_id}"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

# 主流程
if __name__ == "__main__":
    try:
        # 获取Token
        print("1. 获取访问令牌...")
        token = get_access_token()
        print(f"✅ Token: {token[:20]}...")

        # 上传文件
        print("\n2. 上传工程图纸...")
        upload_result = upload_file(
            token,
            "drawing.pdf",
            "张三",
            "V1.0"
        )
        print(f"✅ 文件ID: {upload_result['file_id']}")
        filename = upload_result['filename']

        # 执行检测
        print("\n3. 执行检测...")
        inspect_result = inspect_drawing(token, filename)
        print(f"✅ 检测ID: {inspect_result['inspection_id']}")
        print(f"   结论: {inspect_result['conclusion']}")

        # 查询结果
        print("\n4. 查询检测结果...")
        result = get_result(token, inspect_result['inspection_id'])
        print(f"✅ 文件名: {result['filename']}")
        print(f"   结论: {result['conclusion']}")
        print(f"   检入者: {result['checker_name']}")
        print(f"   版本: {result['version']}")

    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP错误: {e}")
        print(f"   响应: {e.response.text}")
    except Exception as e:
        print(f"❌ 错误: {e}")
```

---

## ⚠️ 错误码说明

### OAuth认证错误

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| unsupported_grant_type | 400 | 不支持的授权类型 |
| invalid_request | 400 | 请求参数错误 |
| invalid_client | 401 | 客户端认证失败 |
| client_disabled | 403 | 客户端已被禁用 |
| invalid_scope | 400 | 权限范围无效 |
| server_error | 500 | 服务器内部错误 |

### API调用错误

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| missing_authorization | 401 | 缺少Authorization头 |
| invalid_authorization | 401 | Authorization头格式错误 |
| invalid_token | 401 | Token无效或已过期 |
| token_revoked | 401 | Token已被撤销 |
| insufficient_scope | 403 | 权限不足 |
| rate_limit_exceeded | 429 | 超过频率限制 |
| missing_file | 400 | 缺少文件 |
| invalid_file_type | 400 | 文件类型不支持 |
| file_not_found | 404 | 文件不存在 |
| not_found | 404 | 资源不存在 |
| inspection_failed | 500 | 检测失败 |

---

## 📊 频率限制

- **默认限制**: 100次/小时
- **限制方式**: 滑动窗口
- **超限响应**: HTTP 429 Too Many Requests
- **重置时间**: 每小时整点重置

**响应头**:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 2025-11-19T11:00:00Z
```

---

## 🔒 安全建议

1. **保护密钥**:
   - 不要在代码中硬编码client_secret
   - 使用环境变量或配置文件存储
   - 定期轮换密钥

2. **HTTPS传输**:
   - 生产环境必须使用HTTPS
   - 防止Token被窃取

3. **Token管理**:
   - Token有效期为1小时
   - 过期后需重新获取
   - 不要共享Token

4. **错误处理**:
   - 实现重试机制
   - 记录错误日志
   - 监控API调用状态

---

## 📞 技术支持

如有问题，请联系系统管理员。

**文档版本**: 1.0.0
**最后更新**: 2025-11-19

