#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
制图检测工具函数模块 - 代码
"""

import os
import base64
import shutil
from pdf2image import convert_from_path
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

def allowed_file(filename):
    """检查文件是否为PDF格式 - 函数"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'pdf'

def get_poppler_path():
    """自动检测 Poppler 路径

    按优先级尝试以下路径：
    1. 系统 PATH 环境变量（如果 pdftoppm 可执行）
    2. 项目目录下的 poppler 文件夹
    3. 常见的 Windows 安装位置

    Returns:
        str or None: Poppler bin 目录路径，如果未找到则返回 None
    """
    # 1. 检查系统 PATH 中是否有 pdftoppm
    if shutil.which('pdftoppm'):
        print("✅ 在系统 PATH 中找到 Poppler")
        return None  # pdf2image 会自动使用 PATH 中的 poppler

    # 2. 检查项目目录下的 poppler 文件夹
    possible_paths = [
        # 项目根目录下的 poppler
        r"poppler\Library\bin",
        r"poppler\bin",
        # 常见的 Windows 安装位置
        r"C:\Program Files\poppler\Library\bin",
        r"C:\poppler\Library\bin",
        r"C:\Program Files (x86)\poppler\Library\bin",
        # 旧的硬编码路径（向后兼容）
        r"poppler\poppler\poppler-25.07.0\Library\bin",
    ]

    for path in possible_paths:
        # 检查路径是否存在且包含 pdftoppm.exe
        pdftoppm_path = os.path.join(path, 'pdftoppm.exe')
        if os.path.exists(pdftoppm_path):
            print(f"✅ 找到 Poppler: {path}")
            return path

    print("⚠️  未找到 Poppler，PDF 预览将使用占位符")
    print("💡 提示：请参考 'Poppler安装配置指南.md' 安装 Poppler")
    return None

def convert_pdf_to_image(pdf_path, page_num=0, max_width=800):
    """PDF文件转图片预览功能

    使用Poppler工具将PDF文件转换为PNG图片，用于前端预览显示

    Args:
        pdf_path (str): PDF文件路径
        page_num (int): 要转换的页码，默认为第0页
        max_width (int): 图片最大宽度，默认800像素

    Returns:
        str: base64编码的图片数据URL，失败时返回None
    """
    try:
        # 自动检测 Poppler 路径
        poppler_path = get_poppler_path()

        # 使用poppler工具转换PDF为图片
        if poppler_path:
            # 使用指定路径
            images = convert_from_path(
                pdf_path,
                first_page=page_num+1,  # 指定页码（poppler从1开始计数）
                last_page=page_num+1,
                dpi=150,  # 图片清晰度设置
                poppler_path=poppler_path
            )
        else:
            # 使用系统 PATH 中的 poppler（或抛出异常）
            images = convert_from_path(
                pdf_path,
                first_page=page_num+1,
                last_page=page_num+1,
                dpi=150
            )

        if images:
            image = images[0]
            # 限制图片宽度，保持比例
            if image.width > max_width:
                ratio = max_width / image.width
                new_height = int(image.height * ratio)
                image = image.resize((max_width, new_height), Image.Resampling.LANCZOS)

            # 转换为base64格式返回给前端
            buffer = BytesIO()
            image.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            return f"data:image/png;base64,{img_str}"

    except Exception as e:
        print(f"❌ PDF预览失败: {e}")
        print(f"📄 PDF 文件路径: {pdf_path}")
        print(f"💡 提示：请确保已安装 Poppler 工具")

    return None

def create_placeholder_image(filename):
    """创建PDF文件占位符图片

    当PDF转换失败时，生成一个包含文件名的占位符图片用于前端显示

    Args:
        filename (str): PDF文件名

    Returns:
        str: base64编码的占位符图片数据URL
    """
    try:
        # 创建一个占位符图片画布
        width, height = 600, 800
        img = Image.new('RGB', (width, height), color='#f8f9fa')
        draw = ImageDraw.Draw(img)

        # 绘制边框
        draw.rectangle([20, 20, width-20, height-20], outline='#dee2e6', width=3)

        # 添加PDF图标（简单的矩形表示）
        icon_x, icon_y = width//2 - 40, height//2 - 100
        draw.rectangle([icon_x, icon_y, icon_x+80, icon_y+100], fill='#dc3545', outline='#bd2130', width=2)
        draw.text((icon_x+25, icon_y+35), 'PDF', fill='white', anchor='mm')

        # 添加文件名
        try:
            # 尝试使用默认字体
            font = ImageFont.load_default()
        except:
            font = None

        # 文件名
        text_y = height//2 + 50
        draw.text((width//2, text_y), filename, fill='#495057', anchor='mm', font=font)

        # 提示信息
        draw.text((width//2, text_y + 40), 'PDF文件已上传', fill='#6c757d', anchor='mm', font=font)
        draw.text((width//2, text_y + 70), '需要安装Poppler工具', fill='#6c757d', anchor='mm', font=font)
        draw.text((width//2, text_y + 90), '以显示真实预览', fill='#6c757d', anchor='mm', font=font)

        # 转换为base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()

        return f"data:image/png;base64,{img_str}"

    except Exception as e:
        print(f"创建占位符失败: {e}")
        return None
