#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版压力测试脚本 - 使用真实数据
直接使用用户提供的真实工单数据进行测试
"""

import requests
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import random


# 真实的工单数据（用户提供）
REAL_WORKORDER_DATA = {
    "unique_filename": "batch_001",
    "filename": "batch_001",
    "workorders": [
        {"工单性质":None,"工单单号":"WO0018329556","故障组":"净饮机","新件名称":None,"来电内容":None,"保内保外":"保内","服务项目或故障现象":None,"批次入库日期":None,"故障类别":"电气类","处理方案简述或备注":"打开冰水开关","产品名称":"商务直饮机 立式反渗透压缩机制冷商务直饮机AHR26-1030K1Y(白色+银色)","旧件名称":None,"现场诊断故障现象":None,"购机日期":"2025-08-07","开发主体":None,"故障部位名称":"跷板开关 KCD11-1大绿,CE,CQC,UL,16A 125VAC,16(4)A 250VAC T85(白色主体,绿色按钮)","安装日期":None,"维修方式":"上门维修","判定依据":None},
        {"工单性质":None,"工单单号":"WO0018329558","故障组":"净饮机","新件名称":None,"来电内容":None,"保内保外":"保内","服务项目或故障现象":None,"批次入库日期":None,"故障类别":"电气类","处理方案简述或备注":"结冰需要更换温控","产品名称":"商务直饮机 立式反渗透压缩机制冷商务直饮机AHR26-1030K1Y(白色+银色)","旧件名称":None,"现场诊断故障现象":None,"购机日期":"2025-09-30","开发主体":None,"故障部位名称":"手动复位温控器-HB 110℃，T10M-110/H121, 250V/30A,四个接线脚,认证号CQC14002117082(/)","安装日期":None,"维修方式":"上门维修","判定依据":None},
        {"工单性质":None,"工单单号":"WO0018329559","故障组":"净饮机","新件名称":None,"来电内容":None,"保内保外":"保外","服务项目或故障现象":None,"批次入库日期":None,"故障类别":"外观结构类","处理方案简述或备注":"压缩机异响无法维修","产品名称":"商务直饮机 立式反渗透压缩机制冷商务直饮机AHR26-1030K1Y(白色+银色)","旧件名称":None,"现场诊断故障现象":None,"购机日期":"2025-06-07","开发主体":None,"故障部位名称":"压缩机压板 90*20*2(原色)","安装日期":None,"维修方式":"上门维修","判定依据":None}
    ],
    "account": "QMS"
}


def upload_batch(url: str, batch_id: str, workorder_count: int = 3, token: str = None):
    """上传一个批次"""
    # 复制真实数据
    data = {
        "unique_filename": batch_id,
        "filename": batch_id,
        "workorders": [],
        "account": "TEST_QMS"
    }
    
    # 使用真实工单数据，修改工单单号避免冲突
    for i in range(workorder_count):
        workorder = REAL_WORKORDER_DATA["workorders"][i % 3].copy()
        # 生成唯一工单号
        workorder["工单单号"] = f"TEST_{batch_id}_{i:04d}"
        data["workorders"].append(workorder)
    
    try:
        start_time = time.time()
        
        # 构建请求头
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        response = requests.post(
            url,
            json=data,
            headers=headers,
            timeout=60
        )
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 批次 {batch_id}: 成功 - {result.get('success_count', 0)}条入库 - 耗时{elapsed:.2f}秒")
            return True, elapsed, result
        elif response.status_code == 429:
            print(f"⚠️  批次 {batch_id}: 限流 - {response.json().get('error_description')}")
            return False, elapsed, {'error': 'rate_limited'}
        elif response.status_code == 503:
            print(f"⚠️  批次 {batch_id}: 过载 - {response.json().get('error_description')}")
            return False, elapsed, {'error': 'overload'}
        else:
            print(f"❌ 批次 {batch_id}: 失败 - HTTP {response.status_code}")
            return False, elapsed, {'error': response.text[:100]}
    
    except Exception as e:
        print(f"❌ 批次 {batch_id}: 异常 - {str(e)}")
        return False, 0, {'error': str(e)}


def run_test(url: str, total_batches: int = 20, workorders_per_batch: int = 50, 
             max_workers: int = 10, token: str = None):
    """运行测试"""
    print("=" * 80)
    print("🚀 高并发上传压力测试")
    print("=" * 80)
    print(f"📊 配置: {total_batches}批次 × {workorders_per_batch}工单 = {total_batches * workorders_per_batch}条数据")
    print(f"🔧 并发线程: {max_workers}")
    print("=" * 80)
    print()
    
    success_count = 0
    failed_count = 0
    response_times = []
    
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        
        for i in range(total_batches):
            # 生成唯一批次ID
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            random_suffix = random.randint(1000, 9999)
            batch_id = f"test_{timestamp}_{random_suffix}"
            
            future = executor.submit(upload_batch, url, batch_id, workorders_per_batch, token)
            futures.append(future)
            
            # 小延迟避免瞬时压力过大
            time.sleep(0.1)
        
        # 等待所有任务完成
        for future in as_completed(futures):
            success, elapsed, result = future.result()
            if success:
                success_count += 1
                response_times.append(elapsed)
            else:
                failed_count += 1
    
    total_time = time.time() - start_time
    
    # 打印结果
    print()
    print("=" * 80)
    print("📊 测试结果")
    print("=" * 80)
    print(f"✅ 成功: {success_count}/{total_batches} ({success_count/total_batches*100:.2f}%)")
    print(f"❌ 失败: {failed_count}/{total_batches} ({failed_count/total_batches*100:.2f}%)")
    print(f"⏱️  总耗时: {total_time:.2f}秒")
    print(f"⚡ 平均QPS: {total_batches/total_time:.2f}请求/秒")
    
    if response_times:
        avg_time = sum(response_times) / len(response_times)
        print(f"📈 平均响应时间: {avg_time:.2f}秒")
        print(f"📈 最快响应: {min(response_times):.2f}秒")
        print(f"📈 最慢响应: {max(response_times):.2f}秒")
    
    success_rate = success_count / total_batches * 100
    if success_rate >= 99:
        print(f"\n🎯 评估: ✅ 优秀！成功率 {success_rate:.2f}%")
    elif success_rate >= 95:
        print(f"\n🎯 评估: ✅ 良好！成功率 {success_rate:.2f}%")
    elif success_rate >= 90:
        print(f"\n🎯 评估: ⚠️  一般，成功率 {success_rate:.2f}%")
    else:
        print(f"\n🎯 评估: ❌ 较差，成功率 {success_rate:.2f}%")
    
    print("=" * 80)


if __name__ == '__main__':
    # 配置
    API_URL = "http://localhost:5000/excel/quality-dataupload"
    
    # OAuth Token（从你的截图中获取）
    # 如果需要认证，请填入你的token
    OAUTH_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjbGllbnRfaWQiOiJhcGlfdGVzdF9jbGllbnRfdG9tYXRvIiwic2NvcGVzIjpbIioiXSwiZXhwIjoxNzY1ODczODIxLCJpYXQiOjE3NjUyNjkwMjEsInR5cGUiOiJhY2Nlc3NfdG9rZW4ifQ.V9r_NiRtEBmnBKgeUr-t0VsUIxNn7E3ouYbOYO4q3Ic"
    
    print("请选择测试强度:")
    print("1. 轻度测试 (10批次 × 20工单 = 200条)")
    print("2. 中度测试 (30批次 × 50工单 = 1500条)")
    print("3. 高度测试 (50批次 × 50工单 = 2500条)")
    print("4. 极限测试 (100批次 × 100工单 = 10000条)")
    
    choice = input("\n请选择 (1-4，默认2): ").strip() or '2'
    
    scenarios = {
        '1': {'batches': 10, 'workorders': 20, 'workers': 5},
        '2': {'batches': 30, 'workorders': 50, 'workers': 10},
        '3': {'batches': 50, 'workorders': 50, 'workers': 20},
        '4': {'batches': 100, 'workorders': 100, 'workers': 30}
    }
    
    config = scenarios.get(choice, scenarios['2'])
    
    print(f"\n⏳ 3秒后开始测试...\n")
    time.sleep(3)
    
    run_test(
        API_URL,
        total_batches=config['batches'],
        workorders_per_batch=config['workorders'],
        max_workers=config['workers'],
        token=OAUTH_TOKEN  # 传递token
    )
