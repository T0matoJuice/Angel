#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查看 drawing_part 表结构
"""
import sys
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

from app import app
from modules.auth import db

with app.app_context():
    # 查看表结构
    result = db.session.execute(db.text("DESCRIBE drawing_part"))
    print("drawing_part 表结构:")
    print("-" * 80)
    for row in result:
        print(f"字段名: {row[0]}, 类型: {row[1]}, 允许NULL: {row[2]}, 键: {row[3]}, 默认值: {row[4]}")
    print("-" * 80)
    
    # 查看表中数据样例
    result = db.session.execute(db.text("SELECT * FROM drawing_part LIMIT 3"))
    print("\n数据样例:")
    print("-" * 80)
    for row in result:
        print(row)
