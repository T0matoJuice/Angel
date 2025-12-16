#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试质量工单数据上传接口 - /excel/quality-dataupload
"""

import requests
import json
import time

# ===== 配置 =====
BASE_URL = "http://198.18.0.1:5000"
UPLOAD_URL = f"{BASE_URL}/excel/quality-dataupload"

# OAuth 认证配置
CLIENT_ID = "api_test_client_tomato"  # 替换为实际的client_id
CLIENT_SECRET = "api_test_secret_123"  # 替换为实际的client_secret
TOKEN_URL = f"{BASE_URL}/api/oauth/token"

# 可选：如果已有访问令牌，直接填写在这里（留空则自动申请）
ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjbGllbnRfaWQiOiJhcGlfdGVzdF9jbGllbnRfdG9tYXRvIiwic2NvcGVzIjpbIioiXSwiZXhwIjoxNzY1MjYyODk4LCJpYXQiOjE3NjQ2NTgwOTgsInR5cGUiOiJhY2Nlc3NfdG9rZW4ifQ.415HRmtV66EFSchkJfJKkZuqXMopOjbSvF8q4MYP_j0"  # 例如: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# ===== 颜色输出 =====
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_success(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")

def print_error(msg):
    print(f"{Colors.RED}❌ {msg}{Colors.END}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.END}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.END}")


def get_access_token():
    """获取OAuth访问令牌"""
    print_info("正在获取访问令牌...")
    
    try:
        response = requests.post(
            TOKEN_URL,
            data={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "grant_type": "client_credentials"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"令牌获取成功，有效期: {data['expires_in']}秒")
            return data["access_token"]
        else:
            print_error(f"令牌获取失败: {response.json()}")
            return None
            
    except Exception as e:
        print_error(f"请求失败: {str(e)}")
        return None


def test_upload_data(access_token):
    """测试数据上传接口"""
    
    print("=" * 60)
    print("质量工单数据上传接口测试")
    print("=" * 60)
    print()
    
    # 准备测试数据（包含19个必填字段）
    data = {
  "account": "测试用户",
  "filename": "example_batch",
  "unique_filename": "example_batch",
  "workorders": [
    {
      "工单单号": "WO00101",
      "工单性质": "",
      "判定依据": "",
      "保内保外": "保外转保内",
      "批次入库日期": "2024-12-06 20:50:46",
      "安装日期": "2025-02-12",
      "购机日期": "2025-02-12",
      "产品名称": "净水设备 反渗透厨下式净水机,J3674-ROC150，446*146*388mm(安吉尔白+天空蓝)",
      "开发主体": "电商事业部",
      "故障部位名称": "复合滤芯成品-SP J3673-ROC120,Ф98*357.5mm,含活性炭滤芯,PP滤芯,滤桶,包装胶袋等,批件型号:LX-3622US-PPC180,箱式,售后专用(/)",
      "故障组": "净水机",
      "故障类别": "滤芯类",
      "服务项目或故障现象": "",
      "维修方式": "上门维修",
      "旧件名称": "复合滤芯成品-SP J3673-ROC120,Ф98*357.5mm,含活性炭滤芯,PP滤芯,滤桶,包装胶袋等,批件型号:LX-3622US-PPC180,箱式,售后专用(/)",
      "新件名称": "复合滤芯成品-SP J3673-ROC120,Ф98*357.5mm,含活性炭滤芯,PP滤芯,滤桶,包装胶袋等,批件型号:LX-3622US-PPC180,箱式,售后专用(/)",
      "来电内容": "来电号码:13696788198;故障信息:机器故障具体故障问题请师傅先联系确认",
      "现场诊断故障现象": "滤芯堵塞",
      "处理方案简述或备注": "更换滤芯机器恢复正常"
    },
    {
      "工单单号": "WO00102",
      "工单性质": "",
      "判定依据": "",
      "保内保外": "保外转保内",
      "批次入库日期": "2024-12-06 20:50:46",
      "安装日期": "2025-02-12",
      "购机日期": "2025-02-12",
      "产品名称": "净水设备 反渗透厨下式净水机,J3674-ROC150，446*146*388mm(安吉尔白+天空蓝)",
      "开发主体": "电商事业部",
      "故障部位名称": "复合滤芯成品-SP J3673-ROC120,Ф98*357.5mm,含活性炭滤芯,PP滤芯,滤桶,包装胶袋等,批件型号:LX-3622US-PPC180,箱式,售后专用(/)",
      "故障组": "净水机",
      "故障类别": "滤芯类",
      "服务项目或故障现象": "",
      "维修方式": "上门维修",
      "旧件名称": "复合滤芯成品-SP J3673-ROC120,Ф98*357.5mm,含活性炭滤芯,PP滤芯,滤桶,包装胶袋等,批件型号:LX-3622US-PPC180,箱式,售后专用(/)",
      "新件名称": "复合滤芯成品-SP J3673-ROC120,Ф98*357.5mm,含活性炭滤芯,PP滤芯,滤桶,包装胶袋等,批件型号:LX-3622US-PPC180,箱式,售后专用(/)",
      "来电内容": "来电号码:13696788198;故障信息:机器故障具体故障问题请师傅先联系确认",
      "现场诊断故障现象": "滤芯堵塞",
      "处理方案简述或备注": "更换滤芯机器恢复正常"
    },
    {
      "工单单号": "WO00103",
      "工单性质": "",
      "判定依据": "",
      "保内保外": "保外转保内",
      "批次入库日期": "2024-12-06 20:50:46",
      "安装日期": "2025-02-12",
      "购机日期": "2025-02-12",
      "产品名称": "净水设备 反渗透厨下式净水机,J3674-ROC150，446*146*388mm(安吉尔白+天空蓝)",
      "开发主体": "电商事业部",
      "故障部位名称": "复合滤芯成品-SP J3673-ROC120,Ф98*357.5mm,含活性炭滤芯,PP滤芯,滤桶,包装胶袋等,批件型号:LX-3622US-PPC180,箱式,售后专用(/)",
      "故障组": "净水机",
      "故障类别": "滤芯类",
      "服务项目或故障现象": "",
      "维修方式": "上门维修",
      "旧件名称": "复合滤芯成品-SP J3673-ROC120,Ф98*357.5mm,含活性炭滤芯,PP滤芯,滤桶,包装胶袋等,批件型号:LX-3622US-PPC180,箱式,售后专用(/)",
      "新件名称": "复合滤芯成品-SP J3673-ROC120,Ф98*357.5mm,含活性炭滤芯,PP滤芯,滤桶,包装胶袋等,批件型号:LX-3622US-PPC180,箱式,售后专用(/)",
      "来电内容": "来电号码:13696788198;故障信息:机器故障具体故障问题请师傅先联系确认",
      "现场诊断故障现象": "滤芯堵塞",
      "处理方案简述或备注": "更换滤芯机器恢复正常"
    },
    {
      "工单单号": "WO00104",
      "工单性质": "",
      "判定依据": "",
      "保内保外": "保外转保内",
      "批次入库日期": "2024-12-06 20:50:46",
      "安装日期": "2025-02-12",
      "购机日期": "2025-02-12",
      "产品名称": "净水设备 反渗透厨下式净水机,J3674-ROC150，446*146*388mm(安吉尔白+天空蓝)",
      "开发主体": "电商事业部",
      "故障部位名称": "复合滤芯成品-SP J3673-ROC120,Ф98*357.5mm,含活性炭滤芯,PP滤芯,滤桶,包装胶袋等,批件型号:LX-3622US-PPC180,箱式,售后专用(/)",
      "故障组": "净水机",
      "故障类别": "滤芯类",
      "服务项目或故障现象": "",
      "维修方式": "上门维修",
      "旧件名称": "复合滤芯成品-SP J3673-ROC120,Ф98*357.5mm,含活性炭滤芯,PP滤芯,滤桶,包装胶袋等,批件型号:LX-3622US-PPC180,箱式,售后专用(/)",
      "新件名称": "复合滤芯成品-SP J3673-ROC120,Ф98*357.5mm,含活性炭滤芯,PP滤芯,滤桶,包装胶袋等,批件型号:LX-3622US-PPC180,箱式,售后专用(/)",
      "来电内容": "来电号码:13696788198;故障信息:机器故障具体故障问题请师傅先联系确认",
      "现场诊断故障现象": "滤芯堵塞",
      "处理方案简述或备注": "更换滤芯机器恢复正常"
    },
    {
      "工单单号": "WO00105",
      "工单性质": "",
      "判定依据": "",
      "保内保外": "保外转保内",
      "批次入库日期": "2024-12-06 20:50:46",
      "安装日期": "2025-02-12",
      "购机日期": "2025-02-12",
      "产品名称": "净水设备 反渗透厨下式净水机,J3674-ROC150，446*146*388mm(安吉尔白+天空蓝)",
      "开发主体": "电商事业部",
      "故障部位名称": "复合滤芯成品-SP J3673-ROC120,Ф98*357.5mm,含活性炭滤芯,PP滤芯,滤桶,包装胶袋等,批件型号:LX-3622US-PPC180,箱式,售后专用(/)",
      "故障组": "净水机",
      "故障类别": "滤芯类",
      "服务项目或故障现象": "",
      "维修方式": "上门维修",
      "旧件名称": "复合滤芯成品-SP J3673-ROC120,Ф98*357.5mm,含活性炭滤芯,PP滤芯,滤桶,包装胶袋等,批件型号:LX-3622US-PPC180,箱式,售后专用(/)",
      "新件名称": "复合滤芯成品-SP J3673-ROC120,Ф98*357.5mm,含活性炭滤芯,PP滤芯,滤桶,包装胶袋等,批件型号:LX-3622US-PPC180,箱式,售后专用(/)",
      "来电内容": "来电号码:13696788198;故障信息:机器故障具体故障问题请师傅先联系确认",
      "现场诊断故障现象": "滤芯堵塞",
      "处理方案简述或备注": "更换滤芯机器恢复正常"
    },
    {
      "工单单号": "WO00106",
      "工单性质": "",
      "判定依据": "",
      "保内保外": "保外转保内",
      "批次入库日期": "2024-12-06 20:50:46",
      "安装日期": "2025-02-12",
      "购机日期": "2025-02-12",
      "产品名称": "净水设备 反渗透厨下式净水机,J3674-ROC150，446*146*388mm(安吉尔白+天空蓝)",
      "开发主体": "电商事业部",
      "故障部位名称": "复合滤芯成品-SP J3673-ROC120,Ф98*357.5mm,含活性炭滤芯,PP滤芯,滤桶,包装胶袋等,批件型号:LX-3622US-PPC180,箱式,售后专用(/)",
      "故障组": "净水机",
      "故障类别": "滤芯类",
      "服务项目或故障现象": "",
      "维修方式": "上门维修",
      "旧件名称": "复合滤芯成品-SP J3673-ROC120,Ф98*357.5mm,含活性炭滤芯,PP滤芯,滤桶,包装胶袋等,批件型号:LX-3622US-PPC180,箱式,售后专用(/)",
      "新件名称": "复合滤芯成品-SP J3673-ROC120,Ф98*357.5mm,含活性炭滤芯,PP滤芯,滤桶,包装胶袋等,批件型号:LX-3622US-PPC180,箱式,售后专用(/)",
      "来电内容": "来电号码:13696788198;故障信息:机器故障具体故障问题请师傅先联系确认",
      "现场诊断故障现象": "滤芯堵塞",
      "处理方案简述或备注": "更换滤芯机器恢复正常"
    },
    {
      "工单单号": "WO00107",
      "工单性质": "",
      "判定依据": "",
      "保内保外": "保外转保内",
      "批次入库日期": "2024-12-06 20:50:46",
      "安装日期": "2025-02-12",
      "购机日期": "2025-02-12",
      "产品名称": "净水设备 反渗透厨下式净水机,J3674-ROC150，446*146*388mm(安吉尔白+天空蓝)",
      "开发主体": "电商事业部",
      "故障部位名称": "复合滤芯成品-SP J3673-ROC120,Ф98*357.5mm,含活性炭滤芯,PP滤芯,滤桶,包装胶袋等,批件型号:LX-3622US-PPC180,箱式,售后专用(/)",
      "故障组": "净水机",
      "故障类别": "滤芯类",
      "服务项目或故障现象": "",
      "维修方式": "上门维修",
      "旧件名称": "复合滤芯成品-SP J3673-ROC120,Ф98*357.5mm,含活性炭滤芯,PP滤芯,滤桶,包装胶袋等,批件型号:LX-3622US-PPC180,箱式,售后专用(/)",
      "新件名称": "复合滤芯成品-SP J3673-ROC120,Ф98*357.5mm,含活性炭滤芯,PP滤芯,滤桶,包装胶袋等,批件型号:LX-3622US-PPC180,箱式,售后专用(/)",
      "来电内容": "来电号码:13696788198;故障信息:机器故障具体故障问题请师傅先联系确认",
      "现场诊断故障现象": "滤芯堵塞",
      "处理方案简述或备注": "更换滤芯机器恢复正常"
    }
  ]
}

    
    print_info(f"准备上传 {len(data['workorders'])} 条测试数据...")
    print()
    
    try:
        # 发送POST请求（添加OAuth认证）
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
        response = requests.post(UPLOAD_URL, json=data, headers=headers)
        
        # 打印响应状态
        print(f"响应状态码: {response.status_code}")
        print()
        
        # 解析响应
        result = response.json()
        
        if response.status_code == 200 and result.get('success'):
            print_success("数据上传成功！")
            print()
            print_info("响应详情:")
            print(f"  批次ID: {result.get('batch_id')}")
            print(f"  接收总数: {result.get('total_received')}")
            print(f"  成功入库: {result.get('success_count')}")
            print(f"  失败数量: {result.get('failed_count')}")
            print(f"  队列状态: {result.get('queue_status')}")
            print(f"  消息: {result.get('message')}")
            print()
            
            if result.get('errors'):
                print_warning("部分数据入库失败:")
                for error in result['errors']:
                    print(f"  - 第{error['index']}条: {error['error']}")
                print()
            
            # 返回batch_id供后续查询使用
            return result.get('batch_id')
            
        else:
            print_error("数据上传失败！")
            print()
            print_error("错误信息:")
            print(f"  错误代码: {result.get('error', 'unknown')}")
            print(f"  错误描述: {result.get('error_description', result.get('message', 'unknown'))}")
            
            if result.get('errors'):
                print()
                print_error("详细错误:")
                for error in result['errors'][:5]:  # 只显示前5个
                    print(f"  - {error}")
            
            return None
            
    except requests.exceptions.ConnectionError:
        print_error("无法连接到服务器！")
        print_info("请确保Flask应用正在运行: python app.py")
        return None
        
    except Exception as e:
        print_error(f"请求失败: {str(e)}")
        return None


def check_detection_status(batch_id, access_token):
    """查询检测状态"""
    
    if not batch_id:
        return
    
    print()
    print("=" * 60)
    print("查询检测状态")
    print("=" * 60)
    print()
    
    status_url = f"{BASE_URL}/excel/quality-process"
    
    print_info(f"批次ID: {batch_id}")
    print_info("开始轮询检测状态...")
    print()
    
    max_attempts = 30  # 最多查询30次（1分钟）
    attempt = 0
    
    while attempt < max_attempts:
        try:
            response = requests.post(
                status_url,
                json={
                    "filename": batch_id,
                    "unique_filename": batch_id  # 直接指定unique_filename，绕过时间戳解析
                },
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {access_token}"
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                status = result.get('status')
                
                if status == 'pending':
                    print(f"⏳ [{attempt + 1}] 队列中等待...")
                    
                elif status == 'processing':
                    progress = result.get('progress', {})
                    current = progress.get('current', 0)
                    total = progress.get('total', 0)
                    print(f"🔄 [{attempt + 1}] 检测中... {current}/{total}")
                    
                elif status == 'completed':
                    print_success("检测完成！")
                    print()
                    result_data = result.get('result', {})
                    print_info("结果信息:")
                    print(f"  CSV文件: {result_data.get('csv_filename', 'N/A')}")
                    print(f"  Excel文件: {result_data.get('excel_filename', 'N/A')}")
                    print(f"  已处理: {result_data.get('rows_processed', 0)} 条")
                    return True
                    
                elif status == 'failed':
                    print_error(f"检测失败: {result.get('message', 'unknown')}")
                    return False
                    
                else:
                    print_warning(f"未知状态: {status}")
            
            elif response.status_code == 404:
                print_error(f"批次不存在: {batch_id}")
                break
                    
            else:
                print_error(f"查询失败: HTTP {response.status_code}")
                try:
                    error_info = response.json()
                    print_error(f"错误: {error_info.get('error_description', 'unknown')}")
                except:
                    print_error(f"响应内容: {response.text[:200]}")
                break
                
            attempt += 1
            time.sleep(2)  # 每2秒查询一次
            
        except Exception as e:
            print_error(f"查询失败: {str(e)}")
            break
    
    print_warning("查询超时")
    return False


def main():
    """主函数"""
    print("=" * 60)
    print()
    
    # 第一步：获取访问令牌
    print("【步骤1】获取OAuth访问令牌")
    
    # 如果已配置ACCESS_TOKEN，直接使用
    if ACCESS_TOKEN:
        print_success("使用已配置的访问令牌")
        access_token = ACCESS_TOKEN
    else:
        print_info("未配置访问令牌，自动申请...")
        access_token = get_access_token()
        if not access_token:
            print_error("无法获取访问令牌，测试终止")
            print_info("请检查CLIENT_ID和CLIENT_SECRET配置")
            return
    print()
    
    # 第二步：测试上传
    print("【步骤2】上传工单数据")
    batch_id = test_upload_data(access_token)
    
    # 如果上传成功，查询检测状态
    if batch_id:
        print()
        print("【步骤3】查询检测状态")
        check_detection_status(batch_id, access_token)
    
    print()
    print("=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
