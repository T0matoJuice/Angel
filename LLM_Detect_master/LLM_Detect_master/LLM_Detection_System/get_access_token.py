#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取 OAuth 2.0 访问令牌 (Access Token)
使用 Client ID 和 Client Secret 获取 Access Token
"""

import requests
import json
from datetime import datetime, timedelta
from modules.auth.oauth_models import OAuthClient
from app import app


def get_access_token(client_id, client_secret, base_url="https://1qs168qy34541.vicp.fun/"):
    """
    获取 OAuth 2.0 访问令牌
    
    Args:
        client_id: 客户端ID
        client_secret: 客户端密钥
        base_url: API基础URL
    
    Returns:
        dict: Token信息，包含access_token等字段
    """
    print("\n" + "=" * 70)
    print("OAuth 2.0 访问令牌获取工具")
    print("=" * 70)
    
    # Token端点URL
    token_url = f"{base_url}/api/oauth/token"
    
    # 请求参数
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "drawing:upload,drawing:inspect,drawing:query"
    }
    
    print(f"\n正在请求Token...")
    print(f"Token端点: {token_url}")
    print(f"Client ID: {client_id}")
    print(f"权限范围: drawing:upload,drawing:inspect,drawing:query")
    
    try:
        # 发送POST请求
        response = requests.post(token_url, data=data)
        
        print(f"\n响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print("\n" + "=" * 70)
            print("✅ Token获取成功！")
            print("=" * 70)
            
            print(f"\n【访问令牌 (Access Token)】")
            print(result['access_token'])
            
            print(f"\n【Token详细信息】")
            print(f"Token类型: {result['token_type']}")

            # 动态显示有效期
            expires_in_seconds = result['expires_in']
            expires_in_days = expires_in_seconds // 86400
            expires_in_hours = (expires_in_seconds % 86400) // 3600

            if expires_in_days > 0:
                print(f"有效期: {result['expires_in']}秒 ({expires_in_days}天)")
            elif expires_in_hours > 0:
                print(f"有效期: {result['expires_in']}秒 ({expires_in_hours}小时)")
            else:
                print(f"有效期: {result['expires_in']}秒")

            print(f"权限范围: {', '.join(result['scopes'])}")

            # 计算过期时间
            expires_at = datetime.now() + timedelta(seconds=expires_in_seconds)
            print(f"过期时间: 约 {expires_at.strftime('%Y-%m-%d %H:%M:%S')}")
            
            print(f"\n【使用方法】")
            print(f"在API请求的Header中添加:")
            print(f"Authorization: Bearer {result['access_token'][:50]}...")
            
            print(f"\n【Python代码示例】")
            print(f"```python")
            print(f"import requests")
            print(f"")
            print(f"access_token = '{result['access_token']}'")
            print(f"headers = {{'Authorization': f'Bearer {{access_token}}'}}")
            print(f"")
            print(f"# 调用API")
            print(f"response = requests.get(")
            print(f"    '{base_url}/api/v1/drawing/history',")
            print(f"    headers=headers")
            print(f")")
            print(f"```")
            
            print(f"\n【curl命令示例】")
            print(f"```bash")
            print(f"curl -X GET '{base_url}/api/v1/drawing/history' \\")
            print(f"  -H 'Authorization: Bearer {result['access_token'][:50]}...'")
            print(f"```")
            
            print("\n" + "=" * 70)
            
            # 保存到文件（可选）
            save = input("\n是否保存Token到文件? (y/n): ").strip().lower()
            if save == 'y':
                filename = f"access_token_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"Access Token 信息\n")
                    f.write(f"=" * 70 + "\n\n")
                    f.write(f"获取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Client ID: {client_id}\n")
                    f.write(f"有效期: {result['expires_in']}秒 (1小时)\n\n")
                    f.write(f"Access Token:\n")
                    f.write(result['access_token'] + "\n\n")
                    f.write(f"使用方法:\n")
                    f.write(f"Authorization: Bearer {result['access_token']}\n")
                
                print(f"✅ Token已保存到文件: {filename}")
            
            return result
            
        else:
            # 处理错误
            error = response.json()
            print("\n" + "=" * 70)
            print("❌ Token获取失败")
            print("=" * 70)
            print(f"\n错误类型: {error.get('error')}")
            print(f"错误描述: {error.get('error_description')}")
            
            # 常见错误提示
            if error.get('error') == 'invalid_client':
                print("\n💡 可能的原因:")
                print("  1. Client ID 或 Client Secret 输入错误")
                print("  2. 客户端不存在")
                print("  3. 客户端已被禁用")
                print("\n建议:")
                print("  - 检查 Client ID 和 Client Secret 是否正确")
                print("  - 联系管理员确认客户端状态")
            
            return None
            
    except requests.exceptions.ConnectionError:
        print("\n❌ 连接失败")
        print(f"无法连接到服务器: {base_url}")
        print("\n请检查:")
        print("  1. 服务器是否正在运行")
        print("  2. URL是否正确")
        print("  3. 网络连接是否正常")
        return None
        
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        return None


def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("OAuth 2.0 访问令牌获取工具")
    print("=" * 70)
    
    # 获取用户输入
    print("\n请输入您的OAuth客户端凭证:")
    print("(如果您还没有凭证，请联系管理员或运行 manage_oauth_clients.py 创建)")
    
    client_id = input("\nClient ID: ").strip()
    if not client_id:
        print("❌ Client ID 不能为空")
        return
    
    client_secret = input("Client Secret: ").strip()
    if not client_secret:
        print("❌ Client Secret 不能为空")
        return
    
    # 可选：自定义服务器URL
    use_custom_url = input("\n使用默认服务器 (https://1qs168qy34541.vicp.fun/)? (y/n): ").strip().lower()
    if use_custom_url == 'n':
        base_url = input("请输入服务器URL: ").strip()
    else:
        base_url = "https://1qs168qy34541.vicp.fun/"
    
    # 获取Token
    result = get_access_token(client_id, client_secret, base_url)
    
    if result:
        print("\n✅ 完成！您现在可以使用这个Token调用API了。")
        print("⚠️  注意: Token有效期为12小时，过期后需要重新获取。")
    else:
        print("\n❌ 获取Token失败，请检查错误信息并重试。")


if __name__ == '__main__':
    main()

