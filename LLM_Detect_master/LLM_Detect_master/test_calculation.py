#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试数据计算逻辑
"""
import sys
sys.path.insert(0, 'LLM_Detection_System')

from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
env_path = Path('LLM_Detection_System') / '.env'
load_dotenv(env_path)

from flask import Flask
from modules.common.config import init_app_config
from modules.auth import init_auth, db
from modules.drawing.models import DrawingData
from modules.excel.models import WorkorderData
from sqlalchemy import func

# 创建应用
app = Flask(__name__)
init_app_config(app)
init_auth(app)

print("="*80)
print("数据计算逻辑测试")
print("="*80)

with app.app_context():
    print("\n【1. 图纸符合率测试】")
    print("-"*80)
    
    # 查询已完成的图纸总数
    completed_total = db.session.query(func.count(DrawingData.id)).filter(
        DrawingData.status == 'completed'
    ).scalar() or 0
    print(f"✅ 已完成检测的图纸总数: {completed_total}")
    
    # 查询conclusion='符合'的数量
    compliant_count = db.session.query(func.count(DrawingData.id)).filter(
        DrawingData.status == 'completed',
        DrawingData.conclusion == '符合'
    ).scalar() or 0
    print(f"✅ conclusion='符合'的数量: {compliant_count}")
    
    # 查询conclusion='不符合'的数量
    non_compliant_count = db.session.query(func.count(DrawingData.id)).filter(
        DrawingData.status == 'completed',
        DrawingData.conclusion == '不符合'
    ).scalar() or 0
    print(f"❌ conclusion='不符合'的数量: {non_compliant_count}")
    
    # 查询其他值
    other_count = completed_total - compliant_count - non_compliant_count
    if other_count > 0:
        print(f"⚠️  其他值的数量: {other_count}")
        # 查看具体是什么值
        other_values = db.session.query(DrawingData.conclusion).filter(
            DrawingData.status == 'completed',
            DrawingData.conclusion != '符合',
            DrawingData.conclusion != '不符合'
        ).distinct().all()
        print(f"   其他值包括: {[v[0] for v in other_values]}")
    
    # 计算符合率
    if completed_total > 0:
        rate = round((compliant_count / completed_total) * 100, 1)
        print(f"\n📊 图纸符合率: {rate}% ({compliant_count}/{completed_total})")
    else:
        print(f"\n📊 图纸符合率: 0.0% (无数据)")
    
    print("\n" + "="*80)
    print("\n【2. 工单问题比例测试】")
    print("-"*80)
    
    # 查询工单总数
    workorder_total = db.session.query(func.count(WorkorderData.id)).scalar() or 0
    print(f"✅ 工单总数: {workorder_total}")
    
    # 查询质量问题工单
    quality_issues = db.session.query(func.count(WorkorderData.id)).filter(
        WorkorderData.workOrderNature == '质量问题'
    ).scalar() or 0
    print(f"⚠️  质量问题工单: {quality_issues}")
    
    # 查询非质量问题工单
    non_quality = db.session.query(func.count(WorkorderData.id)).filter(
        WorkorderData.workOrderNature != '质量问题'
    ).scalar() or 0
    print(f"✅ 非质量问题工单: {non_quality}")
    
    # 查看workOrderNature的所有值
    print(f"\n📋 workOrderNature字段的所有值:")
    nature_stats = db.session.query(
        WorkorderData.workOrderNature,
        func.count(WorkorderData.id).label('count')
    ).group_by(WorkorderData.workOrderNature).all()
    
    for nature, count in nature_stats:
        is_quality = "⚠️ " if nature == '质量问题' else "✅"
        print(f"   {is_quality} {nature}: {count}个")
    
    # 计算非质量问题比例
    if workorder_total > 0:
        rate = round((non_quality / workorder_total) * 100, 1)
        print(f"\n📊 工单问题比例: {rate}% ({non_quality}/{workorder_total})")
        print(f"   （表示{rate}%的工单是非质量问题工单）")
    else:
        print(f"\n📊 工单问题比例: 0.0% (无数据)")
    
    print("\n" + "="*80)
    print("\n【3. 验证总结】")
    print("-"*80)
    
    if completed_total > 0:
        drawing_rate = round((compliant_count / completed_total) * 100, 1)
        print(f"✅ 图纸符合率: {drawing_rate}%")
        if other_count > 0:
            print(f"   ⚠️  警告: 发现{other_count}个conclusion字段值不是'符合'或'不符合'")
    else:
        print(f"⚠️  图纸符合率: 无数据")
    
    if workorder_total > 0:
        issue_rate = round((non_quality / workorder_total) * 100, 1)
        print(f"✅ 工单问题比例: {issue_rate}%")
    else:
        print(f"⚠️  工单问题比例: 无数据")
    
    print("\n" + "="*80)
    print("测试完成！")
    print("="*80)
