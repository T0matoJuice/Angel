#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整流程测试脚本 - 包含上传和检测监控
测试流程：上传 → 入库 → AI检测 → 结果验证
"""

import requests
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import random


# 真实的工单数据（用户提供）
REAL_WORKORDER_DATA = {
    "workorders": [
        {"工单性质":None,"工单单号":"WO0018329556","故障组":"净饮机","新件名称":None,"来电内容":None,"保内保外":"保内","服务项目或故障现象":None,"批次入库日期":None,"故障类别":"电气类","处理方案简述或备注":"打开冰水开关","产品名称":"商务直饮机 立式反渗透压缩机制冷商务直饮机AHR26-1030K1Y(白色+银色)","旧件名称":None,"现场诊断故障现象":None,"购机日期":"2025-08-07","开发主体":None,"故障部位名称":"跷板开关 KCD11-1大绿","安装日期":None,"维修方式":"上门维修","判定依据":None},
        {"工单性质":None,"工单单号":"WO0018329558","故障组":"净饮机","新件名称":None,"来电内容":None,"保内保外":"保内","服务项目或故障现象":None,"批次入库日期":None,"故障类别":"电气类","处理方案简述或备注":"结冰需要更换温控","产品名称":"商务直饮机 立式反渗透压缩机制冷商务直饮机AHR26-1030K1Y(白色+银色)","旧件名称":None,"现场诊断故障现象":None,"购机日期":"2025-09-30","开发主体":None,"故障部位名称":"手动复位温控器-HB 110℃","安装日期":None,"维修方式":"上门维修","判定依据":None},
        {"工单性质":None,"工单单号":"WO0018329559","故障组":"净饮机","新件名称":None,"来电内容":None,"保内保外":"保外","服务项目或故障现象":None,"批次入库日期":None,"故障类别":"外观结构类","处理方案简述或备注":"压缩机异响无法维修","产品名称":"商务直饮机 立式反渗透压缩机制冷商务直饮机AHR26-1030K1Y(白色+银色)","旧件名称":None,"现场诊断故障现象":None,"购机日期":"2025-06-07","开发主体":None,"故障部位名称":"压缩机压板 90*20*2(原色)","安装日期":None,"维修方式":"上门维修","判定依据":None}
    ]
}


def upload_batch(url: str, batch_id: str, workorder_count: int = 3, token: str = None):
    """上传一个批次"""
    data = {
        "unique_filename": batch_id,
        "filename": batch_id,
        "workorders": [],
        "account": "TEST_QMS"
    }
    
    for i in range(workorder_count):
        workorder = REAL_WORKORDER_DATA["workorders"][i % 3].copy()
        workorder["工单单号"] = f"TEST_{batch_id}_{i:04d}"
        data["workorders"].append(workorder)
    
    try:
        start_time = time.time()
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        response = requests.post(url, json=data, headers=headers, timeout=60)
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 批次 {batch_id}: 成功 - {result.get('success_count', 0)}条入库 - 耗时{elapsed:.2f}秒")
            return True, elapsed, result, batch_id
        else:
            print(f"❌ 批次 {batch_id}: 失败 - HTTP {response.status_code}")
            return False, elapsed, {'error': response.text[:100]}, batch_id
    
    except Exception as e:
        print(f"❌ 批次 {batch_id}: 异常 - {str(e)}")
        return False, 0, {'error': str(e)}, batch_id


def check_queue_status(base_url: str, token: str = None):
    """查询队列状态"""
    url = f"{base_url}/excel/api/queue/info"
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None


def verify_detection_results(batch_id: str, base_url: str, token: str = None, expected_count: int = 0):
    """验证检测结果"""
    url = f"{base_url}/excel/api/history"
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code != 200:
            return None
        
        data = response.json()
        if not data.get('success'):
            return None
        
        records = data.get('records', [])
        batch_records = [r for r in records if r.get('filename') == batch_id]
        
        if not batch_records:
            return None
        
        total_count = len(batch_records)
        filled_count = sum(1 for r in batch_records if r.get('workOrderNature'))
        quality_count = sum(1 for r in batch_records if r.get('workOrderNature') == '质量工单')
        non_quality_count = sum(1 for r in batch_records if r.get('workOrderNature') == '非质量工单')
        
        return {
            'total_count': total_count,
            'filled_count': filled_count,
            'quality_count': quality_count,
            'non_quality_count': non_quality_count,
            'fill_rate': filled_count / total_count * 100 if total_count > 0 else 0
        }
        
    except:
        return None


def monitor_detection(batch_ids: list, base_url: str, token: str = None, 
                      max_wait_time: int = 600, check_interval: int = 10):
    """监控检测过程"""
    print("\n" + "=" * 80)
    print("🔍 开始监控AI检测过程")
    print("=" * 80)
    print(f"📊 监控批次数: {len(batch_ids)}")
    print(f"⏰ 最大等待时间: {max_wait_time}秒")
    print(f"🔄 检查间隔: {check_interval}秒")
    print("=" * 80)
    
    start_time = time.time()
    last_queue_size = None
    completed_batches = set()
    
    while time.time() - start_time < max_wait_time:
        elapsed = time.time() - start_time
        
        # 查询队列状态
        queue_info = check_queue_status(base_url, token)
        if queue_info:
            queue_size = queue_info.get('queue_size', 0)
            current_task = queue_info.get('current_task', '')
            
            if queue_size != last_queue_size:
                print(f"\n[{elapsed:.0f}s] 队列状态:")
                print(f"   - 队列长度: {queue_size}")
                print(f"   - 当前任务: {current_task or '无'}")
                last_queue_size = queue_size
        
        # 检查每个批次的检测结果
        for batch_id in batch_ids:
            if batch_id in completed_batches:
                continue
            
            result = verify_detection_results(batch_id, base_url, token)
            if result and result['fill_rate'] >= 99:
                completed_batches.add(batch_id)
                print(f"✅ 批次 {batch_id}: 检测完成 ({result['filled_count']}/{result['total_count']})")
        
        # 如果所有批次都完成了
        if len(completed_batches) == len(batch_ids):
            print(f"\n🎉 所有批次检测完成！总耗时 {elapsed:.0f} 秒")
            break
        
        # 显示进度
        progress = len(completed_batches) / len(batch_ids) * 100
        print(f"[{elapsed:.0f}s] 检测进度: {len(completed_batches)}/{len(batch_ids)} ({progress:.1f}%)", end='\r')
        
        time.sleep(check_interval)
    
    # 最终统计
    print("\n\n" + "=" * 80)
    print("📊 检测结果统计")
    print("=" * 80)
    
    total_workorders = 0
    total_filled = 0
    total_quality = 0
    total_non_quality = 0
    
    for batch_id in batch_ids:
        result = verify_detection_results(batch_id, base_url, token)
        if result:
            total_workorders += result['total_count']
            total_filled += result['filled_count']
            total_quality += result['quality_count']
            total_non_quality += result['non_quality_count']
            
            print(f"\n批次: {batch_id}")
            print(f"   - 总工单数: {result['total_count']}")
            print(f"   - 已判定数: {result['filled_count']} ({result['fill_rate']:.1f}%)")
            print(f"   - 质量工单: {result['quality_count']}")
            print(f"   - 非质量工单: {result['non_quality_count']}")
    
    overall_fill_rate = total_filled / total_workorders * 100 if total_workorders > 0 else 0
    
    print(f"\n总计:")
    print(f"   - 总工单数: {total_workorders}")
    print(f"   - 已判定数: {total_filled} ({overall_fill_rate:.1f}%)")
    print(f"   - 质量工单: {total_quality}")
    print(f"   - 非质量工单: {total_non_quality}")
    
    if overall_fill_rate >= 99:
        print(f"\n🎯 评估: ✅ 优秀！检测完成度 {overall_fill_rate:.1f}%")
    elif overall_fill_rate >= 90:
        print(f"\n🎯 评估: ✅ 良好！检测完成度 {overall_fill_rate:.1f}%")
    else:
        print(f"\n🎯 评估: ⚠️  较低，检测完成度 {overall_fill_rate:.1f}%")
    
    print("=" * 80)


def run_full_test(api_url: str, base_url: str, total_batches: int = 5, 
                  workorders_per_batch: int = 20, token: str = None, 
                  monitor: bool = True):
    """运行完整流程测试"""
    print("=" * 80)
    print("🚀 完整流程测试：上传 → 入库 → AI检测 → 结果验证")
    print("=" * 80)
    print(f"📊 配置: {total_batches}批次 × {workorders_per_batch}工单 = {total_batches * workorders_per_batch}条数据")
    print(f"🔍 检测监控: {'已启用' if monitor else '已禁用'}")
    print("=" * 80)
    print()
    
    # 第一阶段：上传数据
    print("📤 第一阶段：批量上传数据")
    print("-" * 80)
    
    success_count = 0
    failed_count = 0
    uploaded_batches = []
    
    for i in range(total_batches):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        random_suffix = random.randint(1000, 9999)
        batch_id = f"test_{timestamp}_{random_suffix}"
        
        success, elapsed, result, bid = upload_batch(api_url, batch_id, workorders_per_batch, token)
        if success:
            success_count += 1
            uploaded_batches.append(batch_id)
        else:
            failed_count += 1
        
        time.sleep(0.5)  # 批次间延迟
    
    print(f"\n✅ 上传完成: 成功{success_count}, 失败{failed_count}")
    
    # 第二阶段：监控检测
    if monitor and uploaded_batches:
        time.sleep(2)  # 等待2秒让队列开始处理
        monitor_detection(uploaded_batches, base_url, token)
    
    print("\n🎉 测试完成！")


if __name__ == '__main__':
    # 配置
    BASE_URL = "http://localhost:5000"
    API_URL = f"{BASE_URL}/excel/quality-dataupload"
    OAUTH_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjbGllbnRfaWQiOiJhcGlfdGVzdF9jbGllbnRfdG9tYXRvIiwic2NvcGVzIjpbIioiXSwiZXhwIjoxNzY1ODczODIxLCJpYXQiOjE3NjUyNjkwMjEsInR5cGUiOiJhY2Nlc3NfdG9rZW4ifQ.V9r_NiRtEBmnBKgeUr-t0VsUIxNn7E3ouYbOYO4q3Ic"
    
    print("请选择测试模式:")
    print("1. 快速测试 (5批次 × 10工单 = 50条，含检测监控)")
    print("2. 标准测试 (10批次 × 20工单 = 200条，含检测监控)")
    print("3. 压力测试 (20批次 × 50工单 = 1000条，含检测监控)")
    print("4. 仅上传测试 (不监控检测)")
    
    choice = input("\n请选择 (1-4，默认1): ").strip() or '1'
    
    scenarios = {
        '1': {'batches': 5, 'workorders': 10, 'monitor': True},
        '2': {'batches': 10, 'workorders': 20, 'monitor': True},
        '3': {'batches': 20, 'workorders': 50, 'monitor': True},
        '4': {'batches': 10, 'workorders': 20, 'monitor': False}
    }
    
    config = scenarios.get(choice, scenarios['1'])
    
    print(f"\n⏳ 3秒后开始测试...\n")
    time.sleep(3)
    
    run_full_test(
        API_URL,
        BASE_URL,
        total_batches=config['batches'],
        workorders_per_batch=config['workorders'],
        token=OAUTH_TOKEN,
        monitor=config['monitor']
    )
