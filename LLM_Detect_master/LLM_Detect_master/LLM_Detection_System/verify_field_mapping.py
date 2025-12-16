#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字段映射验证脚本 - 验证field_mapping.py中的映射是否与实际数据库表结构一致
"""

import pymysql
from modules.excel.field_mapping import (
    EXCEL_TO_WORKORDER_DATA,
    EXCEL_TO_WORKORDER_USELESSDATA_1,
    EXCEL_TO_WORKORDER_USELESSDATA_2
)

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': '123456',
    'database': 'angel',
    'charset': 'utf8mb4'
}

def get_table_columns(cursor, table_name):
    """获取表的所有列名（排除id, filename, workAlone）"""
    cursor.execute(f"DESC {table_name}")
    result = cursor.fetchall()
    columns = [row[0] for row in result if row[0] not in ['id', 'filename', 'workAlone', 'account', 'datatime']]
    return set(columns)

def verify_mapping():
    """验证字段映射"""
    connection = pymysql.connect(**DB_CONFIG)
    cursor = connection.cursor()
    
    try:
        print("=" * 80)
        print("字段映射验证")
        print("=" * 80)
        
        # 获取实际表结构
        workorder_data_cols = get_table_columns(cursor, 'workorder_data')
        workorder_uselessdata_1_cols = get_table_columns(cursor, 'workorder_uselessdata_1')
        workorder_uselessdata_2_cols = get_table_columns(cursor, 'workorder_uselessdata_2')
        
        print(f"\n实际数据库表结构：")
        print(f"  workorder_data: {len(workorder_data_cols)} 个字段")
        print(f"  workorder_uselessdata_1: {len(workorder_uselessdata_1_cols)} 个字段")
        print(f"  workorder_uselessdata_2: {len(workorder_uselessdata_2_cols)} 个字段")
        
        # 获取映射配置
        mapping_data_cols = set(EXCEL_TO_WORKORDER_DATA.values())
        mapping_uselessdata_1_cols = set(EXCEL_TO_WORKORDER_USELESSDATA_1.values())
        mapping_uselessdata_2_cols = set(EXCEL_TO_WORKORDER_USELESSDATA_2.values())
        
        print(f"\n映射配置：")
        print(f"  EXCEL_TO_WORKORDER_DATA: {len(mapping_data_cols)} 个字段")
        print(f"  EXCEL_TO_WORKORDER_USELESSDATA_1: {len(mapping_uselessdata_1_cols)} 个字段")
        print(f"  EXCEL_TO_WORKORDER_USELESSDATA_2: {len(mapping_uselessdata_2_cols)} 个字段")
        
        # 验证workorder_data
        print("\n" + "=" * 80)
        print("验证 workorder_data 表")
        print("=" * 80)
        
        # 映射中有但表中没有的字段
        missing_in_db = mapping_data_cols - workorder_data_cols
        if missing_in_db:
            print(f"❌ 映射中有但表中没有的字段: {missing_in_db}")
        else:
            print("✅ 所有映射字段都存在于表中")
        
        # 表中有但映射中没有的字段
        missing_in_mapping = workorder_data_cols - mapping_data_cols
        if missing_in_mapping:
            print(f"⚠️  表中有但映射中没有的字段: {missing_in_mapping}")
        else:
            print("✅ 表中所有字段都在映射中")
        
        # 验证workorder_uselessdata_1
        print("\n" + "=" * 80)
        print("验证 workorder_uselessdata_1 表")
        print("=" * 80)
        
        missing_in_db = mapping_uselessdata_1_cols - workorder_uselessdata_1_cols
        if missing_in_db:
            print(f"❌ 映射中有但表中没有的字段: {missing_in_db}")
        else:
            print("✅ 所有映射字段都存在于表中")
        
        missing_in_mapping = workorder_uselessdata_1_cols - mapping_uselessdata_1_cols
        if missing_in_mapping:
            print(f"⚠️  表中有但映射中没有的字段: {missing_in_mapping}")
        else:
            print("✅ 表中所有字段都在映射中")
        
        # 验证workorder_uselessdata_2
        print("\n" + "=" * 80)
        print("验证 workorder_uselessdata_2 表")
        print("=" * 80)
        
        missing_in_db = mapping_uselessdata_2_cols - workorder_uselessdata_2_cols
        if missing_in_db:
            print(f"❌ 映射中有但表中没有的字段: {missing_in_db}")
        else:
            print("✅ 所有映射字段都存在于表中")
        
        missing_in_mapping = workorder_uselessdata_2_cols - mapping_uselessdata_2_cols
        if missing_in_mapping:
            print(f"⚠️  表中有但映射中没有的字段: {missing_in_mapping}")
        else:
            print("✅ 表中所有字段都在映射中")
        
        # 检查重复映射
        print("\n" + "=" * 80)
        print("检查重复映射")
        print("=" * 80)
        
        # 检查是否有字段同时映射到多个表
        all_excel_cols = set()
        duplicates = []
        
        for excel_col in EXCEL_TO_WORKORDER_DATA.keys():
            if excel_col in all_excel_cols:
                duplicates.append(excel_col)
            all_excel_cols.add(excel_col)
        
        for excel_col in EXCEL_TO_WORKORDER_USELESSDATA_1.keys():
            if excel_col in all_excel_cols:
                duplicates.append(excel_col)
            all_excel_cols.add(excel_col)
        
        for excel_col in EXCEL_TO_WORKORDER_USELESSDATA_2.keys():
            if excel_col in all_excel_cols:
                duplicates.append(excel_col)
            all_excel_cols.add(excel_col)
        
        if duplicates:
            print(f"⚠️  以下Excel列被映射到多个表: {set(duplicates)}")
            print("   这是正常的，因为某些字段需要同时存储在多个表中")
        else:
            print("✅ 没有重复映射")
        
        # 统计总字段数
        print("\n" + "=" * 80)
        print("总结")
        print("=" * 80)
        print(f"Excel列总数: {len(all_excel_cols)}")
        print(f"数据库字段总数: {len(workorder_data_cols) + len(workorder_uselessdata_1_cols) + len(workorder_uselessdata_2_cols)}")
        
        # 检查关键字段
        print("\n" + "=" * 80)
        print("检查关键字段（产品类型、产品一级分类、产品二级分类、维修类别）")
        print("=" * 80)
        
        key_fields = ['productType', 'productTypeLevelOne', 'productTypeLevelTwo', 'maintenanceCategory']
        
        for field in key_fields:
            in_data = field in workorder_data_cols
            in_uselessdata_1 = field in workorder_uselessdata_1_cols
            in_uselessdata_2 = field in workorder_uselessdata_2_cols
            
            print(f"\n{field}:")
            print(f"  workorder_data: {'✅' if in_data else '❌'}")
            print(f"  workorder_uselessdata_1: {'✅' if in_uselessdata_1 else '❌'}")
            print(f"  workorder_uselessdata_2: {'✅' if in_uselessdata_2 else '❌'}")
            
            if in_data and not in_uselessdata_1 and not in_uselessdata_2:
                print(f"  ✅ 正确：只在workorder_data表中")
            elif not in_data and in_uselessdata_1 and not in_uselessdata_2:
                print(f"  ⚠️  只在workorder_uselessdata_1表中")
            else:
                print(f"  ❌ 错误：字段分布不正确")
        
        print("\n" + "=" * 80)
        print("验证完成")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ 验证失败：{str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        cursor.close()
        connection.close()


if __name__ == '__main__':
    verify_mapping()

