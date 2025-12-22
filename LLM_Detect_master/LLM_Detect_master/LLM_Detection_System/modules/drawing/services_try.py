#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
制图检测测试服务模块 - 用于测试prompt_1.txt提示词效果
仅将PDF转换为PNG，使用prompt_1.txt进行检测，并将结果保存到.txt文件
"""

import os
import time
from pathlib import Path
from openai import OpenAI
import re
import uuid
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# 导入处理 PDF 的依赖库
try:
    from pdf2image import convert_from_path
    from PIL import Image
except ImportError:
    print("❌ 错误: 缺少必要的依赖库。请运行: pip install pdf2image Pillow")

from modules.drawing.utils import get_poppler_path


def inspect_drawing_test(drawing_file_path, drawing_type=None):
    """制图检测测试函数 - 使用prompt_1.txt进行测试

    将 PDF 转换为 PNG 图像并保存到 drawing/PNG 目录，
    使用prompt_1.txt作为提示词进行检测，
    将模型输出结果保存到PNG目录下的.txt文件。

    Args:
        drawing_file_path (str): 待检测的PDF制图文件路径
        drawing_type (str): 图纸类型（可选）

    Returns:
        dict: 包含检测结果文件路径的字典
    """

    # 获取API密钥和模型配置
    api_key = os.getenv('DRAWING_API_KEY', 'Angel@123456')
    model_name = os.getenv('DRAWING_MODEL_NAME', 'GLM-4.1V-9B-Thinking')
    model_url = os.getenv('DRAWING_BASE_URL', 'http://10.2.32.163:8001/v1')

    # 验证配置
    if not api_key:
        error_msg = "未配置 API 密钥..."
        print(f"❌ 错误: {error_msg}")
        return {"error": error_msg}

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

    # 获取prompt文件路径（drawing_12prompts目录）
    base_dir = Path(__file__).resolve().parent.parent.parent
    prompts_dir = base_dir / "prompts" / "drawing_12prompts"

    print(f"📁 提示词目录路径: {prompts_dir}")

    # 获取Poppler路径
    poppler_path = get_poppler_path()
    if poppler_path:
        print(f"🔧 Poppler路径: {poppler_path}")
    else:
        print(f"🔧 Poppler: 使用系统PATH")

    # 检查待检测文件是否存在
    if not os.path.exists(drawing_file_path):
        error_msg = f"找不到待检测文件 - {drawing_file_path}"
        print(f"❌ 错误: {error_msg}")
        return {"error": error_msg}

    # 创建PNG存储目录
    png_dir = Path(__file__).resolve().parent / "PNG"
    png_dir.mkdir(exist_ok=True)

    # 初始化PNG文件路径变量
    png_file_path = None
    result_file_path = None

    # 初始化all_result字段，用于存储所有检测结果
    all_result = ""

    # 初始化不符合项计数
    non_conforming_count = 0

    try:
        # 步骤1: 将 PDF 图纸转换为 PNG 图像，并保存到 drawing/PNG 目录
        print(f"ℹ️ 正在将 PDF 文件 {drawing_file_path} 转换为 PNG 图像...")

        # 转换 PDF 的第一页，设置 DPI (200)
        if poppler_path:
            images = convert_from_path(
                drawing_file_path,
                first_page=1,
                last_page=1,
                dpi=200,
                poppler_path=poppler_path
            )
        else:
            images = convert_from_path(
                drawing_file_path,
                first_page=1,
                last_page=1,
                dpi=200
            )

        if not images:
            raise ValueError("PDF 转换失败或文件为空。请检查 Poppler 是否安装正确。")

        # 生成唯一的PNG文件名（使用时间戳和UUID）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        png_filename = f"drawing_{timestamp}_{unique_id}.png"
        png_file_path = png_dir / png_filename

        # 保存PNG图像到文件
        images[0].save(png_file_path, format='PNG')

        logger.info(f"✅ PDF转换完成，PNG文件已保存: {png_file_path}")
        print(f"✅ PNG文件已保存: {png_file_path}")

        # 步骤2: 对每个prompt文件进行检测（12次顺序执行）
        png_file_path = Path(str(png_file_path).replace("/app", "/root/project/LLM_Detect_master"))

        # 检测1: prompt_1.txt（爆炸图或水路图跳过模型检测）
        print(f"\n🔍 [1/12] 使用 prompt_1.txt 进行检测...")
        if drawing_type in ["爆炸图", "水路图"]:
            cleaned_result = '''**第1条检测结果：**
- 检测项目：尺寸公差检测
- 检测结果：符合
- 发现内容：无
- 位置描述：无
- 符合/不符合原因：图纸类型为水路图或爆炸图，该类图纸无公差
- 修改建议：无'''
            all_result += f"{cleaned_result.strip()}\n\n"
            if re.search(r'- 检测结果[：:]\s*不符合', cleaned_result):
                non_conforming_count += 1
            print(f"✅ [1/12] prompt_1.txt 检测完成（图纸类型为{drawing_type}，跳过模型检测）")
        else:
            prompt_file = prompts_dir / "prompt_1.txt"
            if prompt_file.exists():
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    prompt_content = f.read()
                messages = [{"role": "user", "content": [{"type": "text", "text": prompt_content}, {"type": "image_url",
                                                                                                    "image_url": {
                                                                                                        "url": f"file://{png_file_path}"}}]}]
                completion = client.chat.completions.create(model=model_name, messages=messages, temperature=0.6,
                                                            max_tokens=8192)
                result = completion.choices[0].message.content
                cleaned_result = re.sub(r'<think>.*?</think>', '', result, flags=re.DOTALL)
                cleaned_result = re.sub(r'</?answer>', '', cleaned_result)
                all_result += f"{cleaned_result.strip()}\n\n"
                if re.search(r'- 检测结果[：:]\s*不符合', cleaned_result):
                    non_conforming_count += 1
                print(f"✅ [1/12] prompt_1.txt 检测完成")

        # 检测2: prompt_2.txt（爆炸图或水路图跳过模型检测）
        print(f"\n🔍 [2/12] 使用 prompt_2.txt 进行检测...")
        if drawing_type in ["爆炸图", "水路图"]:
            cleaned_result = '''**第2条检测结果：**
- 检测项目：公差精确度检测
- 检测结果：符合
- 发现内容：无
- 位置描述：无
- 符合/不符合原因：图纸类型为水路图或爆炸图，该类图纸无公差
- 修改建议：无'''
            all_result += f"{cleaned_result.strip()}\n\n"
            if re.search(r'- 检测结果[：:]\s*不符合', cleaned_result):
                non_conforming_count += 1
            print(f"✅ [2/12] prompt_2.txt 检测完成（图纸类型为{drawing_type}，跳过模型检测）")
        else:
            prompt_file = prompts_dir / "prompt_2.txt"
            if prompt_file.exists():
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    prompt_content = f.read()
                messages = [{"role": "user", "content": [{"type": "text", "text": prompt_content}, {"type": "image_url",
                                                                                                    "image_url": {
                                                                                                        "url": f"file://{png_file_path}"}}]}]
                completion = client.chat.completions.create(model=model_name, messages=messages, temperature=0.6,
                                                            max_tokens=8192)
                result = completion.choices[0].message.content
                cleaned_result = re.sub(r'<think>.*?</think>', '', result, flags=re.DOTALL)
                cleaned_result = re.sub(r'</?answer>', '', cleaned_result)
                all_result += f"{cleaned_result.strip()}\n\n"
                if re.search(r'- 检测结果[：:]\s*不符合', cleaned_result):
                    non_conforming_count += 1
                print(f"✅ [2/12] prompt_2.txt 检测完成")

        # 检测3: prompt_3.txt（爆炸图或水路图跳过模型检测）
        print(f"\n🔍 [3/12] 使用 prompt_3.txt 进行检测...")
        if drawing_type in ["爆炸图", "水路图"]:
            cleaned_result = '''**第3条检测结果：**
- 检测项目：关键尺寸识别
- 检测结果：不符合
- 发现内容：无
- 位置描述：无
- 符合/不符合原因：图纸类型为水路图或爆炸图，该类图纸无尺寸
- 修改建议：无'''
            all_result += f"{cleaned_result.strip()}\n\n"
            if re.search(r'- 检测结果[：:]\s*不符合', cleaned_result):
                non_conforming_count += 1
            print(f"✅ [3/12] prompt_3.txt 检测完成（图纸类型为{drawing_type}，跳过模型检测）")
        else:
            prompt_file = prompts_dir / "prompt_3.txt"
            if prompt_file.exists():
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    prompt_content = f.read()
                messages = [{"role": "user", "content": [{"type": "text", "text": prompt_content}, {"type": "image_url",
                                                                                                    "image_url": {
                                                                                                        "url": f"file://{png_file_path}"}}]}]
                completion = client.chat.completions.create(model=model_name, messages=messages, temperature=0.6,
                                                            max_tokens=8192)
                result = completion.choices[0].message.content
                cleaned_result = re.sub(r'<think>.*?</think>', '', result, flags=re.DOTALL)
                cleaned_result = re.sub(r'</?answer>', '', cleaned_result)
                all_result += f"{cleaned_result.strip()}\n\n"
                if re.search(r'- 检测结果[：:]\s*不符合', cleaned_result):
                    non_conforming_count += 1
                print(f"✅ [3/12] prompt_3.txt 检测完成")

        # 检测4: prompt_4.txt（爆炸图或水路图跳过模型检测）
        print(f"\n🔍 [4/12] 使用 prompt_4.txt 进行检测...")
        if drawing_type in ["爆炸图", "水路图"]:
            cleaned_result = '''**第4条检测结果：**
- 检测项目：技术要求检测
- 检测结果：符合
- 发现内容：无
- 位置描述：无
- 符合/不符合原因：图纸类型为水路图或爆炸图，该类图纸无技术要求
- 修改建议：无'''
            all_result += f"{cleaned_result.strip()}\n\n"
            if re.search(r'- 检测结果[：:]\s*不符合', cleaned_result):
                non_conforming_count += 1
            print(f"✅ [4/12] prompt_4.txt 检测完成（图纸类型为{drawing_type}，跳过模型检测）")
        else:
            prompt_file = prompts_dir / "prompt_4.txt"
            if prompt_file.exists():
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    prompt_content = f.read()
                messages = [{"role": "user", "content": [{"type": "text", "text": prompt_content}, {"type": "image_url",
                                                                                                    "image_url": {
                                                                                                        "url": f"file://{png_file_path}"}}]}]
                completion = client.chat.completions.create(model=model_name, messages=messages, temperature=0.6,
                                                            max_tokens=8192)
                result = completion.choices[0].message.content
                cleaned_result = re.sub(r'<think>.*?</think>', '', result, flags=re.DOTALL)
                cleaned_result = re.sub(r'</?answer>', '', cleaned_result)
                all_result += f"{cleaned_result.strip()}\n\n"
                if re.search(r'- 检测结果[：:]\s*不符合', cleaned_result):
                    non_conforming_count += 1
                print(f"✅ [4/12] prompt_4.txt 检测完成")

        # 检测5: 根据图纸类型选择prompt文件
        print(f"\n🔍 [5/12] 进行人员参数检查...")
        if drawing_type in ["钣金件", "塑胶件", "电器件", "总成图"]:
            cleaned_result = '''**第5条检测结果：**
- 检测项目：人员参数检查
- 检测结果：符合
- 发现内容：无
- 位置描述：无
- 符合/不符合原因：图纸类型为"钣金件"、"塑胶件"、"电器件"或"总成图"，该类图纸人员参数设置在CREO
- 修改建议：无'''
            all_result += f"{cleaned_result.strip()}\n\n"
            if re.search(r'- 检测结果[：:]\s*不符合', cleaned_result):
                non_conforming_count += 1
            print(f"✅ [5/12] 人员参数检查完成（图纸类型为{drawing_type}，跳过模型检测）")
        else:
            if drawing_type in ["爆炸图", "水路图"]:
                prompt_file = prompts_dir / "prompt_5_waterboom.txt"
                prompt_name = "prompt_5_waterboom.txt"
            else:
                prompt_file = prompts_dir / "prompt_5.txt"
                prompt_name = "prompt_5.txt"

            if prompt_file.exists():
                print(f"使用 {prompt_name} 进行检测...")
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    prompt_content = f.read()
                messages = [{"role": "user", "content": [{"type": "text", "text": prompt_content}, {"type": "image_url",
                                                                                                    "image_url": {
                                                                                                        "url": f"file://{png_file_path}"}}]}]
                completion = client.chat.completions.create(model=model_name, messages=messages, temperature=0.6,
                                                            max_tokens=8192)
                result = completion.choices[0].message.content
                cleaned_result = re.sub(r'<think>.*?</think>', '', result, flags=re.DOTALL)
                cleaned_result = re.sub(r'</?answer>', '', cleaned_result)
                all_result += f"{cleaned_result.strip()}\n\n"
                if re.search(r'- 检测结果[：:]\s*不符合', cleaned_result):
                    non_conforming_count += 1
                print(f"✅ [5/12] {prompt_name} 检测完成")

        # 检测6: prompt_6.txt（爆炸图或水路图跳过模型检测）
        print(f"\n🔍 [6/12] 使用 prompt_6.txt 进行检测...")
        if drawing_type in ["爆炸图", "水路图"]:
            cleaned_result = '''**第6条检测结果：**
- 检测项目：未注公差表检查
- 检测结果：符合
- 发现内容：无
- 位置描述：无
- 符合/不符合原因：图纸类型为水路图或爆炸图，该类图纸无公差
- 修改建议：无'''
            all_result += f"{cleaned_result.strip()}\n\n"
            if re.search(r'- 检测结果[：:]\s*不符合', cleaned_result):
                non_conforming_count += 1
            print(f"✅ [6/12] prompt_6.txt 检测完成（图纸类型为{drawing_type}，跳过模型检测）")
        else:
            prompt_file = prompts_dir / "prompt_6.txt"
            if prompt_file.exists():
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    prompt_content = f.read()
                messages = [{"role": "user", "content": [{"type": "text", "text": prompt_content}, {"type": "image_url",
                                                                                                    "image_url": {
                                                                                                        "url": f"file://{png_file_path}"}}]}]
                completion = client.chat.completions.create(model=model_name, messages=messages, temperature=0.6,
                                                            max_tokens=8192)
                result = completion.choices[0].message.content
                cleaned_result = re.sub(r'<think>.*?</think>', '', result, flags=re.DOTALL)
                cleaned_result = re.sub(r'</?answer>', '', cleaned_result)
                all_result += f"{cleaned_result.strip()}\n\n"
                if re.search(r'- 检测结果[：:]\s*不符合', cleaned_result):
                    non_conforming_count += 1
                print(f"✅ [6/12] prompt_6.txt 检测完成")

        # 检测7: prompt_7.txt
        prompt_file = prompts_dir / "prompt_7.txt"
        if prompt_file.exists():
            print(f"\n🔍 [7/12] 使用 prompt_7.txt 进行检测...")
            with open(prompt_file, 'r', encoding='utf-8') as f:
                prompt_content = f.read()
            messages = [{"role": "user", "content": [{"type": "text", "text": prompt_content}, {"type": "image_url",
                                                                                                "image_url": {
                                                                                                    "url": f"file://{png_file_path}"}}]}]
            completion = client.chat.completions.create(model=model_name, messages=messages, temperature=0.6,
                                                        max_tokens=8192)
            result = completion.choices[0].message.content
            cleaned_result = re.sub(r'<think>.*?</think>', '', result, flags=re.DOTALL)
            cleaned_result = re.sub(r'</?answer>', '', cleaned_result)
            all_result += f"{cleaned_result.strip()}\n\n"
            if re.search(r'- 检测结果[：:]\s*不符合', cleaned_result):
                non_conforming_count += 1
            print(f"✅ [7/12] prompt_7.txt 检测完成")

        # 检测8: prompt_8.txt
        prompt_file = prompts_dir / "prompt_8.txt"
        if prompt_file.exists():
            print(f"\n🔍 [8/12] 使用 prompt_8.txt 进行检测...")
            with open(prompt_file, 'r', encoding='utf-8') as f:
                prompt_content = f.read()
            messages = [{"role": "user", "content": [{"type": "text", "text": prompt_content}, {"type": "image_url",
                                                                                                "image_url": {
                                                                                                    "url": f"file://{png_file_path}"}}]}]
            completion = client.chat.completions.create(model=model_name, messages=messages, temperature=0.6,
                                                        max_tokens=8192)
            result = completion.choices[0].message.content
            cleaned_result = re.sub(r'<think>.*?</think>', '', result, flags=re.DOTALL)
            cleaned_result = re.sub(r'</?answer>', '', cleaned_result)
            all_result += f"{cleaned_result.strip()}\n\n"
            if re.search(r'- 检测结果[：:]\s*不符合', cleaned_result):
                non_conforming_count += 1
            print(f"✅ [8/12] prompt_8.txt 检测完成")

        # 检测9: prompt_9.txt
        prompt_file = prompts_dir / "prompt_9.txt"
        if prompt_file.exists():
            print(f"\n🔍 [9/12] 使用 prompt_9.txt 进行检测...")
            with open(prompt_file, 'r', encoding='utf-8') as f:
                prompt_content = f.read()
            messages = [{"role": "user", "content": [{"type": "text", "text": prompt_content}, {"type": "image_url",
                                                                                                "image_url": {
                                                                                                    "url": f"file://{png_file_path}"}}]}]
            completion = client.chat.completions.create(model=model_name, messages=messages, temperature=0.6,
                                                        max_tokens=8192)
            result = completion.choices[0].message.content
            cleaned_result = re.sub(r'<think>.*?</think>', '', result, flags=re.DOTALL)
            cleaned_result = re.sub(r'</?answer>', '', cleaned_result)
            all_result += f"{cleaned_result.strip()}\n\n"
            if re.search(r'- 检测结果[：:]\s*不符合', cleaned_result):
                non_conforming_count += 1
            print(f"✅ [9/12] prompt_9.txt 检测完成")

        # 检测10: prompt_10.txt（材料信息检查，需后处理结果）
        prompt_file = prompts_dir / "prompt_10.txt"
        if prompt_file.exists():
            print(f"\n🔍 [10/12] 使用 prompt_10.txt 进行检测...")
            with open(prompt_file, 'r', encoding='utf-8') as f:
                prompt_content = f.read()
            messages = [{"role": "user", "content": [{"type": "text", "text": prompt_content}, {"type": "image_url",
                                                                                                "image_url": {
                                                                                                    "url": f"file://{png_file_path}"}}]}]
            completion = client.chat.completions.create(model=model_name, messages=messages, temperature=0.6,
                                                        max_tokens=8192)
            result = completion.choices[0].message.content
            cleaned_result = re.sub(r'<think>.*?</think>', '', result, flags=re.DOTALL)
            cleaned_result = re.sub(r'</?answer>', '', cleaned_result)

            # 后处理：根据图纸类型和发现内容修改检测结果
            material_content_match = re.search(r'- 发现内容[：:]\s*(.+)', cleaned_result)
            if material_content_match:
                material_content = material_content_match.group(1).strip()

                # 爆炸图或水路图：发现内容不是"/"则不符合
                if drawing_type in ["爆炸图", "水路图"] and material_content != "/":
                    cleaned_result = re.sub(r'(- 检测结果[：:]\s*)符合', r'\1不符合', cleaned_result)
                    cleaned_result = re.sub(r'(- 符合/不符合原因[：:]\s*)[^\n]+', r'\1图纸中材料信息不为"/"',
                                            cleaned_result)
                    cleaned_result = re.sub(r'(- 修改建议[：:]\s*)[^\n]+', r'\1修改材料信息', cleaned_result)

                # 非爆炸图/水路图：发现内容是"/"则不符合
                elif drawing_type not in ["爆炸图", "水路图"] and material_content == "/":
                    cleaned_result = re.sub(r'(- 检测结果[：:]\s*)符合', r'\1不符合', cleaned_result)
                    cleaned_result = re.sub(r'(- 符合/不符合原因[：:]\s*)[^\n]+', r'\1图纸中材料信息为"/"',
                                            cleaned_result)
                    cleaned_result = re.sub(r'(- 修改建议[：:]\s*)[^\n]+', r'\1修改材料信息', cleaned_result)

            all_result += f"{cleaned_result.strip()}\n\n"
            if re.search(r'- 检测结果[：:]\s*不符合', cleaned_result):
                non_conforming_count += 1
            print(f"✅ [10/12] prompt_10.txt 检测完成")

        # 检测11: prompt_11.txt
        prompt_file = prompts_dir / "prompt_11.txt"
        if prompt_file.exists():
            print(f"\n🔍 [11/12] 使用 prompt_11.txt 进行检测...")
            with open(prompt_file, 'r', encoding='utf-8') as f:
                prompt_content = f.read()
            messages = [{"role": "user", "content": [{"type": "text", "text": prompt_content}, {"type": "image_url",
                                                                                                "image_url": {
                                                                                                    "url": f"file://{png_file_path}"}}]}]
            completion = client.chat.completions.create(model=model_name, messages=messages, temperature=0.6,
                                                        max_tokens=8192)
            result = completion.choices[0].message.content
            cleaned_result = re.sub(r'<think>.*?</think>', '', result, flags=re.DOTALL)
            cleaned_result = re.sub(r'</?answer>', '', cleaned_result)
            all_result += f"{cleaned_result.strip()}\n\n"
            if re.search(r'- 检测结果[：:]\s*不符合', cleaned_result):
                non_conforming_count += 1
            print(f"✅ [11/12] prompt_11.txt 检测完成")

        # 检测12: prompt_12.txt（重量信息检查，需后处理结果）
        prompt_file = prompts_dir / "prompt_12.txt"
        if prompt_file.exists():
            print(f"\n🔍 [12/12] 使用 prompt_12.txt 进行检测...")
            with open(prompt_file, 'r', encoding='utf-8') as f:
                prompt_content = f.read()
            messages = [{"role": "user", "content": [{"type": "text", "text": prompt_content}, {"type": "image_url",
                                                                                                "image_url": {
                                                                                                    "url": f"file://{png_file_path}"}}]}]
            completion = client.chat.completions.create(model=model_name, messages=messages, temperature=0.6,
                                                        max_tokens=8192)
            result = completion.choices[0].message.content
            cleaned_result = re.sub(r'<think>.*?</think>', '', result, flags=re.DOTALL)
            cleaned_result = re.sub(r'</?answer>', '', cleaned_result)

            # 后处理：根据图纸类型和发现内容修改检测结果
            weight_content_match = re.search(r'- 发现内容[：:]\s*(.+)', cleaned_result)
            if weight_content_match:
                weight_content = weight_content_match.group(1).strip()

                # 爆炸图或水路图：发现内容不是"/"则不符合
                if drawing_type in ["爆炸图", "水路图"] and weight_content != "/":
                    cleaned_result = re.sub(r'(- 检测结果[：:]\s*)符合', r'\1不符合', cleaned_result)
                    cleaned_result = re.sub(r'(- 符合/不符合原因[：:]\s*)[^\n]+', r'\1图纸中重量信息不为"/"',
                                            cleaned_result)
                    cleaned_result = re.sub(r'(- 修改建议[：:]\s*)[^\n]+', r'\1修改重量信息', cleaned_result)

                # 非爆炸图/水路图：发现内容是"/"则不符合
                elif drawing_type not in ["爆炸图", "水路图"] and weight_content == "/":
                    cleaned_result = re.sub(r'(- 检测结果[：:]\s*)符合', r'\1不符合', cleaned_result)
                    cleaned_result = re.sub(r'(- 符合/不符合原因[：:]\s*)[^\n]+', r'\1图纸中重量信息为"/"',
                                            cleaned_result)
                    cleaned_result = re.sub(r'(- 修改建议[：:]\s*)[^\n]+', r'\1修改重量信息', cleaned_result)

            all_result += f"{cleaned_result.strip()}\n\n"
            if re.search(r'- 检测结果[：:]\s*不符合', cleaned_result):
                non_conforming_count += 1
            print(f"✅ [12/12] prompt_12.txt 检测完成")

        print("\n🧹 已清理所有 <think> 标签内容。")

        # 添加最终统计信息
        conforming_count = 12 - non_conforming_count
        overall_evaluation = "不符合" if non_conforming_count > 0 else "符合"
        all_result += f"""**最终统计：**
- 符合项目：{conforming_count}项
- 不符合项目：{non_conforming_count}项
- 总体评价：{overall_evaluation}
"""

        final_result = {
            "success": True,
            "conclusion": overall_evaluation,
            "detailed_report": all_result,
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
        }

    except Exception as e:
        final_result = {"error": f"检测失败: {str(e)}"}
        if png_file_path and png_file_path.exists():
            logger.warning(f"⚠️ 检测失败，但PNG文件已保留用于调试: {png_file_path}")
            print(f"⚠️ 检测失败，PNG文件保留在: {png_file_path}")

    return final_result
