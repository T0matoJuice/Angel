import requests

# 目标地址
url = "http://qmstest.angelgroup.com.cn:8080/ssoServer/oauth/login"

# 请求头
headers = {
    "Authorization": "Basic cXVhbGl0eURhdGE6JDJhJDEwJGZDOU40WUxOWUlCLzgyM3ZQcjd2b2U3dWtndUtHSkRNYzdya210UmkxeHVCQ0lZZUcwMkJX",
    "Content-Type": "application/json"
}

# 请求体
payload = {
    "username": "ai",
    "password": "Ai@2025."
}

# 发送POST请求
response = requests.post(url, json=payload, headers=headers)

# 解析响应
if response.status_code == 200:
    data = response.json()
    print("access_token:", data.get("access_token"))
    print("token_type:", data.get("token_type"))
else:
    print("请求失败，状态码：", response.status_code)
    print(response.text)
