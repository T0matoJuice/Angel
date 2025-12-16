#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大模型智能检测系统 - 集成制图检测和质量工单检测功能

"""

from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
import os
import tempfile
import time
import base64
import json
import pandas as pd
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from io import BytesIO
from pdf2image import convert_from_path
from PIL import Image
from werkzeug.utils import secure_filename

# 加载环境变量（API密钥等）
load_dotenv('.env')

# 初始化Flask应用
app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 配置文件上传
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# 配置历史记录存储
HISTORY_FOLDER = 'history'
if not os.path.exists(HISTORY_FOLDER):
    os.makedirs(HISTORY_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['HISTORY_FOLDER'] = HISTORY_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 限制文件大小50MB
app.config['MAX_HISTORY_RECORDS'] = 10  # 最大历史记录数

# ==================== 提示词管理函数 ====================

def load_prompt(prompt_name):
    """加载提示词文件"""
    try:
        prompt_path = os.path.join('prompts', f'{prompt_name}.txt')
        if not os.path.exists(prompt_path):
            raise FileNotFoundError(f"提示词文件不存在: {prompt_path}")

        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception as e:
        print(f"加载提示词失败 {prompt_name}: {e}")
        return ""

# ==================== 制图检测相关函数 ====================

def allowed_file(filename):
    """检查文件是否为PDF格式"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'pdf'

def inspect_drawing_api(drawing_file_path):
    """制图检测核心函数 - 使用Kimi API分析制图规范"""

    # 初始化Kimi客户端
    client = OpenAI(
        api_key=os.getenv('MOONSHOT_API_KEY'),
        base_url="https://api.moonshot.cn/v1",
    )
    model_name = os.getenv('MOONSHOT_MODEL_vision')
    # 教材文件路径
    textbook_file = "data/机械制图规范检测标准.txt"

    # 检查必要文件是否存在
    if not os.path.exists(textbook_file):
        return {"error": f"找不到教材文件 - {textbook_file}"}

    if not os.path.exists(drawing_file_path):
        return {"error": f"找不到待检测文件 - {drawing_file_path}"}

    try:
        # 步骤1: 上传教材文件到Kimi
        textbook_object = client.files.create(file=Path(textbook_file), purpose="file-extract")

        # 步骤2: 上传待检测的制图文件到Kimi
        drawing_object = client.files.create(file=Path(drawing_file_path), purpose="file-extract")

        # 步骤3: 提取教材文本内容
        textbook_content = client.files.content(file_id=textbook_object.id).text

        # 步骤4: 提取制图文本内容
        drawing_content = client.files.content(file_id=drawing_object.id).text

        # 步骤5: 加载AI检测提示词
        system_prompt = load_prompt('drawing_detection_system')

        # 步骤6: 构建对话消息（系统指令+用户请求）
        messages = [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": load_prompt('drawing_detection_user').format(
                    textbook_content=textbook_content,
                    drawing_content=drawing_content
                )
            },
        ]

        # 步骤7: 调用Kimi API进行智能检测
        completion = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0.6,  # 控制回答的随机性
            max_tokens=4000,  # 限制回答长度
        )

        # 步骤8: 获取AI检测结果
        result = completion.choices[0].message.content

        # 步骤9: 解析检测结论（从AI回答中提取关键结论）
        conclusion = "未知"  # 默认值

        # 定义所有可能的结论关键词（按长度从长到短排序，避免短词匹配长词）
        keywords = ["基本不符合", "基本符合", "不符合", "符合"]

        # 在整个输出文本中找到第一个出现的关键词
        first_keyword = None
        first_position = len(result)

        for keyword in keywords:
            if keyword in result:
                position = result.find(keyword)
                if position < first_position:
                    first_position = position
                    first_keyword = keyword

        if first_keyword:
            conclusion = first_keyword
        else:
            conclusion = "未知"

        detailed_report = result

        # 步骤10: 清理临时上传的文件
        try:
            client.files.delete(textbook_object.id)
            client.files.delete(drawing_object.id)
        except:
            pass  # 忽略删除失败

        return {
            "success": True,
            "conclusion": conclusion,
            "detailed_report": detailed_report,
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
        }

    except Exception as e:
        return {"error": f"检测失败: {str(e)}"}

def convert_pdf_to_image(pdf_path, page_num=0, max_width=800):
    """PDF转图片预览功能"""
    try:
        # 使用poppler工具转换PDF为图片
        images = convert_from_path(
            pdf_path,
            first_page=page_num+1,  # 指定页码
            last_page=page_num+1,
            dpi=150,  # 图片清晰度
            poppler_path=r"D:\poppler\poppler\poppler-25.07.0\Library\bin"
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
        print(f"PDF预览失败: {e}")

    return None

def create_placeholder_image(filename):
    """创建PDF占位符图片"""
    try:
        from PIL import ImageDraw, ImageFont

        # 创建一个占位符图片
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

# ==================== 历史记录管理函数 ====================

def save_detection_history(filename, conclusion, detailed_report, timestamp):
    """保存检测历史记录"""
    try:
        history_file = os.path.join(app.config['HISTORY_FOLDER'], 'detection_history.json')

        # 创建新的历史记录
        new_record = {
            'id': str(int(time.time() * 1000)),  # 使用毫秒时间戳作为ID
            'filename': filename,
            'original_filename': filename.split('_', 1)[1] if '_' in filename else filename,
            'conclusion': conclusion,
            'detailed_report': detailed_report,
            'timestamp': timestamp,
            'created_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }

        # 读取现有历史记录
        history_records = []
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    history_records = json.load(f)
            except:
                history_records = []

        # 添加新记录到列表开头
        history_records.insert(0, new_record)

        # 限制历史记录数量
        max_records = app.config['MAX_HISTORY_RECORDS']
        if len(history_records) > max_records:
            history_records = history_records[:max_records]

        # 保存更新后的历史记录
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history_records, f, ensure_ascii=False, indent=2)

        return True

    except Exception as e:
        print(f"保存历史记录失败: {e}")
        return False

def get_detection_history():
    """获取制图检测历史记录"""
    try:
        history_file = os.path.join(app.config['HISTORY_FOLDER'], 'detection_history.json')

        if not os.path.exists(history_file):
            return []

        with open(history_file, 'r', encoding='utf-8') as f:
            history_records = json.load(f)

        return history_records

    except Exception as e:
        print(f"读取制图检测历史记录失败: {e}")
        return []

def save_excel_history(filename, original_filename, rows_processed, timestamp):
    """保存Excel处理历史记录"""
    try:
        history_file = os.path.join(app.config['HISTORY_FOLDER'], 'excel_history.json')

        # 创建新的历史记录
        new_record = {
            'id': str(int(time.time() * 1000)),  # 使用毫秒时间戳作为ID
            'filename': filename,
            'original_filename': original_filename,
            'rows_processed': rows_processed,
            'timestamp': timestamp,
            'created_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }

        # 读取现有历史记录
        history_records = []
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    history_records = json.load(f)
            except:
                history_records = []

        # 添加新记录到列表开头
        history_records.insert(0, new_record)

        # 限制历史记录数量
        max_records = app.config['MAX_HISTORY_RECORDS']
        if len(history_records) > max_records:
            history_records = history_records[:max_records]

        # 保存更新后的历史记录
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history_records, f, ensure_ascii=False, indent=2)

        return True

    except Exception as e:
        print(f"保存Excel处理历史记录失败: {e}")
        return False

def get_excel_history():
    """获取Excel处理历史记录"""
    try:
        history_file = os.path.join(app.config['HISTORY_FOLDER'], 'excel_history.json')

        if not os.path.exists(history_file):
            return []

        with open(history_file, 'r', encoding='utf-8') as f:
            history_records = json.load(f)

        return history_records

    except Exception as e:
        print(f"读取Excel处理历史记录失败: {e}")
        return []

# ==================== Excel检测相关类（来自Excel_detect/Excel_detect_app.py）====================

class Processor:
    """Excel智能填充处理器 - 使用K2模型学习和推理"""

    def __init__(self):
        """初始化大模型处理器"""

        # 获取API密钥
        self.api_key = os.getenv('MOONSHOT_API_KEY')
        self.model = os.getenv('MOONSHOT_MODEL_turbo')
        if not self.api_key:
            raise ValueError("未找到MOONSHOT_API_KEY")

        # 初始化Kimi客户端
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.moonshot.cn/v1",
            timeout=120  # 设置超时时间
        )

    def learn_rules(self, training_excel: str) -> tuple:
        """第一阶段：从训练数据中学习推理规则"""
        try:
            # 上传训练Excel文件到Kimi
            training_file_object = self.client.files.create(
                file=Path(training_excel),
                purpose="file-extract"
            )

            # 提取训练文件的文本内容
            training_content = self.client.files.content(file_id=training_file_object.id).text

            # 构建学习规则的提示词
            prompt1 = load_prompt('excel_learn_rules').format(training_content=training_content)

            messages = [{"role": "user", "content": prompt1}]

            # 调用K2模型学习规则
            resp1 = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.6,  # 控制创造性
                max_tokens=10000  # 允许较长回答
            )

            # 提取学习到的规则
            rules = resp1.choices[0].message.content.strip()
            messages.append({"role": "assistant", "content": rules})

            return messages, rules, resp1.usage  # 返回对话历史、规则和token使用量

        except Exception as e:
            raise Exception(f"学习规则失败: {str(e)}")

    def apply_rules(self, messages: list, test_excel: str) -> tuple:
        """第二阶段：应用学到的规则对测试数据进行填充"""
        try:
            # 上传测试Excel文件到Kimi
            test_file_object = self.client.files.create(
                file=Path(test_excel),
                purpose="file-extract"
            )

            # 提取测试文件的文本内容
            test_content = self.client.files.content(file_id=test_file_object.id).text

            # 读取Excel获取数据行数（用于验证输出完整性）
            df_test = pd.read_excel(test_excel, dtype=str)
            test_row_count = len(df_test)

            # 构建应用规则的提示词
            prompt2 = load_prompt('excel_apply_rules').format(
                test_content=test_content,
                test_row_count=test_row_count
            )

            # 添加应用规则的用户请求到对话历史
            messages.append({"role": "user", "content": prompt2})

            # 调用K2模型应用规则进行填充
            resp2 = self.client.chat.completions.create(
                model=self.model,
                messages=messages,  # 包含之前学习的规则
                temperature=0.6,
                max_tokens=10000
            )

            # 提取填充结果
            filled_result = resp2.choices[0].message.content.strip()

            return filled_result, resp2.usage  # 返回填充结果和token使用量

        except Exception as e:
            raise Exception(f"应用规则失败: {str(e)}")

    def learn_quality_rules_v1_backup(self, training_excel: str) -> tuple:
        """备份版本：第一阶段：从训练数据中学习非质量问题识别规则"""
        try:
            # 上传训练Excel文件到Kimi
            training_file_object = self.client.files.create(
                file=Path(training_excel),
                purpose="file-extract"
            )

            # 提取训练文件的文本内容
            training_content = self.client.files.content(file_id=training_file_object.id).text

            # 构建学习规则的提示词
            prompt1 = load_prompt('quality_learn_rules').format(training_content=training_content)

            messages = [{"role": "user", "content": prompt1}]

            # 调用K2模型学习规则
            resp1 = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.6,
                max_tokens=10000
            )

            # 提取学习到的规则
            rules = resp1.choices[0].message.content.strip()
            messages.append({"role": "assistant", "content": rules})

            return messages, rules, resp1.usage

        except Exception as e:
            raise Exception(f"学习非质量问题识别规则失败: {str(e)}")

    def apply_quality_rules_v1_backup(self, messages: list, test_excel: str) -> tuple:
        """备份版本：第二阶段：应用学到的规则对测试数据进行非质量问题判断"""
        try:
            # 上传测试Excel文件到Kimi
            test_file_object = self.client.files.create(
                file=Path(test_excel),
                purpose="file-extract"
            )

            # 提取测试文件的文本内容
            test_content = self.client.files.content(file_id=test_file_object.id).text

            # 读取Excel获取数据行数
            df_test = pd.read_excel(test_excel, dtype=str)
            test_row_count = len(df_test)

            # 构建应用规则的提示词
            prompt2 = load_prompt('quality_apply_rules').format(
                test_content=test_content,
                test_row_count=test_row_count
            )

            # 添加应用规则的用户请求到对话历史
            messages.append({"role": "user", "content": prompt2})

            # 调用K2模型应用规则进行判断
            resp2 = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.6,
                max_tokens=10000
            )

            # 提取判断结果
            quality_result = resp2.choices[0].message.content.strip()

            # 清理AI返回的结果，移除Markdown标记
            if quality_result.startswith('```csv'):
                quality_result = quality_result[6:]  # 移除开头的```csv
            if quality_result.endswith('```'):
                quality_result = quality_result[:-3]  # 移除结尾的```
            quality_result = quality_result.strip()

            # 确保有CSV头部
            if not quality_result.startswith('编号(维修行),是否为非产品质量问题'):
                quality_result = '编号(维修行),是否为非产品质量问题\n' + quality_result

            return quality_result, resp2.usage

        except Exception as e:
            raise Exception(f"应用非质量问题识别规则失败: {str(e)}")

    def learn_quality_rules(self, training_excel: str) -> tuple:
        """新版本：两阶段推理 - 第一阶段：学习维修问题点推理规则"""
        try:
            # 上传训练Excel文件到Kimi
            training_file_object = self.client.files.create(
                file=Path(training_excel),
                purpose="file-extract"
            )

            # 提取训练文件的文本内容
            training_content = self.client.files.content(file_id=training_file_object.id).text

            # 使用质量工单填充的学习提示词
            prompt1 = load_prompt('excel_learn_rules').format(training_content=training_content)

            messages = [{"role": "user", "content": prompt1}]

            # 调用K2模型学习规则
            resp1 = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.6,
                max_tokens=10000
            )

            # 提取学习到的规则
            rules = resp1.choices[0].message.content.strip()
            messages.append({"role": "assistant", "content": rules})

            return messages, rules, resp1.usage

        except Exception as e:
            raise Exception(f"学习维修问题点推理规则失败: {str(e)}")

    def apply_quality_rules(self, messages: list, test_excel: str) -> tuple:
        """新版本：两阶段推理 - 第二阶段：应用规则并提取非质量问题"""
        try:
            # 上传测试Excel文件到Kimi
            test_file_object = self.client.files.create(
                file=Path(test_excel),
                purpose="file-extract"
            )

            # 提取测试文件的文本内容
            test_content = self.client.files.content(file_id=test_file_object.id).text

            # 读取Excel获取数据行数
            df_test = pd.read_excel(test_excel, dtype=str)
            test_row_count = len(df_test)

            # 第一步：使用质量工单填充的应用提示词，推理出维修问题点
            prompt2 = load_prompt('excel_apply_rules').format(
                test_content=test_content,
                test_row_count=test_row_count
            )

            messages.append({"role": "user", "content": prompt2})

            # 调用K2模型推理维修问题点
            resp2 = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.6,
                max_tokens=10000
            )

            # 提取维修问题点推理结果
            maintenance_result = resp2.choices[0].message.content.strip()

            # 清理结果格式
            if maintenance_result.startswith('```csv'):
                maintenance_result = maintenance_result[6:]
            if maintenance_result.endswith('```'):
                maintenance_result = maintenance_result[:-3]
            maintenance_result = maintenance_result.strip()

            # 第二步：基于推理出的维修问题点，提取非质量问题
            quality_prompt = f"""
根据刚才推理出的维修问题点结果，提取"是否为非产品质量问题"的信息。

推理结果：
{maintenance_result}

任务：
1. 从推理结果中提取"维修问题点"列
2. 如果维修问题点是"非产品质量问题"，则标注为"非产品质量问题"
3. 如果维修问题点是其他类型（如滤芯堵塞、漏水、TDS值调整等），则标注为"否"
4. 输出格式：编号(维修行),是否为非产品质量问题

请仅输出CSV格式结果：

编号(维修行),是否为非产品质量问题
"""

            messages.append({"role": "assistant", "content": maintenance_result})
            messages.append({"role": "user", "content": quality_prompt})

            # 调用K2模型提取非质量问题信息
            resp3 = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,  # 降低温度，提高一致性
                max_tokens=5000
            )

            # 提取最终结果
            quality_result = resp3.choices[0].message.content.strip()

            # 清理AI返回的结果
            if quality_result.startswith('```csv'):
                quality_result = quality_result[6:]
            if quality_result.endswith('```'):
                quality_result = quality_result[:-3]
            quality_result = quality_result.strip()

            # 确保有CSV头部
            if not quality_result.startswith('编号(维修行),是否为非产品质量问题'):
                quality_result = '编号(维修行),是否为非产品质量问题\n' + quality_result

            # 合并token使用情况
            total_usage = {
                'stage1_learn': resp2.usage.model_dump() if hasattr(resp2.usage, 'model_dump') else (resp2.usage.dict() if hasattr(resp2.usage, 'dict') else str(resp2.usage)),
                'stage2_extract': resp3.usage.model_dump() if hasattr(resp3.usage, 'model_dump') else (resp3.usage.dict() if hasattr(resp3.usage, 'dict') else str(resp3.usage))
            }

            return quality_result, total_usage

        except Exception as e:
            raise Exception(f"两阶段推理失败: {str(e)}")

# 全局Excel处理器实例
processor = None

# ==================== 集成系统主页 ====================

@app.route('/')
def index():
    """集成系统主页 - 显示两个子系统入口"""
    return render_template('index.html')

# ==================== 制图检测路由 ====================

@app.route('/drawing')
def drawing_index():
    """制图检测系统主页"""
    return render_template('drawing_index.html')

@app.route('/drawing/detection')
def drawing_detection():
    """制图检测页面 - 上传PDF并进行检测"""
    return render_template('drawing_detection.html')

@app.route('/drawing/textbook')
def drawing_textbook():
    """制图规范教材 - 直接下载PDF文件"""
    textbook_file = "data/机械制图教材 (1).pdf"
    if os.path.exists(textbook_file):
        return send_file(textbook_file, as_attachment=False)
    else:
        return jsonify({'error': '教材文件不存在'}), 404

@app.route('/drawing/history')
def drawing_history():
    """制图检测历史记录页面"""
    return render_template('drawing_history.html')

@app.route('/drawing/api/history')
def drawing_get_history():
    """获取制图检测历史记录API"""
    try:
        history_records = get_detection_history()
        return jsonify({
            'success': True,
            'records': history_records,
            'total': len(history_records)
        })
    except Exception as e:
        return jsonify({'error': f'获取历史记录失败: {str(e)}'}), 500

@app.route('/drawing/api/history/<record_id>')
def drawing_get_history_detail(record_id):
    """获取历史记录详情"""
    try:
        history_records = get_detection_history()

        # 查找指定ID的记录
        target_record = None
        for record in history_records:
            if record['id'] == record_id:
                target_record = record
                break

        if not target_record:
            return jsonify({'error': '历史记录不存在'}), 404

        return jsonify({
            'success': True,
            'record': target_record
        })

    except Exception as e:
        return jsonify({'error': f'获取历史记录详情失败: {str(e)}'}), 500



@app.route('/drawing/upload', methods=['POST'])
def drawing_upload_file():
    """制图检测 - PDF文件上传接口"""
    if 'file' not in request.files:
        return jsonify({'error': '没有选择文件'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': '只支持PDF文件格式'}), 400

    # 保存文件到uploads目录
    filename = f"{int(time.time())}_{file.filename}"  # 添加时间戳避免重名
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    return jsonify({
        'success': True,
        'filename': filename,
        'message': 'PDF文件上传成功',
        'preview_url': f'/drawing/preview/{filename}'  # 返回预览URL
    })

@app.route('/drawing/inspect', methods=['POST'])
def drawing_inspect():
    """制图检测 - AI智能检测接口"""
    data = request.get_json()
    filename = data.get('filename')

    if not filename:
        return jsonify({'error': '缺少文件名参数'}), 400

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    if not os.path.exists(filepath):
        return jsonify({'error': '文件不存在'}), 404

    # 调用AI检测函数
    result = inspect_drawing_api(filepath)

    # 如果检测成功，保存到历史记录
    if 'error' not in result and result.get('success'):
        save_detection_history(
            filename=filename,
            conclusion=result.get('conclusion', '未知'),
            detailed_report=result.get('detailed_report', ''),
            timestamp=result.get('timestamp', time.strftime('%Y-%m-%d %H:%M:%S'))
        )

    # 检测完成后清理临时文件
    try:
        os.remove(filepath)
    except:
        pass  # 忽略删除失败

    if 'error' in result:
        return jsonify(result), 500

    return jsonify(result)

@app.route('/drawing/preview/<filename>')
def drawing_preview_pdf(filename):
    """PDF预览接口 - 简化版本"""
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    if not os.path.exists(filepath):
        return jsonify({'error': '文件不存在'}), 404

    # 尝试转换PDF为图片
    image_data = convert_pdf_to_image(filepath)

    if image_data:
        return jsonify({
            'success': True,
            'image_data': image_data,
            'message': 'PDF预览生成成功',
            'real_preview': True
        })
    else:
        # 使用占位符
        placeholder_data = create_placeholder_image(filename)
        return jsonify({
            'success': True,
            'image_data': placeholder_data,
            'message': 'PDF预览使用占位符',
            'real_preview': False
        })



@app.route('/drawing/download-report', methods=['POST'])
def drawing_download_report():
    """下载检测报告"""
    try:
        data = request.get_json()
        conclusion = data.get('conclusion', '未知')
        content = data.get('content', '')
        timestamp = data.get('timestamp', time.strftime('%Y-%m-%d %H:%M:%S'))
        format_type = data.get('format', 'txt')

        if format_type == 'txt':
            # 生成TXT格式报告
            report_content = f"""机械制图规范检测报告
{'='*50}

检测结论: {conclusion}
检测时间: {timestamp}

详细分析:
{'-'*30}
{content}

{'='*50}
报告生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}
系统版本: 大模型智能检测系统 v1.0
"""

            # 创建临时文件
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8')
            temp_file.write(report_content)
            temp_file.close()

            return send_file(
                temp_file.name,
                as_attachment=True,
                download_name=f"制图检测报告_{time.strftime('%Y%m%d_%H%M%S')}.txt",
                mimetype='text/plain'
            )

        else:
            return jsonify({'error': '不支持的文件格式'}), 400

    except Exception as e:
        return jsonify({'error': f'生成报告失败: {str(e)}'}), 500

# ==================== Excel工单检测路由 ====================

@app.route('/excel')
def excel_index():
    """Excel检测系统主页 - 显示两个子模块"""
    return render_template('excel_main.html')

@app.route('/excel/detection')
def excel_detection():
    """Excel检测页面"""
    return render_template('excel_index.html')

@app.route('/excel/history')
def excel_history():
    """Excel处理历史记录页面"""
    return render_template('excel_history.html')

@app.route('/excel/quality-check')
def excel_quality_check():
    """非质量问题点检测页面"""
    return render_template('excel_quality_detection.html')

@app.route('/excel/quality-check/result')
def excel_quality_result():
    """非质量问题检测结果页面"""
    return render_template('excel_quality_result.html')

@app.route('/excel/format-standard')
def excel_format_standard():
    """工单文件标准格式主页"""
    return render_template('excel_format_standard.html')

@app.route('/excel/format-standard/detection')
def excel_format_detection():
    """工单检测格式详情页面"""
    source = request.args.get('source', 'standard')  # 默认来源是标准格式页面
    return render_template('excel_format_detection.html', source=source)

@app.route('/excel/format-standard/quality')
def excel_format_quality():
    """非质量问题检测格式详情页面"""
    source = request.args.get('source', 'standard')  # 默认来源是标准格式页面
    return render_template('excel_format_quality.html', source=source)

@app.route('/excel/result')
def excel_result_page():
    """Excel检测结果页面"""
    return render_template('excel_result.html')

@app.route('/excel/upload', methods=['POST'])
def excel_upload_file():
    """上传Excel文件"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': '未选择文件'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '未选择文件'}), 400

        if not file.filename.lower().endswith(('.xlsx', '.xls')):
            return jsonify({'error': '请上传Excel文件(.xlsx或.xls)'}), 400

        # 保存上传的文件 - 使用原始文件名
        original_filename = file.filename  # 保存原始文件名
        timestamp = str(int(time.time()))
        # 直接使用原始文件名，不使用secure_filename
        filename = f"{timestamp}_{original_filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # 验证Excel文件
        try:
            df = pd.read_excel(filepath)
            rows, cols = df.shape
        except Exception as e:
            os.remove(filepath)
            return jsonify({'error': f'Excel文件格式错误: {str(e)}'}), 400

        return jsonify({
            'success': True,
            'filename': filename,
            'original_filename': original_filename,
            'rows': rows,
            'columns': cols,
            'message': f'文件上传成功，包含{rows}行{cols}列数据'
        })

    except Exception as e:
        return jsonify({'error': f'上传失败: {str(e)}'}), 500

@app.route('/excel/process', methods=['POST'])
def excel_process_inference():
    """执行K2推理处理"""
    global processor

    try:
        data = request.get_json()
        filename = data.get('filename')

        if not filename:
            return jsonify({'error': '未指定文件'}), 400

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(filepath):
            return jsonify({'error': '文件不存在'}), 404

        # 初始化处理器
        if not processor:
            processor = Processor()

        # 固定的训练工单路径（写死在后端）

        training_file = "data/训练工单250条.xlsx"

        # 检查训练文件是否存在
        if not os.path.exists(training_file):
            return jsonify({'error': f'训练工单文件不存在: {training_file}'}), 500

        # 第一步：使用固定的训练工单学习规则
        messages, rules, usage1 = processor.learn_rules(training_file)

        # 第二步：对用户上传的文件应用规则进行填充
        filled_result, usage2 = processor.apply_rules(messages, filepath)

        # 保存CSV结果
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        csv_filename = f"excel_result_{timestamp}.csv"
        csv_filepath = os.path.join(app.config['UPLOAD_FOLDER'], csv_filename)

        with open(csv_filepath, 'w', encoding='utf-8') as f:
            f.write(filled_result)

        # 转换为Excel
        excel_filename = f"excel_result_{timestamp}.xlsx"
        excel_filepath = os.path.join(app.config['UPLOAD_FOLDER'], excel_filename)

        # 读取CSV并转换为Excel
        df_result = pd.read_csv(csv_filepath, dtype=str)
        df_result.to_excel(excel_filepath, index=False)

        # 保存到历史记录 - 从请求中获取原始文件名
        original_filename = data.get('original_filename')
        if not original_filename:
            # 如果没有提供原始文件名，尝试从文件名中提取
            original_filename = filename.split('_', 1)[1] if '_' in filename else filename

        save_excel_history(
            filename=excel_filename,
            original_filename=original_filename,
            rows_processed=len(df_result),
            timestamp=time.strftime('%Y-%m-%d %H:%M:%S')
        )

        return jsonify({
            'success': True,
            'message': '处理完成',
            'excel_filename': excel_filename,
            'csv_filename': csv_filename,
            'rows_processed': len(df_result)
        })

    except Exception as e:
        return jsonify({'error': f'处理失败: {str(e)}'}), 500

@app.route('/excel/download/<filename>')
def excel_download_file(filename):
    """下载结果文件"""
    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(filepath):
            return jsonify({'error': '文件不存在'}), 404

        return send_file(filepath, as_attachment=True)

    except Exception as e:
        return jsonify({'error': f'下载失败: {str(e)}'}), 500

@app.route('/excel/get-original-data/<filename>')
def excel_get_original_data(filename):
    """获取原始上传文件的数据"""
    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(filepath):
            return jsonify({'error': '文件不存在'}), 404

        # 读取Excel文件
        df = pd.read_excel(filepath, dtype=str)
        df = df.fillna('')  # 将NaN替换为空字符串

        # 转换为JSON格式
        data = df.to_dict('records')
        columns = df.columns.tolist()

        return jsonify({
            'success': True,
            'data': data,
            'columns': columns,
            'rows': len(data)
        })

    except Exception as e:
        return jsonify({'error': f'读取原始数据失败: {str(e)}'}), 500

@app.route('/excel/get-result-data/<filename>')
def excel_get_result_data(filename):
    """获取填充结果数据"""
    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(filepath):
            return jsonify({'error': '文件不存在'}), 404

        # 读取CSV文件
        df = pd.read_csv(filepath, dtype=str)
        df = df.fillna('')  # 将NaN替换为空字符串

        # 转换为JSON格式
        data = df.to_dict('records')
        columns = df.columns.tolist()

        return jsonify({
            'success': True,
            'data': data,
            'columns': columns,
            'rows': len(data)
        })

    except Exception as e:
        return jsonify({'error': f'读取结果数据失败: {str(e)}'}), 500

@app.route('/excel/api/history')
def excel_get_history():
    """获取Excel处理历史记录API"""
    try:
        history_records = get_excel_history()
        return jsonify({
            'success': True,
            'records': history_records,
            'total': len(history_records)
        })
    except Exception as e:
        return jsonify({'error': f'获取历史记录失败: {str(e)}'}), 500

@app.route('/excel/api/history/<record_id>')
def excel_get_history_detail(record_id):
    """获取Excel历史记录详情"""
    try:
        history_records = get_excel_history()

        # 查找指定ID的记录
        target_record = None
        for record in history_records:
            if record['id'] == record_id:
                target_record = record
                break

        if not target_record:
            return jsonify({'error': '历史记录不存在'}), 404

        return jsonify({
            'success': True,
            'record': target_record
        })

    except Exception as e:
        return jsonify({'error': f'获取历史记录详情失败: {str(e)}'}), 500

@app.route('/excel/quality-upload', methods=['POST'])
def excel_quality_upload():
    """非质量问题检测文件上传"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': '未选择文件'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '未选择文件'}), 400

        if not file.filename.lower().endswith(('.xlsx', '.xls')):
            return jsonify({'error': '请上传Excel文件(.xlsx或.xls)'}), 400

        # 保存上传的文件 - 使用原始文件名
        original_filename = file.filename
        timestamp = str(int(time.time()))
        # 直接使用原始文件名，不使用secure_filename
        filename = f"{timestamp}_{original_filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # 验证Excel文件
        try:
            df = pd.read_excel(filepath)
            rows, cols = df.shape
        except Exception as e:
            os.remove(filepath)
            return jsonify({'error': f'Excel文件格式错误: {str(e)}'}), 400

        return jsonify({
            'success': True,
            'filename': filename,
            'original_filename': original_filename,
            'rows': rows,
            'columns': cols,
            'message': f'文件上传成功，包含{rows}行{cols}列数据'
        })

    except Exception as e:
        return jsonify({'error': f'上传失败: {str(e)}'}), 500

@app.route('/excel/quality-process', methods=['POST'])
def excel_quality_process():
    """执行非质量问题检测处理"""
    global processor

    try:
        data = request.get_json()
        filename = data.get('filename')

        if not filename:
            return jsonify({'error': '未指定文件'}), 400

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(filepath):
            return jsonify({'error': '文件不存在'}), 404

        # 初始化处理器
        if not processor:
            processor = Processor()

        # 固定的训练工单路径
        training_file = "训练工单-非质量问题点.xlsx"

        # 检查训练文件是否存在
        if not os.path.exists(training_file):
            return jsonify({'error': f'训练工单文件不存在: {training_file}'}), 500

        # 检查是否使用备份版本（用于回退）
        use_backup = data.get('use_backup_version', False)

        if use_backup:
            # 使用备份版本（原始方法）
            messages, rules, usage1 = processor.learn_quality_rules_v1_backup(training_file)
            quality_result, usage2 = processor.apply_quality_rules_v1_backup(messages, filepath)
        else:
            # 使用新的两阶段推理法
            messages, rules, usage1 = processor.learn_quality_rules(training_file)
            quality_result, usage2 = processor.apply_quality_rules(messages, filepath)

        # 保存CSV结果
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        csv_filename = f"quality_result_{timestamp}.csv"
        csv_filepath = os.path.join(app.config['UPLOAD_FOLDER'], csv_filename)

        with open(csv_filepath, 'w', encoding='utf-8') as f:
            f.write(quality_result)

        # 转换为Excel
        excel_filename = f"quality_result_{timestamp}.xlsx"
        excel_filepath = os.path.join(app.config['UPLOAD_FOLDER'], excel_filename)

        # 读取CSV并转换为Excel
        df_result = pd.read_csv(csv_filepath, dtype=str)
        df_result.to_excel(excel_filepath, index=False)

        # 保存到历史记录
        original_filename = data.get('original_filename')
        if not original_filename:
            original_filename = filename.split('_', 1)[1] if '_' in filename else filename

        save_excel_history(
            filename=excel_filename,
            original_filename=original_filename,
            rows_processed=len(df_result),
            timestamp=time.strftime('%Y-%m-%d %H:%M:%S')
        )

        return jsonify({
            'success': True,
            'message': '非质量问题检测完成',
            'excel_filename': excel_filename,
            'csv_filename': csv_filename,
            'rows_processed': len(df_result)
        })

    except Exception as e:
        return jsonify({'error': f'处理失败: {str(e)}'}), 500

@app.route('/excel/download-template/<template_type>')
def download_template(template_type):
    """下载Excel模板文件"""
    try:
        if template_type == 'detection':
            # 工单检测模板
            template_data = {
                '编号(维修行)': ['RL0011191618', 'RL0011191619', 'RL0011191620'],
                '来电内容(维修行)': ['净水器不出水', '水质TDS值偏高', '机器漏水'],
                '现场诊断故障现象(维修行)': ['现场检测发现增压泵不工作', '检测RO滤芯已堵塞', '发现水路接头松动'],
                '故障部位(维修行)': ['增压泵', '滤芯', '水路接头'],
                '故障件名称(维修行)': ['增压泵', 'RO滤芯', '水路接头'],
                '处理方案简述(维修行)': ['更换增压泵', '更换RO滤芯', '紧固水路接头'],
                '故障类别(维修行)': ['电气类', '滤芯类', '水路类'],
                '维修问题点': ['', '', ''],  # 待填充
                '二级问题点': ['', '', '']   # 待填充
            }
            filename = '工单检测标准模板.xlsx'

        elif template_type == 'quality':
            # 非质量问题检测模板
            template_data = {
                '编号(维修行)': ['RL0011191618', 'RL0011191619', 'RL0011191620'],
                '来电内容(维修行)': ['净水器不出水', '机器漏水', '水质TDS值偏高'],
                '现场诊断故障现象(维修行)': ['现场检测发现增压泵不工作', '现场检测机器各方面正常', '检测RO滤芯已堵塞'],
                '故障部位(维修行)': ['增压泵', '外部管路', '滤芯'],
                '故障件名称(维修行)': ['增压泵', '三通角阀', 'RO滤芯'],
                '处理方案简述(维修行)': ['更换增压泵', '客户工程三通角阀漏水，非我司机器设备', '更换RO滤芯'],
                '故障类别(维修行)': ['电气类', '安装类', '滤芯类'],
                '是否为非产品质量问题': ['', '', '']  # 待填充
            }
            filename = '非质量问题检测标准模板.xlsx'
        else:
            return jsonify({'error': '无效的模板类型'}), 400

        # 创建DataFrame并保存为Excel
        df = pd.DataFrame(template_data)

        # 使用内存中的Excel文件
        from io import BytesIO
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='工单数据')

        output.seek(0)

        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        return jsonify({'error': f'下载模板失败: {str(e)}'}), 500

# ==================== 通用路由 ====================

@app.route('/health')
def health():
    """健康检查"""
    return jsonify({'status': 'ok', 'message': '大模型智能检测系统运行正常'})

if __name__ == '__main__':
    print("==== 大模型智能检测系统 ====")
    print("访问地址: http://localhost:5000")


    app.run(debug=False, host='0.0.0.0', port=5000)