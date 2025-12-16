#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CAPTCHA工具模块 - 生成和验证验证码
"""
import random
import string
from io import BytesIO
from captcha.image import ImageCaptcha


class CaptchaGenerator:
    """验证码生成器"""
    
    def __init__(self, width=160, height=60, font_sizes=(42, 50, 56)):
        """初始化验证码生成器
        
        Args:
            width: 图片宽度
            height: 图片高度
            font_sizes: 字体大小范围
        """
        self.width = width
        self.height = height
        self.image_captcha = ImageCaptcha(width=width, height=height, font_sizes=font_sizes)
    
    def generate_code(self, length=4):
        """生成随机验证码文本
        
        Args:
            length: 验证码长度
            
        Returns:
            str: 验证码文本
        """
        # 使用数字和大写字母，排除容易混淆的字符（0, O, I, 1）
        characters = string.digits + string.ascii_uppercase
        characters = characters.replace('0', '').replace('O', '').replace('I', '').replace('1', '')
        return ''.join(random.choices(characters, k=length))
    
    def generate_image(self, code):
        """生成验证码图片
        
        Args:
            code: 验证码文本
            
        Returns:
            BytesIO: 图片数据流
        """
        # 生成验证码图片
        image = self.image_captcha.generate(code)
        
        # 将图片数据转换为BytesIO对象
        image_io = BytesIO()
        image_io.write(image.read())
        image_io.seek(0)
        
        return image_io
    
    def generate(self, length=4):
        """生成验证码（文本和图片）
        
        Args:
            length: 验证码长度
            
        Returns:
            tuple: (验证码文本, 图片数据流)
        """
        code = self.generate_code(length)
        image = self.generate_image(code)
        return code, image


def validate_captcha(user_input, stored_code):
    """验证用户输入的验证码
    
    Args:
        user_input: 用户输入的验证码
        stored_code: 存储在session中的验证码
        
    Returns:
        bool: 验证是否通过
    """
    if not user_input or not stored_code:
        return False
    
    # 不区分大小写比较
    return user_input.strip().upper() == stored_code.strip().upper()

