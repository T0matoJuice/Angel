# 工程制图检测模块 OAuth 2.0 API 功能使用指南

## 📖 简介

本系统已成功为工程制图检测模块添加了OAuth 2.0 API接口功能，允许外部系统通过编程方式调用检测服务。

**核心特性**:
- ✅ 基于OAuth 2.0标准的安全认证
- ✅ RESTful API设计
- ✅ JWT访问令牌
- ✅ 频率限制保护
- ✅ 完整的API调用审计
- ✅ 不影响现有Web界面功能

---

## 🚀 快速开始

### 第一步：获取客户端凭证

联系系统管理员，使用客户端管理工具创建OAuth客户端：

```bash
cd LLM_Detection_System
python manage_oauth_clients.py
```

选择 "1. 创建新客户端"，按提示输入信息后，会获得：
- **Client ID**: 客户端标识符（如：`client_abc123`）
- **Client Secret**: 客户端密钥（如：`secret_xyz789`）

⚠️ **重要**: Client Secret仅显示一次，请立即保存！

---

### 第二步：获取访问令牌

使用客户端凭证获取访问令牌：

**Python示例**:
```python
import requests

# 配置
BASE_URL = "http://localhost:5000"
CLIENT_ID = "your_client_id"
CLIENT_SECRET = "your_client_secret"

# 获取Token
token_url = f"{BASE_URL}/api/oauth/token"
token_data = {
    "grant_type": "client_credentials",
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "scope": "drawing:upload,drawing:inspect,drawing:query"
}

response = requests.post(token_url, data=token_data)
result = response.json()

access_token = result["access_token"]
print(f"访问令牌: {access_token}")
print(f"有效期: {result['expires_in']}秒")
```

**curl示例**:
```bash
curl -X POST http://localhost:5000/api/oauth/token \
  -d "grant_type=client_credentials" \
  -d "client_id=your_client_id" \
  -d "client_secret=your_client_secret" \
  -d "scope=drawing:upload,drawing:inspect,drawing:query"
```

**响应示例**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "scopes": ["drawing:upload", "drawing:inspect", "drawing:query"]
}
```

---

### 第三步：调用API接口

使用获取的访问令牌调用API：

#### 1. 上传工程图纸

```python
# 上传文件
upload_url = f"{BASE_URL}/api/v1/drawing/upload"
headers = {"Authorization": f"Bearer {access_token}"}
files = {"file": open("drawing.pdf", "rb")}
data = {
    "checker_name": "张三",
    "version": "V1.0"
}

response = requests.post(upload_url, headers=headers, files=files, data=data)
result = response.json()

filename = result["filename"]
print(f"文件上传成功: {filename}")
```

#### 2. 执行检测

```python
# 执行检测
inspect_url = f"{BASE_URL}/api/v1/drawing/inspect"
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}
data = {"filename": filename}

response = requests.post(inspect_url, headers=headers, json=data)
result = response.json()

print(f"检测ID: {result['inspection_id']}")
print(f"检测结论: {result['conclusion']}")
print(f"详细报告: {result['detailed_report']}")
```

#### 3. 查询检测结果

```python
# 查询结果
inspection_id = result["inspection_id"]
result_url = f"{BASE_URL}/api/v1/drawing/result/{inspection_id}"
headers = {"Authorization": f"Bearer {access_token}"}

response = requests.get(result_url, headers=headers)
result = response.json()

print(f"文件名: {result['filename']}")
print(f"结论: {result['conclusion']}")
```

#### 4. 查询历史记录

```python
# 查询历史
history_url = f"{BASE_URL}/api/v1/drawing/history"
headers = {"Authorization": f"Bearer {access_token}"}
params = {"page": 1, "per_page": 10}

response = requests.get(history_url, headers=headers, params=params)
result = response.json()

print(f"总记录数: {result['total']}")
for record in result['records']:
    print(f"- {record['filename']}: {record['conclusion']}")
```

---

## 📡 可用的API接口

| 接口 | 方法 | 权限 | 说明 |
|------|------|------|------|
| `/api/oauth/token` | POST | 无 | 获取访问令牌 |
| `/api/oauth/revoke` | POST | 无 | 撤销访问令牌 |
| `/api/v1/drawing/health` | GET | 无 | 健康检查 |
| `/api/v1/drawing/upload` | POST | drawing:upload | 上传图纸 |
| `/api/v1/drawing/inspect` | POST | drawing:inspect | 执行检测 |
| `/api/v1/drawing/result/<id>` | GET | drawing:query | 查询结果 |
| `/api/v1/drawing/history` | GET | drawing:query | 查询历史 |

---

## 🔐 权限范围说明

- **drawing:upload**: 允许上传工程图纸文件
- **drawing:inspect**: 允许执行检测
- **drawing:query**: 允许查询检测结果和历史记录

---

## ⚠️ 常见错误处理

### 1. Token过期 (401)
```json
{
  "error": "invalid_token",
  "error_description": "Token无效或已过期"
}
```
**解决方法**: 重新获取访问令牌

### 2. 权限不足 (403)
```json
{
  "error": "insufficient_scope",
  "error_description": "缺少必要的权限: drawing:upload"
}
```
**解决方法**: 联系管理员调整客户端权限

### 3. 超过频率限制 (429)
```json
{
  "error": "rate_limit_exceeded",
  "error_description": "超过频率限制，请在 2025-11-19 12:00:00 后重试"
}
```
**解决方法**: 等待限制重置或联系管理员提高限额

### 4. 文件类型错误 (400)
```json
{
  "error": "invalid_file_type",
  "error_description": "只支持PDF格式文件"
}
```
**解决方法**: 确保上传的是PDF格式文件

---

## 📊 频率限制

- **默认限制**: 100次/小时
- **计算方式**: 滑动窗口
- **重置时间**: 每小时整点

如需提高限额，请联系系统管理员。

---

## 🔒 安全建议

1. **保护密钥**
   - 不要在代码中硬编码client_secret
   - 使用环境变量或配置文件
   - 定期轮换密钥

2. **Token管理**
   - Token有效期为1小时
   - 过期后需重新获取
   - 不要共享Token给其他系统

3. **HTTPS传输**
   - 生产环境必须使用HTTPS
   - 防止Token被窃取

4. **错误处理**
   - 实现重试机制
   - 记录错误日志
   - 监控API调用状态

---

## 📞 技术支持

### 管理员工具

**客户端管理**:
```bash
python manage_oauth_clients.py
```

功能：
- 创建新客户端
- 查看所有客户端
- 查看客户端详情（包含API调用统计）
- 启用/禁用客户端

### 测试工具

**基础功能测试**:
```bash
python simple_api_test.py
```

**完整流程测试**:
```bash
python test_api.py
```

### 文档

- **API详细文档**: `工程制图检测API文档.md`
- **实现总结**: `OAuth2.0_API实现总结.md`
- **本使用指南**: `OAuth2.0_API功能使用指南.md`

---

## 💡 最佳实践

### 1. Token缓存

```python
class DrawingAPIClient:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.token_expires_at = None
    
    def get_token(self):
        # 检查Token是否过期
        if self.access_token and self.token_expires_at > time.time():
            return self.access_token
        
        # 获取新Token
        response = requests.post(
            "http://localhost:5000/api/oauth/token",
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret
            }
        )
        result = response.json()
        
        self.access_token = result["access_token"]
        self.token_expires_at = time.time() + result["expires_in"] - 60  # 提前1分钟刷新
        
        return self.access_token
```

### 2. 错误重试

```python
import time
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# 配置重试策略
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504]
)

adapter = HTTPAdapter(max_retries=retry_strategy)
session = requests.Session()
session.mount("http://", adapter)
session.mount("https://", adapter)

# 使用session发送请求
response = session.post(url, headers=headers, json=data)
```

---

## 🎯 完整示例代码

完整的Python客户端示例请参考 `test_api.py` 文件。

---

**文档版本**: 1.0.0  
**最后更新**: 2025-11-19
