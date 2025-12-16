#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
制图检测服务模块 - 提供机械制图规范智能检测的核心服务功能
"""

import os
import time
import base64
import tempfile 
from pathlib import Path
from openai import OpenAI
from io import BytesIO 
# 【重要】导入正则表达式库
import re 
# 假设 load_prompt 模块已在项目中正确定义
from modules.common.prompts import load_prompt
from modules.drawing.utils import get_poppler_path
import sys 
import uuid
import logging

logger = logging.getLogger(__name__)


# 导入处理 PDF 的依赖库
# 【重要】确保已安装: pip install pdf2image Pillow
# 【重要】确保系统已安装 Poppler!
try:
    from pdf2image import convert_from_path
    from PIL import Image
except ImportError:
    print("❌ 错误: 缺少必要的依赖库。请运行: pip install pdf2image Pillow")
    # 占位函数定义（确保即使依赖缺失，代码结构也能运行）
    def load_prompt(name):
        if "detection_new" in name:
            return "你是一个专业的机械制图规范检测AI。你的任务是根据提供的制图规范，仔细检查图纸是否合规，并输出详细的检测报告。"
        elif "detection_user" in name:
            return "以下是制图规范: {textbook_content}\n\n待检测图纸已作为多模态输入提供。请根据规范，对图纸进行逐项检查，并给出总体评价和详细不合规项列表。\n\n[图纸内容已作为本地PNG文件路径作为多模态输入提供，请根据提供的机械制图规范进行检测。]"
        return ""

# 假设 load_prompt 在生产环境中是可用的
if 'convert_from_path' not in locals():
    # 这是一个冗余的检查，但保留原代码意图
    def load_prompt(name):
        if "detection_new" in name:
            return "你是一个专业的机械制图规范检测AI。你的任务是根据提供的制图规范，仔细检查图纸是否合规，并输出详细的检测报告。"
        elif "detection_user" in name:
            return "以下是制图规范: {textbook_content}\n\n待检测图纸已作为多模态输入提供。请根据规范，对图纸进行逐项检查，并给出总体评价和详细不合规项列表。\n\n[图纸内容已作为本地PNG文件路径作为多模态输入提供，请根据提供的机械制图规范进行检测。]"
        return ""


def inspect_drawing_api(drawing_file_path):
    """制图检测核心函数 - 使用LLM API分析机械制图规范合规性

    修改逻辑：将 PDF 转换为内存中的 PNG 图像，然后进行 Base64 编码，
    以 Data URL 形式作为多模态输入传递。

    Args:
        drawing_file_path (str): 待检测的PDF制图文件路径

    Returns:
        dict: 包含检测结果、结论和使用统计的字典
    """

    # 获取API密钥和模型配置
    # api_key ='Angel@123456'
    # 保持原有的模型名称
    # model_name = 'GLM-4.1V-9B-Thinking' 
    # 使用代码中的 IP 地址
    # model_url = 'http://10.2.32.163:8001/v1'

    api_key = os.getenv('DRAWING_API_KEY','Angel@123456')
    model_name = os.getenv('DRAWING_MODEL_NAME', 'GLM-4.1V-9B-Thinking')
    model_url = os.getenv('DRAWING_BASE_URL', 'http://10.2.32.163:8001/v1')
    
    # 验证配置 (此处简化，实际项目中应更严谨)
    if not api_key:
        error_msg = ("未配置 API 密钥...")
        print(f"❌ 错误: {error_msg}")
        return {"error": error_msg}

    if not model_name:
        print("⚠️ 警告: 模型名称未配置，使用默认模型")
        model_name = "default-multimodal-model"

    # 初始化客户端
    try:
        client = OpenAI(
            api_key=api_key,
            base_url=model_url,
        )
    except Exception as e:
        error_msg = f"初始化 API 客户端失败: {str(e)}"
        print(f"❌ 错误: {error_msg}")
        return {"error": error_msg}

    # 教材文件路径 - 假设该文件存在于 data 目录下
    base_dir = Path(__file__).resolve().parent.parent.parent
    textbook_file = base_dir / "data" / "机械制图规范检测标准.txt"
    
    # 获取Poppler路径
    poppler_path = get_poppler_path()
    if poppler_path:
        print(f"🔧 Poppler路径: {poppler_path}")
    else:
        print(f"🔧 Poppler: 使用系统PATH")

    print(f"📁 教材文件路径: {textbook_file}")

    # 检查必要文件是否存在
    if not textbook_file.exists():
        error_msg = f"找不到教材文件 - {textbook_file}"
        print(f"❌ 错误: {error_msg}")
        return {"error": error_msg}

    if not os.path.exists(drawing_file_path):
        error_msg = f"找不到待检测文件 - {drawing_file_path}"
        print(f"❌ 错误: {error_msg}")
        return {"error": error_msg}

    # 初始化用于 Base64 编码的变量
    base64_image = None
    
    try:
        # 步骤1: 本地读取教材文件内容 (TXT)
        with open(textbook_file, 'r', encoding='utf-8') as f:
            textbook_content = f.read()

        # 步骤2: 将 PDF 图纸转换为 PNG 图像，并在内存中进行 Base64 编码
        print(f"ℹ️ 正在将 PDF 文件 {drawing_file_path} 转换为 Base64 编码的 PNG 图像...")
        
        # 转换 PDF 的第一页，设置高 DPI (300)
        if poppler_path:
            # 使用指定的Poppler路径
            images = convert_from_path(
                drawing_file_path, 
                first_page=1, 
                last_page=1, 
                dpi=300,
                poppler_path=poppler_path
            )
        else:
            # 使用系统PATH中的Poppler
            images = convert_from_path(
                drawing_file_path, 
                first_page=1, 
                last_page=1, 
                dpi=300
            )
        
        if not images:
            raise ValueError("PDF 转换失败或文件为空。请检查 Poppler 是否安装正确。")
        
        # 使用 BytesIO 将 PIL 图像对象保存到内存中
        img_buffer = BytesIO()
        images[0].save(img_buffer, format='PNG')
        img_bytes = img_buffer.getvalue()

        # 步骤 2.5: Base64 编码
        base64_image = base64.b64encode(img_bytes).decode('utf-8')
        
        # 构建 Data URL
        data_url = f"data:image/png;base64,{base64_image}"
        
        logger.info(data_url)
        logger.info("✅ 文件转换和 Base64 编码完成。")

        # 步骤3: 加载AI检测提示词
        system_prompt = load_prompt('drawing_detection_new')
        
        # 步骤4: 构建用户请求的文本部分
        user_text_request = load_prompt('drawing_detection_user').format(
            textbook_content=textbook_content,
            # 告诉模型图纸已作为多模态输入提供
            drawing_content="[图纸内容已作为Base64编码的PNG图像作为多模态输入提供，请根据提供的机械制图规范进行检测。]"
        )

        # 步骤5: 构建对话消息（系统指令+用户请求，包含多模态输入）
        messages = [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": [
                    # 文本请求部分
                    {"type": "text", "text": user_text_request},
                    # 【关键修改】多模态文件部分，传递 Base64 Data URL
                    {
                        "type": "image_url",
                        "image_url": {
                            # 传递 Base64 格式的 Data URL
                            "url": data_url
                        }
                    }
                ],
            },
        ]

        # 步骤6: 调用 API 进行智能检测
        completion = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0.6,
            max_tokens=8192,
        )

        # 步骤7: 获取结果
        result = completion.choices[0].message.content
        
        # 🚀 步骤 7.5: 【新增】输出结果后处理，去除 <think> 标签内容
        # 使用 re.sub 查找并替换所有 <think>...</think> 之间的内容
        # re.DOTALL 确保 '.' 匹配换行符，从而可以匹配多行思考内容
        cleaned_result = re.sub(r'<think>.*?</think>', '', result, flags=re.DOTALL)
        print("🧹 已清理 <think> 标签内容。")
        
        # 后续操作都基于 cleaned_result
        detailed_report = cleaned_result
        
        # 步骤8-10: 解析结论 (基于 cleaned_result)
        conclusion = "未知"
        keywords = ["基本不符合", "基本符合", "不符合", "符合"]
        evaluation_markers = ["总体评价：", "总体评价:", "- 总体评价：", "- 总体评价:"]
        evaluation_section = None
        
        for marker in evaluation_markers:
            if marker in detailed_report:
                marker_pos = detailed_report.find(marker)
                evaluation_section = detailed_report[marker_pos:marker_pos + 100]
                break
        
        if evaluation_section:
            for keyword in keywords:
                if keyword in evaluation_section:
                    conclusion = keyword
                    break
        
        if conclusion == "未知":
            first_keyword = None
            first_position = len(detailed_report)

            for keyword in keywords:
                if keyword in detailed_report:
                    position = detailed_report.find(keyword)
                    if position < first_position:
                        first_position = position
                        first_keyword = keyword
            
            if first_keyword:
                conclusion = first_keyword

        
        final_result = {
            "success": True,
            "conclusion": conclusion,
            "detailed_report": detailed_report,
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
        }

    except Exception as e:
        final_result = {"error": f"检测失败: {str(e)}"}
    
    finally:
        # 清理逻辑保持不变
        pass 
            
    return final_result

