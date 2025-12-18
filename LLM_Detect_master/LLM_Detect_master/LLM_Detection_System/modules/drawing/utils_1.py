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
    2. 项目目录下的 poppler 文件夹（使用绝对路径定位）
    3. 常见的安装位置（支持Windows和Linux）

    Returns:
        str or None: Poppler bin 目录路径，如果未找到则返回 None
    """
    import platform
    from pathlib import Path
    
    # 1. 检查系统 PATH 中是否有 pdftoppm
    if shutil.which('pdftoppm'):
        print("✅ 在系统 PATH 中找到 Poppler")
        return None  # pdf2image 会自动使用 PATH 中的 poppler

    # 2. 根据操作系统确定可执行文件名
    is_windows = platform.system() == 'Windows'
    pdftoppm_exe = 'pdftoppm.exe' if is_windows else 'pdftoppm'
    
    # 3. 计算项目根目录（使用当前文件位置计算，不依赖工作目录）
    # 当前文件: LLM_Detection_System/modules/drawing/utils_1.py
    # 项目根目录: LLM_Detect_master/LLM_Detect_master/
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent.parent  # 向上4级
    
    # 4. 构建可能的 Poppler 路径（优先使用基于项目根目录的绝对路径）
    possible_paths = []
    
    if is_windows:
        # Windows路径 - 优先使用项目根目录下的poppler
        possible_paths = [
            project_root / "poppler" / "Library" / "bin",  # 项目根目录的poppler（推荐）
            Path("poppler") / "Library" / "bin",  # 当前工作目录
            Path("..") / "poppler" / "Library" / "bin",  # 工作目录上一级
            Path(r"C:\Program Files\poppler\Library\bin"),
            Path(r"C:\poppler\Library\bin"),
            Path(r"C:\Program Files (x86)\poppler\Library\bin"),
        ]
    else:
        # Linux路径
        possible_paths = [
            project_root / "poppler" / "bin",
            project_root / "poppler" / "Library" / "bin",
            Path("/usr/bin"),
            Path("/usr/local/bin"),
            Path("poppler") / "bin",
            Path("../poppler") / "bin",
        ]

    for path in possible_paths:
        # 检查路径是否存在且包含 pdftoppm
        pdftoppm_path = path / pdftoppm_exe
        if pdftoppm_path.exists():
            # 转换为绝对路径字符串
            abs_path = str(path.resolve())
            print(f"✅ 找到 Poppler: {abs_path}")
            return abs_path

    print("⚠️  未找到 Poppler，将依赖系统PATH")
    print("💡 提示：确保Poppler已安装并在系统PATH中，或配置到项目目录")
    return None

def convert_pdf_to_image(pdf_path, page_num=0, max_width=None):
    """PDF文件转图片预览功能

    使用Poppler工具将PDF文件转换为PNG图片，用于前端预览显示

    Args:
        pdf_path (str): PDF文件路径
        page_num (int): 要转换的页码，默认为第0页
        max_width (int): 图片最大宽度，None表示不限制（推荐）

    Returns:
        str: base64编码的图片数据URL，失败时返回None
    """
    try:
        # 自动检测 Poppler 路径
        poppler_path = get_poppler_path()

        # 使用poppler工具转换PDF为图片（使用高DPI获得清晰图片）
        if poppler_path:
            # 使用指定路径
            images = convert_from_path(
                pdf_path,
                first_page=page_num+1,  # 指定页码（poppler从1开始计数）
                last_page=page_num+1,
                dpi=300,  # 使用300 DPI（印刷级别）获得高清图片
                poppler_path=poppler_path
            )
        else:
            # 使用系统 PATH 中的 poppler（或抛出异常）
            images = convert_from_path(
                pdf_path,
                first_page=page_num+1,
                last_page=page_num+1,
                dpi=300
            )

        if images:
            image = images[0]
            # 只在指定max_width时才限制图片宽度
            if max_width and image.width > max_width:
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
