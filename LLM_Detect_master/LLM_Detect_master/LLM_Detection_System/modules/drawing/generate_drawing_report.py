#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
工程图纸检测报告生成工具（完整版）
功能：
1. 从drawing_data表读取detailed_report字段并解析
2. 将解析结果写入drawing_detection表
3. 生成PDF检测报告并合并到原始PDF
"""

import re
import os
from typing import Dict, Optional
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER
from PyPDF2 import PdfReader, PdfWriter
from modules.auth import db

# 注册中文字体（跨平台支持）
import platform

FONT_NAME = 'Helvetica'
FONT_BOLD = 'Helvetica-Bold'

try:
    system = platform.system()
    
    if system == 'Windows':
        # Windows 系统字体
        pdfmetrics.registerFont(TTFont('SimSun', 'C:/Windows/Fonts/simsun.ttc'))
        pdfmetrics.registerFont(TTFont('SimHei', 'C:/Windows/Fonts/simhei.ttf'))
        FONT_NAME = 'SimSun'
        FONT_BOLD = 'SimHei'
        print("✓ 已加载 Windows 中文字体")
    
    elif system == 'Linux':
        # Linux 系统字体(优先中文字体)
        linux_fonts = [
            ('/usr/share/fonts/truetype/wqy/wqy-microhei.ttc', 'WQYMicroHei'),  # 文泉驿微米黑
            ('/usr/share/fonts/wqy-zenhei/wqy-zenhei.ttc', 'WQYZenHei'),        # 文泉驿正黑
            ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 'DejaVuSans'),  # DejaVu(仅英文)
        ]
        
        for font_path, font_name in linux_fonts:
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont(font_name, font_path))
                FONT_NAME = font_name
                FONT_BOLD = font_name
                
                if 'DejaVu' in font_name:
                    print(f"⚠️  已加载 Linux 字体: {font_name} (不支持中文,仅显示英文)")
                    print("   建议安装中文字体: sudo apt-get install fonts-wqy-microhei")
                else:
                    print(f"✓ 已加载 Linux 中文字体: {font_name}")
                break
        else:
            print("⚠️  警告: 未找到任何可用字体，中文可能无法正常显示")
            print("   建议安装: sudo apt-get install fonts-wqy-microhei")
    
    else:
        print(f"⚠️  警告: 未识别的操作系统 ({system})，使用默认字体")

except Exception as e:
    print(f"⚠️  警告: 无法加载中文字体 ({str(e)})，中文可能无法正常显示")
    FONT_NAME = 'Helvetica'
    FONT_BOLD = 'Helvetica-Bold'


# ========== 第一部分：解析 detailed_report 字段 ==========

def extract_field_value(text: str, field_name: str) -> str:
    """从文本中提取指定字段的值"""
    pattern = rf'-\s*{re.escape(field_name)}[:：]\s*(.+?)(?=\n-|\n\*\*|$)'
    match = re.search(pattern, text, re.DOTALL)
    
    if match:
        value = match.group(1).strip()
        value = re.sub(r'\s+', ' ', value)
        return value
    
    return ""


def parse_detection_result(result_block: str, index: int) -> Dict[str, str]:
    """解析单个检测结果块"""
    data = {}
    
    data[f'content_{index}'] = extract_field_value(result_block, '发现内容')
    data[f'result_{index}'] = extract_field_value(result_block, '检测结果')
    data[f'position_{index}'] = extract_field_value(result_block, '位置描述')
    data[f'reason_{index}'] = extract_field_value(result_block, '符合/不符合原因')
    data[f'suggest_{index}'] = extract_field_value(result_block, '修改建议')
    
    return data


def parse_detailed_report(detailed_report: str) -> Dict[str, str]:
    """解析完整的detailed_report字段"""
    all_data = {}
    
    pattern = r'第(\d+)条检测结果[^\n]*\n(.*?)(?=第\d+条检测结果|检测统计：|$)'
    matches = re.findall(pattern, detailed_report, re.DOTALL)
    
    print(f"找到 {len(matches)} 条检测结果")
    
    for match in matches:
        index = int(match[0])
        result_block = match[1]
        
        if 1 <= index <= 12:
            result_data = parse_detection_result(result_block, index)
            all_data.update(result_data)
            print(f"已解析第 {index} 条检测结果")
    
    return all_data


def update_drawing_detection(engineering_drawing_id: str, data: Dict[str, str]) -> bool:
    """将解析的数据更新到drawing_detection表"""
    try:
        # 使用原生SQL查询检查记录是否存在
        sql_check = "SELECT id FROM drawing_detection WHERE engineering_drawing_id = :id"
        result = db.session.execute(db.text(sql_check), {"id": engineering_drawing_id})
        existing = result.fetchone()
        
        if existing:
            # 更新记录
            set_clauses = []
            params = {"id": engineering_drawing_id}
            
            for field, value in data.items():
                if value:
                    set_clauses.append(f"{field} = :{field}")
                    params[field] = value
            
            if set_clauses:
                sql_update = f"UPDATE drawing_detection SET {', '.join(set_clauses)} WHERE engineering_drawing_id = :id"
                db.session.execute(db.text(sql_update), params)
                db.session.commit()
                print(f"成功更新 engineering_drawing_id={engineering_drawing_id} 的记录")
                return True
            else:
                print("没有数据需要更新")
                return False
        else:
            # 插入新记录
            fields = ['engineering_drawing_id'] + list(data.keys())
            placeholders = [f":{field}" for field in fields]
            params = {"engineering_drawing_id": engineering_drawing_id}
            params.update(data)
            
            sql_insert = f"INSERT INTO drawing_detection ({', '.join(fields)}) VALUES ({', '.join(placeholders)})"
            db.session.execute(db.text(sql_insert), params)
            db.session.commit()
            print(f"成功插入 engineering_drawing_id={engineering_drawing_id} 的新记录")
            return True
            
    except Exception as e:
        print(f"数据库操作错误: {e}")
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return False


# ========== 第二部分：生成PDF报告 ==========

def fetch_detection_data(engineering_drawing_id: str) -> Optional[Dict]:
    """从数据库获取检测数据"""
    try:
        query = """
            SELECT 
                d1.engineering_drawing_id,
                d1.original_filename,
                d1.version,
                d1.created_at,
                d1.completed_at,
                d1.conclusion,
                d1.checker_name,
                d2.*
            FROM drawing_data d1
            LEFT JOIN drawing_detection d2 ON d1.engineering_drawing_id = d2.engineering_drawing_id
            WHERE d1.engineering_drawing_id = :id
        """
        
        result = db.session.execute(db.text(query), {"id": engineering_drawing_id})
        row = result.fetchone()
        
        if row:
            # 将结果转换为字典
            columns = result.keys()
            return dict(zip(columns, row))
        
        return None
        
    except Exception as e:
        print(f"数据库查询错误: {e}")
        return None


def extract_drawing_info(engineering_drawing_id: str, filename: str):
    """从数据库字段中提取图号和名称"""
    drawing_number = engineering_drawing_id if engineering_drawing_id else "未知"
    
    drawing_name = filename
    if drawing_name and drawing_name.endswith('.pdf'):
        drawing_name = drawing_name[:-4]
    
    return drawing_number, drawing_name


def create_header_table(data: dict):
    """创建报告头部信息表格"""
    drawing_number, drawing_name = extract_drawing_info(
        data['engineering_drawing_id'], 
        data['original_filename']
    )
    
    upload_time = data['created_at'] if data['created_at'] else ''
    detection_time = data['completed_at'] if data['completed_at'] else ''
    
    detection_date = detection_time.split(' ')[0] if ' ' in detection_time else detection_time
    
    header_data = [
        ['试验编码时间日期：', f'{detection_date}'],
        ['1. 图纸基本信息', ''],
        ['图号：', drawing_number],
        ['名称：', drawing_name],
        ['版本：', data['version'] if data['version'] else '无'],
        ['上传时间：', upload_time],
        ['检测时间：', detection_time],
    ]
    
    header_table = Table(header_data, colWidths=[4*cm, 14*cm])
    header_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), FONT_NAME, 10),
        ('FONT', (0, 1), (0, 1), FONT_BOLD, 11),
        ('TEXTCOLOR', (0, 0), (0, 0), colors.grey),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('SPAN', (0, 1), (1, 1)),
    ]))
    
    return header_table


def create_summary_table(data: dict):
    """创建检测摘要表格"""
    conform_count = 0
    non_conform_count = 0
    
    for i in range(1, 13):
        result_field = f'result_{i}'
        if result_field in data and data[result_field]:
            result = str(data[result_field]).strip()
            if '符合' in result and '不符合' not in result:
                conform_count += 1
            elif '不符合' in result:
                non_conform_count += 1
    
    conclusion = data['conclusion'] if data['conclusion'] else '基本不符合'
    
    summary_data = [
        ['2. 检测摘要', ''],
        ['检测结论：', conclusion],
        ['符合项目数：', str(conform_count)],
        ['不符合项目数：', str(non_conform_count)],
    ]
    
    summary_table = Table(summary_data, colWidths=[4*cm, 14*cm])
    summary_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), FONT_NAME, 10),
        ('FONT', (0, 0), (0, 0), FONT_BOLD, 11),
        ('FONT', (0, 1), (0, 1), FONT_BOLD, 10),
        ('TEXTCOLOR', (1, 1), (1, 1), colors.red if '不符合' in conclusion else colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('SPAN', (0, 0), (1, 0)),
    ]))
    
    return summary_table


def create_detail_table(data: dict):
    """创建详细检测结果表格"""
    detail_data = [
        ['检测项目', '检测结果', '发现内容', '位置描述', '修改建议']
    ]
    
    for i in range(1, 13):
        content = str(data.get(f'content_{i}', '') or '')
        result = str(data.get(f'result_{i}', '') or '')
        position = str(data.get(f'position_{i}', '') or '')
        reason = str(data.get(f'reason_{i}', '') or '')
        suggest = str(data.get(f'suggest_{i}', '') or '')
        
        project = ''
        if reason:
            project = reason[:40] + '...' if len(reason) > 40 else reason
        elif content:
            project = content[:40] + '...' if len(content) > 40 else content
        
        suggestion = suggest if suggest else '无'
        result_text = result if result else ''
        is_non_conform = '不符合' in result_text
        
        detail_data.append([
            Paragraph(project, ParagraphStyle(
                name='Normal',
                fontName=FONT_NAME,
                fontSize=8,
                leading=11,
                wordWrap='CJK'
            )),
            Paragraph(result_text, ParagraphStyle(
                name='Result',
                fontName=FONT_BOLD if is_non_conform else FONT_NAME,
                fontSize=9,
                leading=11,
                alignment=TA_CENTER,
                textColor=colors.red if is_non_conform else colors.black
            )),
            Paragraph(content if content else '无', ParagraphStyle(
                name='Content',
                fontName=FONT_NAME,
                fontSize=8,
                leading=10,
                wordWrap='CJK'
            )),
            Paragraph(position if position else '无', ParagraphStyle(
                name='Position',
                fontName=FONT_NAME,
                fontSize=8,
                leading=10,
                wordWrap='CJK'
            )),
            Paragraph(suggestion, ParagraphStyle(
                name='Suggestion',
                fontName=FONT_NAME,
                fontSize=8,
                leading=10,
                wordWrap='CJK'
            ))
        ])
    
    detail_table = Table(detail_data, colWidths=[3.2*cm, 1.8*cm, 4.8*cm, 3*cm, 4.7*cm])
    
    table_style = [
        ('FONT', (0, 0), (-1, 0), FONT_BOLD, 9),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E8E8E8')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('ALIGN', (1, 1), (1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]
    
    for i in range(1, 13):
        result = str(data.get(f'result_{i}', '') or '')
        if '不符合' in result:
            table_style.append(
                ('BACKGROUND', (0, i), (-1, i), colors.HexColor('#FFF8DC'))
            )
    
    detail_table.setStyle(TableStyle(table_style))
    
    return detail_table


def merge_pdfs(original_pdf_path: str, new_pdf_path: str, output_path: str):
    """合并两个PDF文件"""
    try:
        pdf_writer = PdfWriter()
        
        if os.path.exists(original_pdf_path):
            print(f"读取原始PDF: {original_pdf_path}")
            original_pdf = PdfReader(original_pdf_path)
            for page in original_pdf.pages:
                pdf_writer.add_page(page)
            print(f"已添加原始PDF的 {len(original_pdf.pages)} 页")
        else:
            print(f"警告: 原始PDF不存在: {original_pdf_path}")
        
        print(f"读取报告PDF: {new_pdf_path}")
        report_pdf = PdfReader(new_pdf_path)
        for page in report_pdf.pages:
            pdf_writer.add_page(page)
        print(f"已添加报告PDF的 {len(report_pdf.pages)} 页")
        
        with open(output_path, 'wb') as output_file:
            pdf_writer.write(output_file)
        
        print(f"✓ PDF合并成功: {output_path}")
        
        if os.path.exists(new_pdf_path) and new_pdf_path != output_path:
            os.remove(new_pdf_path)
            print(f"已删除临时文件: {new_pdf_path}")
        
        return True
        
    except Exception as e:
        print(f"✗ PDF合并失败: {e}")
        import traceback
        traceback.print_exc()
        return False


# ========== 主函数：整合所有功能 ==========

def process_drawing_report(engineering_drawing_id: str, output_path: str) -> bool:
    """
    处理工程图纸检测报告（完整流程）
    
    Args:
        engineering_drawing_id: 工程图纸ID
        output_path: 输出PDF文件路径（原始PDF路径）
        
    Returns:
        成功返回True，失败返回False
    """
    print("=" * 80)
    print("工程图纸检测报告处理工具")
    print("=" * 80)
    print(f"工程图纸ID: {engineering_drawing_id}")
    print(f"输出路径: {output_path}")
    print()
    
    # 步骤1: 读取并解析 detailed_report
    print("步骤 1/3: 解析 detailed_report 字段")
    print("-" * 80)
    
    try:
        sql = "SELECT detailed_report FROM drawing_data WHERE engineering_drawing_id = :id"
        result = db.session.execute(db.text(sql), {"id": engineering_drawing_id})
        row = result.fetchone()
        
        if not row or not row[0]:
            print(f"✗ 未找到 engineering_drawing_id={engineering_drawing_id} 的记录或detailed_report为空")
            return False
        
        detailed_report = row[0]
        print(f"✓ 成功读取detailed_report，长度: {len(detailed_report)} 字符")
        print()
        
        # 解析detailed_report
        parsed_data = parse_detailed_report(detailed_report)
        print(f"✓ 解析完成，共提取 {len(parsed_data)} 个字段")
        print()
        
    except Exception as e:
        print(f"✗ 解析失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 步骤2: 写入 drawing_detection 表
    print("步骤 2/3: 写入 drawing_detection 表")
    print("-" * 80)
    
    if not update_drawing_detection(engineering_drawing_id, parsed_data):
        print("✗ 数据写入失败")
        return False
    
    print("✓ 数据写入成功")
    print()
    
    # 步骤3: 生成PDF报告
    print("步骤 3/3: 生成PDF报告")
    print("-" * 80)
    
    try:
        # 获取完整数据
        data = fetch_detection_data(engineering_drawing_id)
        
        if not data:
            print("✗ 未能获取检测数据")
            return False
        
        print(f"✓ 成功获取数据，图纸文件: {data['original_filename']}")
        
        # 创建临时PDF文件
        temp_report_path = output_path.replace('.pdf', '_report_temp.pdf')
        
        # 创建PDF文档
        doc = SimpleDocTemplate(
            temp_report_path,
            pagesize=A4,
            rightMargin=1.5*cm,
            leftMargin=1.5*cm,
            topMargin=1.5*cm,
            bottomMargin=1.5*cm
        )
        
        # 构建文档内容
        story = []
        
        # 标题
        title_style = ParagraphStyle(
            name='Title',
            fontName=FONT_BOLD,
            fontSize=18,
            leading=22,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#CC0000'),
            spaceAfter=15
        )
        
        conclusion = data['conclusion'] if data['conclusion'] else '基本不符合'
        title = Paragraph(conclusion, title_style)
        story.append(title)
        story.append(Spacer(1, 0.3*cm))
        
        # 头部信息表格
        header_table = create_header_table(data)
        story.append(header_table)
        story.append(Spacer(1, 0.4*cm))
        
        # 检测摘要表格
        summary_table = create_summary_table(data)
        story.append(summary_table)
        story.append(Spacer(1, 0.4*cm))
        
        # 详细检测结果
        detail_title_style = ParagraphStyle(
            name='DetailTitle',
            fontName=FONT_BOLD,
            fontSize=11,
            leading=14,
            spaceAfter=10
        )
        detail_title = Paragraph('3. 详细检测结果', detail_title_style)
        story.append(detail_title)
        
        detail_table = create_detail_table(data)
        story.append(detail_table)
        story.append(Spacer(1, 0.4*cm))
        
        # 总结评估
        eval_title = Paragraph('4. 总结评估', detail_title_style)
        story.append(eval_title)
        
        # 统计符合与不符合的条数
        conform_count = 0
        non_conform_count = 0
        for i in range(1, 13):
            result_field = f'result_{i}'
            if result_field in data and data[result_field]:
                result = str(data[result_field]).strip()
                if '符合' in result and '不符合' not in result:
                    conform_count += 1
                elif '不符合' in result:
                    non_conform_count += 1
        
        conclusion = data['conclusion']
        eval_text = f'本次检测共检测12个项目，其中符合项目{conform_count}项，不符合项目{non_conform_count}项。最终判定结果为：{conclusion}。'
        
        eval_style = ParagraphStyle(
            name='Eval',
            fontName=FONT_NAME,
            fontSize=10,
            leading=14,
            textColor=colors.grey,
            wordWrap='CJK'
        )
        eval_para = Paragraph(eval_text, eval_style)
        story.append(eval_para)
        
        # 生成PDF
        doc.build(story)
        print(f"✓ 报告PDF生成成功: {temp_report_path}")
        
        # 备份原始PDF
        if os.path.exists(output_path):
            backup_path = output_path.replace('.pdf', '_backup.pdf')
            if not os.path.exists(backup_path):
                import shutil
                shutil.copy2(output_path, backup_path)
                print(f"✓ 已备份原始PDF: {backup_path}")
        
        # 合并PDF
        success = merge_pdfs(output_path, temp_report_path, output_path)
        
        if success:
            print()
            print("=" * 80)
            print("✓ 所有步骤完成！检测报告已生成")
            print("=" * 80)
            return True
        else:
            return False
        
    except Exception as e:
        print(f"✗ PDF生成失败: {e}")
        import traceback
        traceback.print_exc()
        return False

