#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本：模拟API响应，测试数据同步逻辑

功能说明：
在无法连接VPN的情况下，使用模拟数据测试同步逻辑是否正确

使用方法：
    python test_sync_manual_judgment.py
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from modules.auth import db
from modules.excel.models import WorkorderData
from app import app


def test_sync_logic():
    """测试同步逻辑"""
    
    print("=" * 60)
    print("测试：人工判断数据同步逻辑")
    print("=" * 60)
    
    with app.app_context():
        # 模拟API返回的数据
        mock_data = [
            {
                "workAlone": "WO0014674556",
                "workOrderNature": "质量工单"
            },
            {
                "workAlone": "WO0014674557",
                "workOrderNature": "非质量工单"
            },
            {
                "workAlone": "WO9999999999",  # 不存在的工单
                "workOrderNature": "质量工单"
            }
        ]
        
        print(f"\n模拟数据: {len(mock_data)} 条")
        for item in mock_data:
            print(f"  - {item['workAlone']}: {item['workOrderNature']}")
        
        # 统计信息
        stats = {
            "total": len(mock_data),
            "updated": 0,
            "not_found": 0,
            "errors": 0
        }
        
        print("\n开始测试更新逻辑...")
        
        for item in mock_data:
            work_alone = item["workAlone"]
            work_order_nature = item["workOrderNature"]
            
            try:
                # 查找对应的工单记录
                workorder = WorkorderData.query.filter_by(workAlone=work_alone).first()
                
                if workorder:
                    print(f"\n✓ 找到工单: {work_alone}")
                    print(f"  当前AI判断: {workorder.workOrderNature}")
                    print(f"  人工判断: {work_order_nature}")
                    
                    # 模拟更新（不实际提交）
                    # workorder.workOrderNature_correct = work_order_nature
                    stats["updated"] += 1
                    print(f"  → 将更新 workOrderNature_correct 为: {work_order_nature}")
                else:
                    stats["not_found"] += 1
                    print(f"\n⚠ 未找到工单: {work_alone}")
                    
            except Exception as e:
                stats["errors"] += 1
                print(f"\n✗ 处理失败 [{work_alone}]: {str(e)}")
        
        # 不提交更改（测试模式）
        # db.session.commit()
        db.session.rollback()
        
        # 输出统计信息
        print("\n" + "=" * 60)
        print("测试结果统计")
        print("=" * 60)
        print(f"总记录数:     {stats['total']}")
        print(f"可以更新:     {stats['updated']}")
        print(f"未找到工单:   {stats['not_found']}")
        print(f"处理失败:     {stats['errors']}")
        print("=" * 60)
        print("\n注意: 这是测试模式，未实际修改数据库")
        print("=" * 60)


def check_field_exists():
    """检查 workOrderNature_correct 字段是否存在"""
    
    print("\n" + "=" * 60)
    print("检查数据库字段")
    print("=" * 60)
    
    with app.app_context():
        try:
            # 检查字段是否存在
            sql = """
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_COMMENT
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'workorder_data'
            AND COLUMN_NAME = 'workOrderNature_correct';
            """
            
            result = db.session.execute(db.text(sql)).fetchone()
            
            if result:
                print("\n✓ 字段已存在")
                print(f"  字段名: {result[0]}")
                print(f"  类型: {result[1]}")
                print(f"  允许NULL: {result[2]}")
                print(f"  注释: {result[3]}")
            else:
                print("\n✗ 字段不存在")
                print("  请先执行: python modules\\excel\\add_workorder_nature_correct_field.py")
            
            print("=" * 60)
            
        except Exception as e:
            print(f"\n✗ 检查失败: {str(e)}")
            print("=" * 60)


if __name__ == "__main__":
    # 检查字段是否存在
    check_field_exists()
    
    # 测试同步逻辑
    test_sync_logic()
