#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断脚本：检查数据库中的历史记录
"""

import pymysql
from datetime import datetime, timedelta

# 数据库连接信息
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "123456",
    "database": "angel",
    "charset": "utf8mb4"
}

def check_recent_uploads():
    """检查最近24小时的上传记录"""
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    # 获取今天的日期
    today = datetime.now().strftime('%Y-%m-%d')
    
    # 查询今天的所有上传记录（按文件名分组）
    sql = """
        SELECT 
            account,
            filename,
            datatime,
            COUNT(*) as row_count,
            MIN(id) as first_id,
            MAX(id) as last_id
        FROM workorder_data
        WHERE datatime >= %s
        GROUP BY account, filename, datatime
        ORDER BY datatime DESC
    """
    
    cursor.execute(sql, (today,))
    results = cursor.fetchall()
    
    print("=" * 80)
    print(f"📊 今天（{today}）的上传记录：")
    print("=" * 80)
    
    if not results:
        print("❌ 没有找到今天的上传记录")
    else:
        print(f"✅ 找到 {len(results)} 条上传记录\n")
        
        for i, record in enumerate(results, 1):
            print(f"记录 #{i}:")
            print(f"  账号 (account): {record['account']}")
            print(f"  文件名 (filename): {record['filename']}")
            print(f"  上传时间 (datatime): {record['datatime']}")
            print(f"  工单数量: {record['row_count']} 条")
            print(f"  ID范围: {record['first_id']} - {record['last_id']}")
            print()
    
    # 查询所有不同的账号
    cursor.execute("SELECT DISTINCT account FROM workorder_data WHERE account IS NOT NULL ORDER BY account")
    accounts = cursor.fetchall()
    
    print("=" * 80)
    print("👥 数据库中的所有账号：")
    print("=" * 80)
    for acc in accounts:
        print(f"  - {acc['account']}")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    try:
        check_recent_uploads()
    except Exception as e:
        print(f"❌ 执行出错: {e}")
        import traceback
        traceback.print_exc()
