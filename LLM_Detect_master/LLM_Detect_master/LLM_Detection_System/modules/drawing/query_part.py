#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查询零件数据接口
从远程PLM系统获取零件列表并保存到本地文件，并自动导入到数据库
支持定时任务：通过APScheduler调度器每天凌晨3:00自动运行
"""

import requests
from requests.auth import HTTPBasicAuth
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import sys
import os
import logging

# 添加项目根目录到系统路径
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

# 加载环境变量
env_path = project_root / '.env'
load_dotenv(env_path)

from modules.auth import db

# 配置日志
logger = logging.getLogger(__name__)


class QueryPartManager:
    """零件数据查询和导入管理器"""
    
    def __init__(self):
        """初始化管理器"""
        self.remote_url = "http://plmtest.angelgroup.com.cn:8090/Windchill/ptc1/aiInterface/listPart"
        self.username = "plmSysInt"
        self.password = "plmSysInt"
    
    def parse_drawing_numbers(self, drawing_number_str):
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


    def import_parts_to_database(self, json_data):
        """
        将JSON数据导入到数据库
        
        Args:
            json_data: JSON格式的零件数据
            
        Returns:
            dict: 导入统计信息
        """
        # 提取data数组
        if isinstance(json_data, dict) and 'data' in json_data:
            parts_data = json_data['data']
        elif isinstance(json_data, list):
            parts_data = json_data
        else:
            logger.error(f"❌ JSON格式错误：无法找到数据数组")
            return None
        
        # 统计信息
        stats = {
            'total': 0,          # 总记录数
            'skipped': 0,        # 跳过的记录（drawingNumber为空）
            'inserted': 0,       # 新插入的记录
            'updated': 0,        # 更新的记录
            'errors': 0          # 错误数
        }
        
        logger.info("\n" + "=" * 80)
        logger.info("📊 开始导入零件数据到 drawing_part 表")
        logger.info("=" * 80)
        
        for part in parts_data:
            stats['total'] += 1
            
            # 提取字段，处理None值
            part_number = (part.get('partNumber') or '').strip()
            part_name = (part.get('partName') or '').strip()
            part_code = (part.get('partCode') or '').strip()
            part_clf = (part.get('partClf') or '').strip()
            drawing_number_str = (part.get('drawingNumber') or '').strip()
            
            # 解析图号
            drawing_numbers = self.parse_drawing_numbers(drawing_number_str)
            
            # 如果图号为空，跳过
            if not drawing_numbers:
                stats['skipped'] += 1
                logger.info(f"⏭️  跳过（无图号）: {part_number} - {part_name}")
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
                        logger.info(f"🔄 更新: {drawing_number} - {part_number} - {part_name}")
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
                        logger.info(f"✅ 插入: {drawing_number} - {part_number} - {part_name}")
                    
                    # 提交事务
                    db.session.commit()
                    
                except Exception as e:
                    stats['errors'] += 1
                    logger.error(f"❌ 处理错误 ({drawing_number}): {e}")
                    db.session.rollback()
        
        return stats


    def query_parts_from_plm(self):
        """
        从PLM系统查询零件数据并保存到文件
        
        Returns:
            tuple: (是否查询成功, JSON数据, 输出文件路径)
        """
        logger.info("=" * 80)
        logger.info("📥 开始查询零件数据")
        logger.info("=" * 80)
        logger.info(f"🔗 接口地址: {self.remote_url}")
        logger.info(f"👤 用户名: {self.username}")
        logger.info(f"⏰ 查询时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 80)
        
        try:
            # 发送GET请求
            logger.info(f"📤 正在发送请求...")
            resp = requests.get(
                self.remote_url,
                auth=HTTPBasicAuth(self.username, self.password),
                timeout=3600  # 1小时超时
            )
            
            # 检查响应状态
            logger.info(f"✅ HTTP状态码: {resp.status_code}")
            
            if resp.status_code != 200:
                logger.error(f"❌ 请求失败: HTTP {resp.status_code}")
                logger.error(f"响应内容: {resp.text}")
                return False, None, None
            
            # 解析JSON响应
            try:
                json_data = resp.json()
                logger.info(f"✅ JSON解析成功")
                
                # 显示数据统计
                if isinstance(json_data, dict):
                    status = json_data.get('status', 'unknown')
                    message = json_data.get('message', 'unknown')
                    data = json_data.get('data', [])
                    
                    logger.info(f"📊 响应状态: {status}")
                    logger.info(f"📊 响应消息: {message}")
                    logger.info(f"📊 零件数量: {len(data) if isinstance(data, list) else 0}")
                
            except json.JSONDecodeError as e:
                logger.error(f"❌ JSON解析失败: {e}")
                logger.error(f"响应内容: {resp.text[:500]}...")  # 只显示前500字符
                return False, None, None
            
            # 保存到文件
            excel_dir = Path(__file__).resolve().parent / "EXCEL"
            excel_dir.mkdir(exist_ok=True)
            
            # 生成文件名（带时间戳）
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = excel_dir / f"parts_data_{timestamp}.txt"
            
            # 写入文件（格式化JSON，便于阅读）
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ 数据已保存到: {output_file}")
            logger.info(f"📁 文件大小: {output_file.stat().st_size} bytes")
            
            # 同时保存一份最新版本（不带时间戳）
            latest_file = excel_dir / "parts_data_latest.txt"
            with open(latest_file, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ 最新数据已保存到: {latest_file}")

            logger.info("=" * 80)
            logger.info("✅ 查询完成！")
            logger.info("=" * 80)
            
            return True, json_data, output_file
        
        except requests.Timeout:
            logger.error(f"❌ 请求超时（超过3600秒）")
            return False, None, None
            
        except requests.RequestException as e:
            logger.error(f"❌ 请求异常: {e}")
            return False, None, None
            
        except Exception as e:
            logger.error(f"❌ 未知错误: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False, None, None


# 为了向后兼容，提供全局函数（用于命令行直接调用）
def main():
    """主函数 - 用于命令行直接执行"""
    from app import app
    
    logger.info("\n" + "=" * 80)
    logger.info("🚀 开始执行零件数据查询和导入任务")
    logger.info("=" * 80)
    
    with app.app_context():
        manager = QueryPartManager()
        
        # 第一步：查询数据
        success, json_data, output_file = manager.query_parts_from_plm()
        
        if not success:
            logger.error("\n❌ 零件数据查询失败！")
            logger.info("💡 提示: 请检查网络连接和接口配置")
            return 1
        
        logger.info("\n✅ 零件数据查询成功！")
        
        # 第二步：导入到数据库
        stats = manager.import_parts_to_database(json_data)
        
        if stats:
            logger.info("=" * 80)
            logger.info("📊 导入统计")
            logger.info("=" * 80)
            logger.info(f"📝 总记录数: {stats['total']}")
            logger.info(f"⏭️  跳过记录: {stats['skipped']} (图号为空)")
            logger.info(f"✅ 新插入: {stats['inserted']}")
            logger.info(f"🔄 更新记录: {stats['updated']}")
            logger.info(f"❌ 错误数: {stats['errors']}")
            logger.info("=" * 80)
            logger.info(f"⏰ 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("=" * 80)
            
            if stats['errors'] == 0:
                logger.info("✅ 数据查询并导入成功！")
                return 0
            else:
                logger.warning("⚠️  数据导入完成，但存在错误，请检查日志")
                return 1
        else:
            logger.error("❌ 数据导入失败！")
            return 1


if __name__ == '__main__':
    # 配置日志（仅用于命令行执行）
    log_dir = project_root / 'logs'
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(
                log_dir / f'query_part_{datetime.now().strftime("%Y%m%d")}.log',
                encoding='utf-8'
            ),
            logging.StreamHandler()
        ]
    )
    
    try:
        sys.exit(main())
    except Exception as e:
        logger.error(f"❌ 程序执行出错: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
