#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图纸类型识别模块
功能：使用模型识别图纸类型并保存结果
"""

import os
import time
from pathlib import Path
from openai import OpenAI
import re
import uuid
from datetime import datetime

# 导入处理 PDF 的依赖库
try:
    from pdf2image import convert_from_path
    from PIL import Image
except ImportError:
    print("❌ 错误: 缺少必要的依赖库。请运行: pip install pdf2image Pillow")

from modules.drawing.utils import get_poppler_path


def identify_drawing_type(filepath):
    """识别图纸类型
    
    Args:
        filepath (str): 待检测的PDF图纸文件路径
        
    Returns:
        str: 识别到的图纸类型，如果识别失败则返回 None
    """
    
    # 获取API密钥和模型配置
    api_key = os.getenv('DRAWING_API_KEY', 'Angel@123456')
    model_name = os.getenv('DRAWING_MODEL_NAME', 'GLM-4.1V-9B-Thinking')
    model_url = os.getenv('DRAWING_BASE_URL', 'http://10.2.32.163:8001/v1')
    
    # 验证配置
    if not api_key:
        error_msg = "未配置 API 密钥..."
        print(f"❌ 错误: {error_msg}")
        return None
    
    # 初始化客户端
    try:
        client = OpenAI(
            api_key=api_key,
            base_url=model_url,
        )
    except Exception as e:
        error_msg = f"初始化 API 客户端失败: {str(e)}"
        print(f"❌ 错误: {error_msg}")
        return None
    
    # 获取prompt文件路径
    base_dir = Path(__file__).resolve().parent.parent.parent
    prompts_dir = base_dir / "prompts" / "drawing_12prompts"
    prompt_file = prompts_dir / "prompt_Identify_drawing_types.txt"
    
    print(f"📁 提示词文件路径: {prompt_file}")
    
    # 检查prompt文件是否存在
    if not prompt_file.exists():
        error_msg = f"找不到提示词文件 - {prompt_file}"
        print(f"❌ 错误: {error_msg}")
        return None
    
    # 获取Poppler路径
    poppler_path = get_poppler_path()
    if poppler_path:
        print(f"🔧 Poppler路径: {poppler_path}")
    else:
        print(f"🔧 Poppler: 使用系统PATH")
    
    # 检查待检测文件是否存在
    if not os.path.exists(filepath):
        error_msg = f"找不到待检测文件 - {filepath}"
        print(f"❌ 错误: {error_msg}")
        return None
    
    # 创建PNG存储目录
    png_dir = Path(__file__).resolve().parent / "PNG"
    png_dir.mkdir(exist_ok=True)
    
    png_file_path = None
    
    try:
        # 步骤1: 将 PDF 图纸转换为 PNG 图像
        print(f"ℹ️ 正在将 PDF 文件 {filepath} 转换为 PNG 图像...")
        
        # 转换 PDF 的第一页，设置 DPI (200)
        if poppler_path:
            images = convert_from_path(
                filepath,
                first_page=1,
                last_page=1,
                dpi=200,
                poppler_path=poppler_path
            )
        else:
            images = convert_from_path(
                filepath,
                first_page=1,
                last_page=1,
                dpi=200
            )
        
        if not images:
            raise ValueError("PDF 转换失败或文件为空。请检查 Poppler 是否安装正确。")
        
        # 生成唯一的PNG文件名（使用时间戳和UUID）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        png_filename = f"drawing_type_{timestamp}_{unique_id}.png"
        png_file_path = png_dir / png_filename
        
        # 保存PNG图像到文件
        images[0].save(png_file_path, format='PNG')
        print(f"✅ PNG文件已保存: {png_file_path}")
        
        # 步骤2: 读取提示词内容
        with open(prompt_file, 'r', encoding='utf-8') as f:
            prompt_content = f.read()
        
        # 步骤3: 调用模型进行检测
        print(f"🔍 开始识别图纸类型...")
        
        # 构造消息
        png_file_path = Path(str(png_file_path).replace("/app", "/root/project/LLM_Detect_master"))
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt_content},
                    {"type": "image_url", "image_url": {"url": f"file://{png_file_path}"}}
                ]
            }
        ]
        
        # 调用模型
        completion = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0.6,
            max_tokens=8192
        )
        
        # 获取模型输出结果
        result = completion.choices[0].message.content
        
        # 清理结果（移除思考过程标签）
        cleaned_result = re.sub(r'<think>.*?</think>', '', result, flags=re.DOTALL)
        cleaned_result = re.sub(r'</?answer>', '', cleaned_result)
        cleaned_result = cleaned_result.strip()
        
        print(f"✅ 图纸类型识别完成: {cleaned_result}")
        
        # 步骤4: 将检测结果写入PNG目录下的检测.txt文件
        result_file = png_dir / "检测.txt"
        
        # 追加模式写入文件
        with open(result_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{'=' * 80}\n")
            f.write(f"检测时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"图纸文件: {os.path.basename(filepath)}\n")
            f.write(f"PNG文件: {png_filename}\n")
            f.write(f"识别结果: {cleaned_result}\n")
            f.write(f"{'=' * 80}\n")
        
        print(f"✅ 检测结果已保存到: {result_file}")
        
        return cleaned_result
        
    except Exception as e:
        error_msg = f"图纸类型识别失败: {str(e)}"
        print(f"❌ 错误: {error_msg}")
        import traceback
        traceback.print_exc()
        return None
    
    finally:
        # 注意：这里不删除PNG文件，因为后续检测可能需要使用
        pass


if __name__ == "__main__":
    # 测试代码
    test_filepath = "test_drawing.pdf"
    result = identify_drawing_type(test_filepath)
    if result:
        print(f"\n识别结果: {result}")
    else:
        print("\n识别失败")
