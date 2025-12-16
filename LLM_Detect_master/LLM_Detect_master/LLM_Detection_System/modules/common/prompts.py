#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
提示词管理模块
"""

import os
from pathlib import Path

def load_prompt(prompt_name):
    """加载提示词文件

    使用绝对路径确保无论从哪个目录启动应用都能找到提示词文件

    Args:
        prompt_name (str): 提示词文件名（不含.txt后缀）

    Returns:
        str: 提示词内容，如果加载失败返回空字符串
    """
    try:
        # 获取当前文件所在目录的父目录的父目录（即 LLM_Detection_System 目录）
        # 当前文件: modules/common/prompts.py
        # parent: modules/common
        # parent.parent: modules
        # parent.parent.parent: LLM_Detection_System
        base_dir = Path(__file__).resolve().parent.parent.parent
        prompt_path = base_dir / "prompts" / f"{prompt_name}.txt"

        # 调试信息（可选，便于排查问题）
        # print(f"📄 加载提示词: {prompt_name}")
        # print(f"📁 提示词路径: {prompt_path}")
        # print(f"📁 文件存在: {prompt_path.exists()}")

        if not prompt_path.exists():
            raise FileNotFoundError(f"提示词文件不存在: {prompt_path}")

        with open(prompt_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()

        # print(f"✅ 提示词加载成功: {prompt_name} ({len(content)} 字符)")
        return content

    except Exception as e:
        print(f"❌ 加载提示词失败 {prompt_name}: {e}")
        return ""
