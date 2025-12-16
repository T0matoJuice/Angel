#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试工单质量检测模型配置
"""
import os
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'LLM_Detection_System'))

# 加载环境变量
from dotenv import load_dotenv
env_path = project_root / 'LLM_Detection_System' / '.env'
load_dotenv(env_path)

# 导入处理器
from modules.excel.processor import Processor

def test_processor_config():
    """测试处理器配置"""
    print("=" * 80)
    print("工单质量检测模型配置测试")
    print("=" * 80)
    
    try:
        # 初始化处理器
        processor = Processor()
        
        print(f"\n✅ 处理器初始化成功！")
        print(f"\n当前配置：")
        print(f"  API密钥: {processor.api_key[:20]}...{processor.api_key[-10:]}")
        print(f"  模型名称: {processor.model}")
        print(f"  API地址: {processor.base_url}")
        
        # 测试简单的API调用
        print(f"\n正在测试API连接...")
        response = processor.client.chat.completions.create(
            model=processor.model,
            messages=[{"role": "user", "content": "你好，请回复'测试成功'"}],
            max_tokens=50
        )
        
        reply = response.choices[0].message.content
        print(f"\n✅ API连接测试成功！")
        print(f"  模型回复: {reply}")
        print(f"  Token使用: 输入={response.usage.prompt_tokens}, 输出={response.usage.completion_tokens}")
        
        print("\n" + "=" * 80)
        print("✅ 所有测试通过！工单质量检测已配置为使用硅基流动在线API")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = test_processor_config()
    sys.exit(0 if success else 1)
