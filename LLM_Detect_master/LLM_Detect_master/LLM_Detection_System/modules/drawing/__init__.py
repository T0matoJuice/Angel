"""
制图检测模块

提供PDF制图文件的智能检测功能：
- 制图规范检测
- PDF预览功能
- 历史记录管理
"""

# 导出主要函数，方便外部导入
from .utils import allowed_file, convert_pdf_to_image, create_placeholder_image
from .services import inspect_drawing_api

__all__ = ['allowed_file', 'convert_pdf_to_image', 'create_placeholder_image', 'inspect_drawing_api']
