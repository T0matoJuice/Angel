#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本：添加 workOrderNature_correct 字段

功能说明：
在 workorder_data 表中添加 workOrderNature_correct 字段，用于存储人工判断的工单性质

使用方法：
    python add_workorder_nature_correct_field.py
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from modules.auth import db
from app import app


def add_field():
    """添加 workOrderNature_correct 字段到 workorder_data 表"""
    
    print("=" * 60)
    print("数据库迁移：添加 workOrderNature_correct 字段")
    print("=" * 60)
    
    with app.app_context():
        try:
            # 执行SQL添加字段
            sql = """
            ALTER TABLE workorder_data 
            ADD COLUMN workOrderNature_correct VARCHAR(255) NULL 
            COMMENT '工单性质（人工判断结果）'
            AFTER workOrderNature;
            """
            
            print("\n正在执行SQL...")
            print(sql)
            
            db.session.execute(db.text(sql))
            db.session.commit()
            
            print("\n✓ 字段添加成功！")
            print("\n字段信息:")
            print("  - 字段名: workOrderNature_correct")
            print("  - 类型: VARCHAR(255)")
            print("  - 允许NULL: 是")
            print("  - 位置: workOrderNature 字段之后")
            print("=" * 60)
            
        except Exception as e:
            db.session.rollback()
            
            # 检查是否是字段已存在的错误
            if "Duplicate column name" in str(e):
                print("\n⚠ 字段已存在，无需重复添加")
                print("=" * 60)
            else:
                print(f"\n✗ 迁移失败: {str(e)}")
                print("=" * 60)
                sys.exit(1)


if __name__ == "__main__":
    add_field()
