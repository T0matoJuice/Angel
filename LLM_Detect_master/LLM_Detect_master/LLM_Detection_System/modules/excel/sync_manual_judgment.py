#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同步人工判断的工单性质数据

功能说明：
1. 通过API获取人工判断的工单性质数据
2. 根据工单单号（workAlone）更新数据库中对应记录的 workOrderNature_correct 字段
3. 支持按日期范围查询数据

使用方法：
    python sync_manual_judgment.py --start-date 2025-01-01 --end-date 2025-01-01
    
注意：需要连接内部VPN才能调用API
"""

import sys
import os
import argparse
import requests
from datetime import datetime
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from modules.auth import db
from modules.excel.models import WorkorderData


class ManualJudgmentSyncer:
    """人工判断数据同步器"""
    
    # API配置
    LOGIN_URL = "http://qmstest.angelgroup.com.cn:8080/ssoServer/oauth/login"
    DATA_URL = "http://qmstest.angelgroup.com.cn:8080/qualityDataAnalysis/baseData/crmMaintenanceData/selectJudgedOriginal"
    
    # 登录认证信息
    LOGIN_AUTH = "Basic cXVhbGl0eURhdGE6JDJhJDEwJGZDOU40WUxOWUlCLzgyM3ZQcjd2b2U3dWtndUtHSkRNYzdya210UmkxeHVCQ0lZZUcwMkJX"
    LOGIN_BODY = {
        "username": "ai",
        "password": "Ai@2025."
    }
    
    def __init__(self):
        """初始化同步器"""
        self.token = None
        self.session = requests.Session()
        # 设置超时时间
        self.timeout = 30
        
    def get_bearer_token(self):
        """
        获取Bearer Token
        
        Returns:
            str: Bearer Token，格式为 "Bearer xxx"
            
        Raises:
            Exception: 登录失败时抛出异常
        """
        print("正在获取Bearer Token...")
        
        try:
            headers = {
                "Authorization": self.LOGIN_AUTH,
                "Content-Type": "application/json"
            }
            
            response = self.session.post(
                self.LOGIN_URL,
                json=self.LOGIN_BODY,
                headers=headers,
                timeout=self.timeout
            )
            
            # 检查响应状态
            response.raise_for_status()
            
            # 解析响应
            result = response.json()
            
            # 提取token（根据实际API响应结构调整）
            # 假设响应格式为: {"access_token": "xxx", ...}
            if "access_token" in result:
                token = result["access_token"]
                self.token = f"Bearer {token}"
                print(f"✓ Token获取成功: {self.token[:50]}...")
                return self.token
            else:
                raise Exception(f"响应中未找到access_token: {result}")
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"获取Token失败: {str(e)}")
    
    def fetch_manual_judgment_data(self, start_date, end_date):
        """
        获取人工判断的工单数据
        
        Args:
            start_date (str): 开始日期，格式：YYYY-MM-DD
            end_date (str): 结束日期，格式：YYYY-MM-DD
            
        Returns:
            list: 工单数据列表，每条数据包含 workAlone 和 workOrderNature
            
        Raises:
            Exception: API调用失败时抛出异常
        """
        # 确保已获取token
        if not self.token:
            self.get_bearer_token()
        
        print(f"\n正在获取人工判断数据 ({start_date} ~ {end_date})...")
        
        try:
            headers = {
                "Authorization": self.token
            }
            
            params = {
                "maintenanceTimeStart": start_date,
                "maintenanceTimeEnd": end_date
            }
            
            response = self.session.get(
                self.DATA_URL,
                headers=headers,
                params=params,
                timeout=self.timeout
            )
            
            # 检查响应状态
            response.raise_for_status()
            
            # 解析响应
            result = response.json()
            
            # 提取数据（根据实际API响应结构调整）
            # 假设响应格式为: {"data": [...], ...} 或直接是数组 [...]
            if isinstance(result, list):
                data_list = result
            elif isinstance(result, dict) and "data" in result:
                data_list = result["data"]
            else:
                raise Exception(f"无法解析API响应: {result}")
            
            # 提取需要的字段
            extracted_data = []
            for item in data_list:
                if "workAlone" in item and "workOrderNature" in item:
                    extracted_data.append({
                        "workAlone": item["workAlone"],
                        "workOrderNature": item["workOrderNature"]
                    })
            
            print(f"✓ 成功获取 {len(extracted_data)} 条人工判断数据")
            return extracted_data
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"获取数据失败: {str(e)}")
    
    def update_database(self, data_list):
        """
        更新数据库中的 workOrderNature_correct 字段（优化版）
        
        Args:
            data_list (list): 工单数据列表
            
        Returns:
            dict: 更新统计信息
        """
        import sys
        import time
        from datetime import datetime, timedelta
        
        print("\n正在更新数据库...")
        print(f"API返回数据: {len(data_list)} 条")
        sys.stdout.flush()  # 强制刷新输出
        
        stats = {
            "total": len(data_list),
            "updated": 0,
            "not_found": 0,
            "errors": 0,
            "duplicate_count": 0,
            "api_records": len(data_list)  # API返回的记录数
        }
        
        # 记录开始时间
        start_time = time.time()
        last_progress_time = start_time
        
        # 批量处理：先构建工单号到人工判断的映射
        print("正在构建工单映射...")
        sys.stdout.flush()
        
        workorder_map = {}
        for item in data_list:
            work_alone = item["workAlone"]
            work_order_nature = item["workOrderNature"]
            workorder_map[work_alone] = work_order_nature
        
        print(f"✓ 映射构建完成，共 {len(workorder_map)} 个唯一工单号")
        sys.stdout.flush()
        
        # 批量查询数据库中存在的工单（性能优化）
        print("正在查询数据库中的工单...")
        sys.stdout.flush()
        
        unique_work_alones = list(workorder_map.keys())
        batch_size = 1000  # 每次查询1000个工单号
        all_db_records = []
        
        for i in range(0, len(unique_work_alones), batch_size):
            batch_work_alones = unique_work_alones[i:i+batch_size]
            batch_records = WorkorderData.query.filter(
                WorkorderData.workAlone.in_(batch_work_alones)
            ).all()
            all_db_records.extend(batch_records)
            
            # 显示查询进度
            progress = min(i + batch_size, len(unique_work_alones))
            percent = (progress / len(unique_work_alones)) * 100
            print(f"  查询进度: {progress}/{len(unique_work_alones)} ({percent:.1f}%)")
            sys.stdout.flush()
        
        print(f"✓ 数据库查询完成，找到 {len(all_db_records)} 条匹配记录")
        sys.stdout.flush()
        
        # 统计重复工单
        workalone_count = {}
        for record in all_db_records:
            workalone_count[record.workAlone] = workalone_count.get(record.workAlone, 0) + 1
        
        duplicate_workorders = {k: v for k, v in workalone_count.items() if v > 1}
        if duplicate_workorders:
            print(f"发现 {len(duplicate_workorders)} 个重复工单（共 {sum(duplicate_workorders.values())} 条记录）")
            sys.stdout.flush()
        
        # 更新数据库记录
        print("\n开始更新记录...")
        sys.stdout.flush()
        
        updated_count = 0
        for idx, record in enumerate(all_db_records, 1):
            work_alone = record.workAlone
            
            if work_alone in workorder_map:
                try:
                    # 更新字段
                    record.workOrderNature_correct = workorder_map[work_alone]
                    updated_count += 1
                    
                    # 每100条显示一次进度
                    if updated_count % 100 == 0:
                        elapsed = time.time() - start_time
                        percent = (idx / len(all_db_records)) * 100
                        speed = updated_count / elapsed if elapsed > 0 else 0
                        remaining = (len(all_db_records) - idx) / speed if speed > 0 else 0
                        
                        print(f"  进度: {idx}/{len(all_db_records)} ({percent:.1f}%) | "
                              f"已更新: {updated_count} | "
                              f"速度: {speed:.1f}条/秒 | "
                              f"预计剩余: {int(remaining)}秒")
                        sys.stdout.flush()
                        
                except Exception as e:
                    stats["errors"] += 1
                    print(f"  ✗ 更新失败 [{work_alone}]: {str(e)}")
                    sys.stdout.flush()
        
        stats["updated"] = updated_count
        stats["duplicate_count"] = len(duplicate_workorders)
        stats["not_found"] = len(data_list) - len(all_db_records)
        
        # 提交所有更改
        print("\n正在提交数据库更改...")
        sys.stdout.flush()
        
        try:
            db.session.commit()
            elapsed = time.time() - start_time
            print(f"✓ 数据库更新完成（耗时: {elapsed:.1f}秒）")
            sys.stdout.flush()
        except Exception as e:
            db.session.rollback()
            print(f"✗ 提交失败，已回滚: {str(e)}")
            sys.stdout.flush()
            raise Exception(f"提交数据库更改失败: {str(e)}")
        
        return stats
    
    def sync(self, start_date, end_date):
        from app import app
        """
        执行完整的同步流程
        
        Args:
            start_date (str): 开始日期，格式：YYYY-MM-DD
            end_date (str): 结束日期，格式：YYYY-MM-DD
        """
        print("=" * 60)
        print("人工判断工单性质数据同步工具")
        print("=" * 60)
        
        try:
            # 1. 获取Token
            self.get_bearer_token()
            
            # 2. 获取人工判断数据
            data_list = self.fetch_manual_judgment_data(start_date, end_date)
            
            if not data_list:
                print("\n⚠ 未获取到任何数据，同步终止")
                return
            
            # 3. 更新数据库
            stats = self.update_database(data_list)
            
            # 4. 输出统计信息
            print("\n" + "=" * 60)
            print("同步完成统计")
            print("=" * 60)
            print(f"总记录数:     {stats['total']}")
            print(f"成功更新:     {stats['updated']}")
            print(f"未找到工单:   {stats['not_found']}")
            print(f"更新失败:     {stats['errors']}")
            print(f"重复工单数:   {stats['duplicate_count']} (这些工单在数据库中有多条记录)")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n✗ 同步失败: {str(e)}")
            sys.exit(1)


def validate_date(date_str):
    """
    验证日期格式
    
    Args:
        date_str (str): 日期字符串
        
    Returns:
        str: 验证通过的日期字符串
        
    Raises:
        argparse.ArgumentTypeError: 日期格式错误时抛出
    """
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return date_str
    except ValueError:
        raise argparse.ArgumentTypeError(f"日期格式错误: {date_str}，应为 YYYY-MM-DD")


def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description="同步人工判断的工单性质数据到数据库",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 同步2025年1月1日的数据
  python sync_manual_judgment.py --start-date 2025-01-01 --end-date 2025-01-01
  
  # 同步2025年1月的数据
  python sync_manual_judgment.py --start-date 2025-01-01 --end-date 2025-01-31

注意:
  - 需要连接内部VPN才能调用API
  - 确保数据库连接配置正确
        """
    )
    
    parser.add_argument(
        "--start-date",
        type=validate_date,
        required=True,
        help="开始日期，格式：YYYY-MM-DD"
    )
    
    parser.add_argument(
        "--end-date",
        type=validate_date,
        required=True,
        help="结束日期，格式：YYYY-MM-DD"
    )
    
    args = parser.parse_args()
    
    # 使用Flask应用上下文（用于数据库操作）
    with app.app_context():
        # 执行同步
        syncer = ManualJudgmentSyncer()
        syncer.sync(args.start_date, args.end_date)


if __name__ == "__main__":
    main()
