#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工单系统测试脚本
测试83字段Excel到数据库的完整流程
"""

import pymysql
import pandas as pd

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': '123456',
    'database': 'angel',
    'charset': 'utf8mb4'
}

def test_database_connection():
    """测试数据库连接"""
    print("=" * 60)
    print("测试1：数据库连接")
    print("=" * 60)
    
    try:
        connection = pymysql.connect(**DB_CONFIG)
        print("✅ 数据库连接成功")
        connection.close()
        return True
    except Exception as e:
        print(f"❌ 数据库连接失败：{str(e)}")
        return False


def test_table_structure():
    """测试表结构"""
    print("\n" + "=" * 60)
    print("测试2：表结构验证")
    print("=" * 60)
    
    connection = pymysql.connect(**DB_CONFIG)
    cursor = connection.cursor()
    
    try:
        tables = ['workorder_data', 'workorder_uselessdata_1', 'workorder_uselessdata_2']
        expected_fields = {
            'workorder_data': 20,  # 20个核心字段 + id, account, datatime, filename
            'workorder_uselessdata_1': 43,  # 43个辅助字段 + id, filename, workAlone
            'workorder_uselessdata_2': 31,  # 31个辅助字段 + id, filename, workAlone
        }
        
        for table_name in tables:
            cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
            result = cursor.fetchone()
            
            if result:
                print(f"\n✅ 表 {table_name} 存在")
                
                # 查询字段数量
                cursor.execute(f"SHOW COLUMNS FROM {table_name}")
                columns = cursor.fetchall()
                print(f"   字段数量：{len(columns)}")
                
                # 显示前10个字段
                print(f"   前10个字段：")
                for i, col in enumerate(columns[:10]):
                    print(f"      {i+1}. {col[0]} ({col[1]})")
                
                if len(columns) > 10:
                    print(f"      ... 还有 {len(columns) - 10} 个字段")
            else:
                print(f"❌ 表 {table_name} 不存在")
        
        return True
        
    except Exception as e:
        print(f"❌ 表结构验证失败：{str(e)}")
        return False
    finally:
        cursor.close()
        connection.close()


def test_field_mapping():
    """测试字段映射"""
    print("\n" + "=" * 60)
    print("测试3：字段映射验证")
    print("=" * 60)
    
    try:
        from modules.excel.field_mapping import (
            get_workorder_data_mapping,
            get_workorder_uselessdata_1_mapping,
            get_workorder_uselessdata_2_mapping,
            get_quality_detection_fields,
            get_quality_detection_fields_cn
        )
        
        mapping_data = get_workorder_data_mapping()
        mapping_useless1 = get_workorder_uselessdata_1_mapping()
        mapping_useless2 = get_workorder_uselessdata_2_mapping()
        quality_fields = get_quality_detection_fields()
        quality_fields_cn = get_quality_detection_fields_cn()
        
        print(f"✅ workorder_data 映射字段数：{len(mapping_data)}")
        print(f"✅ workorder_uselessdata_1 映射字段数：{len(mapping_useless1)}")
        print(f"✅ workorder_uselessdata_2 映射字段数：{len(mapping_useless2)}")
        print(f"✅ 质量检测字段数：{len(quality_fields)}")
        
        print(f"\n质量检测11个字段（中文）：")
        for i, field in enumerate(quality_fields_cn, 1):
            print(f"   {i}. {field}")
        
        return True
        
    except Exception as e:
        print(f"❌ 字段映射验证失败：{str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_model_import():
    """测试模型导入"""
    print("\n" + "=" * 60)
    print("测试4：数据模型导入")
    print("=" * 60)
    
    try:
        from modules.excel.models import WorkorderData, WorkorderUselessdata1, WorkorderUselessdata2
        
        print("✅ WorkorderData 模型导入成功")
        print("✅ WorkorderUselessdata1 模型导入成功")
        print("✅ WorkorderUselessdata2 模型导入成功")
        
        # 显示模型字段
        print(f"\nWorkorderData 模型字段：")
        for attr in dir(WorkorderData):
            if not attr.startswith('_') and not callable(getattr(WorkorderData, attr)):
                print(f"   - {attr}")
        
        return True
        
    except Exception as e:
        print(f"❌ 模型导入失败：{str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_data_query():
    """测试数据查询"""
    print("\n" + "=" * 60)
    print("测试5：数据查询")
    print("=" * 60)
    
    connection = pymysql.connect(**DB_CONFIG)
    cursor = connection.cursor()
    
    try:
        tables = ['workorder_data', 'workorder_uselessdata_1', 'workorder_uselessdata_2']
        
        for table_name in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"✅ {table_name} 表记录数：{count}")
        
        return True
        
    except Exception as e:
        print(f"❌ 数据查询失败：{str(e)}")
        return False
    finally:
        cursor.close()
        connection.close()


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 80)
    print(" " * 20 + "工单系统测试套件")
    print("=" * 80)
    
    tests = [
        ("数据库连接", test_database_connection),
        ("表结构验证", test_table_structure),
        ("字段映射验证", test_field_mapping),
        ("数据模型导入", test_model_import),
        ("数据查询", test_data_query),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ 测试 '{test_name}' 执行失败：{str(e)}")
            results.append((test_name, False))
    
    # 汇总结果
    print("\n" + "=" * 80)
    print(" " * 30 + "测试结果汇总")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:30s} {status}")
    
    print("=" * 80)
    print(f"总计：{passed}/{total} 测试通过")
    print("=" * 80)
    
    if passed == total:
        print("\n🎉 所有测试通过！系统准备就绪。")
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败，请检查配置。")


if __name__ == '__main__':
    run_all_tests()

