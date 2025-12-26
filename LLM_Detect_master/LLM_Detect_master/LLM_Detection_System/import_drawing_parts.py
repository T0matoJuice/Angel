#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将JSON文件中的零件数据导入到 drawing_part 表

用法：
    python import_drawing_parts.py <json_file_path>
    
示例：
    python import_drawing_parts.py C:\\Users\\root\\Desktop\\1.txt
"""
import sys
import json
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# 加载环境变量
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

from app import app
from modules.auth import db


def parse_drawing_numbers(drawing_number_str):
    """
    解析图号字符串，支持逗号分隔的多个图号
    
    Args:
        drawing_number_str: 图号字符串，可能包含逗号分隔的多个图号
        
    Returns:
        list: 去重后的图号列表
    """
    if not drawing_number_str or drawing_number_str.strip() == "":
        return []
    
    # 按逗号分割并去除空白
    numbers = [num.strip() for num in drawing_number_str.split(',')]
    # 去重并保持顺序
    seen = set()
    unique_numbers = []
    for num in numbers:
        if num and num not in seen:
            seen.add(num)
            unique_numbers.append(num)
    
    return unique_numbers


def import_parts_from_json(json_file_path):
    """
    从JSON文件导入零件数据到数据库
    
    Args:
        json_file_path: JSON文件路径
        
    Returns:
        dict: 导入统计信息
    """
    # 读取JSON文件
    try:
        # 尝试多种编码
        encodings = ['utf-8', 'utf-8-sig', 'gbk', 'gb2312', 'gb18030']
        content = None
        
        for encoding in encodings:
            try:
                with open(json_file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                print(f"✅ 使用编码 {encoding} 读取文件成功")
                break
            except UnicodeDecodeError:
                continue
        
        if content is None:
            print(f"❌ 无法使用任何编码读取文件")
            return None
            
        # 解析JSON，使用strict=False来允许控制字符
        json_data = json.loads(content, strict=False)
        
        # 提取data数组
        if isinstance(json_data, dict) and 'data' in json_data:
            parts_data = json_data['data']
        elif isinstance(json_data, list):
            parts_data = json_data
        else:
            print(f"❌ JSON格式错误：无法找到数据数组")
            return None
            
    except FileNotFoundError:
        print(f"❌ 文件不存在: {json_file_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ JSON解析错误: {e}")
        return None
    except Exception as e:
        print(f"❌ 读取文件错误: {e}")
        return None
    
    # 统计信息
    stats = {
        'total': 0,          # 总记录数
        'skipped': 0,        # 跳过的记录（drawingNumber为空）
        'inserted': 0,       # 新插入的记录
        'updated': 0,        # 更新的记录
        'errors': 0          # 错误数
    }
    
    with app.app_context():
        for part in parts_data:
            stats['total'] += 1
            
            # 提取字段，处理None值
            part_number = (part.get('partNumber') or '').strip()
            part_name = (part.get('partName') or '').strip()
            part_code = (part.get('partCode') or '').strip()
            part_clf = (part.get('partClf') or '').strip()
            drawing_number_str = (part.get('drawingNumber') or '').strip()
            
            # 解析图号
            drawing_numbers = parse_drawing_numbers(drawing_number_str)
            
            # 如果图号为空，跳过
            if not drawing_numbers:
                stats['skipped'] += 1
                print(f"⏭️  跳过（无图号）: {part_number} - {part_name}")
                continue
            
            # 处理每个图号
            for drawing_number in drawing_numbers:
                try:
                    # 检查数据库中是否存在该图号的记录
                    existing = db.session.execute(
                        db.text("""
                            SELECT * FROM drawing_part 
                            WHERE engineering_drawing_id = :drawing_number
                        """),
                        {'drawing_number': drawing_number}
                    ).fetchone()
                    
                    if existing:
                        # 更新现有记录
                        db.session.execute(
                            db.text("""
                                UPDATE drawing_part 
                                SET partNumber = :part_number,
                                    partName = :part_name,
                                    partCode = :part_code,
                                    partClf = :part_clf
                                WHERE engineering_drawing_id = :drawing_number
                            """),
                            {
                                'part_number': part_number,
                                'part_name': part_name,
                                'part_code': part_code,
                                'part_clf': part_clf,
                                'drawing_number': drawing_number
                            }
                        )
                        stats['updated'] += 1
                        print(f"🔄 更新: {drawing_number} - {part_number} - {part_name}")
                    else:
                        # 插入新记录
                        db.session.execute(
                            db.text("""
                                INSERT INTO drawing_part 
                                (engineering_drawing_id, partNumber, partName, partCode, partClf)
                                VALUES (:drawing_number, :part_number, :part_name, :part_code, :part_clf)
                            """),
                            {
                                'drawing_number': drawing_number,
                                'part_number': part_number,
                                'part_name': part_name,
                                'part_code': part_code,
                                'part_clf': part_clf
                            }
                        )
                        stats['inserted'] += 1
                        print(f"✅ 插入: {drawing_number} - {part_number} - {part_name}")
                    
                    # 提交事务
                    db.session.commit()
                    
                except Exception as e:
                    stats['errors'] += 1
                    print(f"❌ 处理错误 ({drawing_number}): {e}")
                    db.session.rollback()
    
    return stats


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python import_drawing_parts.py <json_file_path>")
        print("示例: python import_drawing_parts.py C:\\Users\\root\\Desktop\\1.txt")
        sys.exit(1)
    
    json_file_path = sys.argv[1]
    
    print("=" * 80)
    print("📥 开始导入零件数据到 drawing_part 表")
    print("=" * 80)
    print(f"📁 文件路径: {json_file_path}")
    print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # 导入数据
    stats = import_parts_from_json(json_file_path)
    
    if stats:
        print("=" * 80)
        print("📊 导入统计")
        print("=" * 80)
        print(f"📝 总记录数: {stats['total']}")
        print(f"⏭️  跳过记录: {stats['skipped']} (图号为空)")
        print(f"✅ 新插入: {stats['inserted']}")
        print(f"🔄 更新记录: {stats['updated']}")
        print(f"❌ 错误数: {stats['errors']}")
        print("=" * 80)
        print(f"⏰ 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        if stats['errors'] == 0:
            print("✅ 导入成功！")
        else:
            print("⚠️  导入完成，但存在错误，请检查日志")
    else:
        print("❌ 导入失败")


if __name__ == '__main__':
    main()
