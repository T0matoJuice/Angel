# 🔗 MySQL 数据库集成说明

## ✅ 已完成的修改

### 1. 数据库配置修改

**文件**: `LLM_Detection_System/modules/common/config.py`

- ✅ 将 SQLite 数据库改为 MySQL 数据库
- ✅ 连接信息：
  - 主机：localhost
  - 端口：3306
  - 用户名：root
  - 密码：123456
  - 数据库名：angel
  - 字符集：utf8mb4

```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:123456@localhost:3306/angel?charset=utf8mb4'
```

---

### 2. User 模型修改

**文件**: `LLM_Detection_System/modules/auth/models.py`

✅ 已将 User 模型映射到 MySQL 的 `angel.user` 表，字段完全匹配：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | int | 主键，自增 |
| username | varchar(255) | 用户名 |
| password | varchar(255) | 密码（存储哈希值） |
| email | varchar(255) | 邮箱 |
| role | varchar(255) | 角色（默认值：'user'） |
| creat_time | varchar(255) | 创建时间 |
| is_active | varchar(255) | 是否启用（'1'=启用，'0'=禁用） |

**重要说明**：
- `password` 字段存储的是 **werkzeug 加密后的哈希值**，不是明文密码
- `is_active` 字段是 varchar 类型，'1' 表示启用，'0' 表示禁用
- `role` 字段默认值为 'user'（普通用户）
- `creat_time` 字段在注册时自动设置为当前时间（格式：YYYY-MM-DD HH:MM:SS）

---

### 3. 认证路由修改

**文件**: `LLM_Detection_System/modules/auth/routes.py`

✅ 已修改登录和注册逻辑：

#### 登录功能
- ✅ 验证 CAPTCHA（验证码）
- ✅ 从 MySQL user 表查询用户
- ✅ 验证密码哈希值
- ✅ 检查账户是否启用（is_active == '1'）
- ✅ 登录成功后跳转到首页

#### 注册功能
- ✅ 验证 CAPTCHA（验证码）
- ✅ 验证用户名、密码、邮箱
- ✅ 自动设置字段：
  - `role`: 'user'
  - `creat_time`: 当前时间
  - `is_active`: '1'（启用）
  - `password`: 加密后的哈希值
- ✅ 插入新用户到 MySQL user 表

---

### 4. 依赖包安装

**文件**: `LLM_Detection_System/requirements.txt`

✅ 已添加 MySQL 驱动：
```
pymysql>=1.0.0
```

✅ 已安装的依赖：
- pymysql==1.1.2
- sqlalchemy==2.0.44
- flask-sqlalchemy>=3.0.0

---

## 🧪 测试结果

### 数据库连接测试

运行测试脚本：
```bash
python LLM_Detection_System/test_mysql_connection.py
```

✅ **测试结果**：
- PyMySQL 连接：✅ 成功
- SQLAlchemy 连接：✅ 成功
- MySQL 版本：8.0.41
- user 表结构：✅ 正确识别所有字段

---

## 🚀 使用指南

### 1. 启动 Flask 应用

```bash
cd C:/Users/root/Desktop/LLM_Detect_master
python LLM_Detection_System/app.py
```

### 2. 访问页面

- **首页**: http://localhost:5000
- **登录页面**: http://localhost:5000/auth/login
- **注册页面**: http://localhost:5000/auth/register

### 3. 注册新用户

1. 访问注册页面
2. 填写表单：
   - 用户名（至少3个字符）
   - 密码（至少6个字符）
   - 确认密码
   - 邮箱（可选）
   - **验证码**（必填，点击图片可刷新）
3. 点击"注册"按钮
4. 注册成功后会自动跳转到登录页面

**注册后的数据库记录**：
```sql
INSERT INTO user (username, password, email, role, creat_time, is_active)
VALUES ('testuser', 'scrypt:32768:8:1$...', 'test@example.com', 'user', '2025-11-12 10:30:00', '1');
```

### 4. 登录系统

1. 访问登录页面
2. 填写表单：
   - 用户名
   - 密码
   - **验证码**（必填，点击图片可刷新）
   - 记住我（可选）
3. 点击"登录"按钮
4. 登录成功后跳转到首页

---

## 🔒 安全特性

### 1. 密码加密
- ✅ 使用 `werkzeug.security.generate_password_hash()` 加密密码
- ✅ 密码不以明文存储在数据库中
- ✅ 使用 `check_password_hash()` 验证密码

### 2. CAPTCHA 验证
- ✅ 登录和注册都需要验证码
- ✅ 验证码存储在 session 中
- ✅ 验证后自动清除，防止重复使用
- ✅ 点击图片可刷新验证码

### 3. 输入验证
- ✅ 用户名长度验证（至少3个字符）
- ✅ 密码长度验证（至少6个字符）
- ✅ 密码确认验证
- ✅ 用户名唯一性验证
- ✅ 邮箱唯一性验证

### 4. 账户状态控制
- ✅ is_active 字段控制账户启用/禁用
- ✅ 禁用账户无法登录

---

## 📊 数据库操作示例

### 查询所有用户

```sql
SELECT id, username, email, role, creat_time, is_active 
FROM user;
```

### 禁用用户

```sql
UPDATE user 
SET is_active = '0' 
WHERE username = 'testuser';
```

### 启用用户

```sql
UPDATE user 
SET is_active = '1' 
WHERE username = 'testuser';
```

### 修改用户角色

```sql
UPDATE user 
SET role = 'admin' 
WHERE username = 'testuser';
```

### 删除用户

```sql
DELETE FROM user 
WHERE username = 'testuser';
```

---

## ⚠️ 注意事项

### 1. 密码字段
- ❗ **重要**：`password` 字段存储的是加密后的哈希值，不是明文密码
- ❗ 不要直接在数据库中修改 password 字段
- ❗ 如需重置密码，请使用 Python 代码生成哈希值

### 2. is_active 字段
- ❗ 类型是 varchar，不是 boolean
- ❗ '1' 表示启用，'0' 表示禁用
- ❗ 不要使用 true/false 或 1/0（数字）

### 3. creat_time 字段
- ❗ 类型是 varchar，不是 datetime
- ❗ 格式：'YYYY-MM-DD HH:MM:SS'
- ❗ 注册时自动设置，不需要手动填写

### 4. role 字段
- ✅ 默认值为 'user'
- ✅ 可以设置为其他值（如 'admin'）
- ✅ 目前系统暂未使用此字段进行权限控制

---

## 🛠️ 故障排查

### 问题1：无法连接到 MySQL 数据库

**检查项**：
1. MySQL 服务是否启动
2. 数据库名称是否为 'angel'
3. 用户名和密码是否正确（root/123456）
4. user 表是否存在

**解决方法**：
```bash
# 运行测试脚本
python LLM_Detection_System/test_mysql_connection.py
```

### 问题2：登录失败

**可能原因**：
1. 用户名不存在
2. 密码错误
3. 账户被禁用（is_active != '1'）
4. 验证码错误

**检查方法**：
```sql
-- 查询用户信息
SELECT * FROM user WHERE username = 'your_username';
```

### 问题3：注册失败

**可能原因**：
1. 用户名已存在
2. 邮箱已被注册
3. 密码长度不足（<6个字符）
4. 用户名长度不足（<3个字符）
5. 验证码错误

---

## 📝 修改文件清单

### 已修改的文件（4个）

1. ✅ `LLM_Detection_System/modules/common/config.py`
   - 修改数据库连接配置

2. ✅ `LLM_Detection_System/modules/auth/models.py`
   - 更新 User 模型字段映射

3. ✅ `LLM_Detection_System/modules/auth/routes.py`
   - 更新登录和注册逻辑

4. ✅ `LLM_Detection_System/modules/auth/__init__.py`
   - 注释掉自动创建表的代码

5. ✅ `LLM_Detection_System/requirements.txt`
   - 添加 pymysql 依赖

### 新增的文件（2个）

1. ✅ `LLM_Detection_System/test_mysql_connection.py`
   - MySQL 连接测试脚本

2. ✅ `MySQL数据库集成说明.md`
   - 本说明文档

---

## ✨ 功能保持不变

以下功能完全保持不变：

- ✅ CAPTCHA 验证码功能
- ✅ 用户登录功能
- ✅ 用户注册功能
- ✅ 用户登出功能
- ✅ 会话管理（Flask-Login）
- ✅ 密码加密存储
- ✅ 页面样式和布局
- ✅ 表单验证逻辑

---

## 🎉 总结

✅ **已成功将 LLM Detection System 连接到本地 MySQL 数据库**

- 数据库：angel
- 表名：user
- 连接方式：pymysql + SQLAlchemy
- 密码加密：werkzeug.security
- 验证码：captcha 库

所有功能已测试通过，可以正常使用！

