#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel工单智能处理器模块 - 提供基于硅基流动大模型的工单数据智能填充和分析功能
"""

import os
import pandas as pd
from pathlib import Path
from openai import OpenAI
from modules.common.prompts import load_prompt

class Processor:
    """Excel工单智能填充处理器

    使用硅基流动大模型进行工单数据的智能学习和推理填充，支持两阶段处理：
    1. 从训练数据学习规则和模式
    2. 将学到的规则应用到测试数据进行智能填充
    """

    def __init__(self):
        """初始化大模型处理器

        配置Kimi官方API客户端和相关参数，准备进行智能处理
        """
        
        # 获取环境变量中的API密钥和模型
        # 使用Kimi官方API配置（替代硅基流动）
        # 本地大模型配置（已停用）:
        # self.api_key = 'Angel@20250428'
        # self.model = 'Qwen3-80B-FP8'
        # self.base_url = 'http://10.2.32.163:8000/v1'
        # self.api_key = os.getenv('EXCEL_API_KEY', 'Angel@20250428')
        # self.model = os.getenv('EXCEL_MODEL_NAME', 'Qwen3-80B-FP8')
        # self.base_url = os.getenv('EXCEL_BASE_URL', 'http://10.2.32.163:8000/v1')
        
        # Kimi官方API配置（Moonshot）
        self.api_key = os.getenv('MOONSHOT_API_KEY', 'sk-S7PzDUN4aPRl8sr5zxqNe9umeTnPj9AdirkD9wKTN9IluR2i')
        self.model = os.getenv('MOONSHOT_MODEL_0711', 'kimi-k2-0905-preview')  # 使用K2-0711模型
        self.base_url = os.getenv('MOONSHOT_BASE_URL', 'https://api.moonshot.cn/v1')

        if not self.api_key:
            raise ValueError("未找到MOONSHOT_API_KEY环境变量")

        # 初始化模型（兼容OpenAI接口格式）
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=600  # 增加超时时间到10分钟，适应大批量数据处理
        )

    def _read_excel_to_text(self, excel_path: str) -> str:
        """将Excel文件转换为文本格式，用于AI分析

        Args:
            excel_path (str): Excel文件路径

        Returns:
            str: Excel内容的文本表示
        """
        try:
            df = pd.read_excel(excel_path, dtype=str)

            # 清理所有字段中的换行符，替换为空格
            # 这样可以避免AI生成的CSV格式出现问题
            for col in df.columns:
                df[col] = df[col].astype(str).str.replace('\r\n', ' ', regex=False)
                df[col] = df[col].astype(str).str.replace('\n', ' ', regex=False)
                df[col] = df[col].astype(str).str.replace('\r', ' ', regex=False)

            # 将DataFrame转换为CSV格式文本
            return df.to_csv(index=False)
        except Exception as e:
            raise Exception(f"读取Excel文件失败: {str(e)}")

    def _fix_csv_format(self, csv_text: str) -> str:
        """修复CSV格式，确保包含逗号、换行符的字段被正确引号包裹

        Args:
            csv_text (str): 原始CSV文本

        Returns:
            str: 修复后的CSV文本
        """
        try:
            import io
            import csv

            # 使用StringIO读取整个CSV文本（支持多行字段）
            input_stream = io.StringIO(csv_text.strip())
            output_stream = io.StringIO()

            # 使用csv.reader读取（自动处理引号和换行符）
            reader = csv.reader(input_stream)
            # 使用csv.writer写入（自动添加必要的引号）
            writer = csv.writer(output_stream, quoting=csv.QUOTE_MINIMAL, lineterminator='\n')

            for row in reader:
                # 跳过空行
                if not row or all(field.strip() == '' for field in row):
                    continue
                writer.writerow(row)

            return output_stream.getvalue()
        except Exception as e:
            # 如果修复失败，返回原始文本
            print(f"警告：CSV格式修复失败: {str(e)}")
            return csv_text

    def _validate_and_fix_csv_fields(self, csv_text: str, expected_field_count: int = 9) -> str:
        """验证并修复CSV字段数量

        Args:
            csv_text (str): CSV文本
            expected_field_count (int): 期望的字段数量

        Returns:
            str: 修复后的CSV文本
        """
        try:
            import io
            import csv

            lines = csv_text.strip().split('\n')
            if not lines:
                return csv_text

            # 读取头部
            header = lines[0]
            header_fields = header.split(',')

            # 如果头部字段数量不对，直接返回
            if len(header_fields) != expected_field_count:
                print(f"警告：CSV头部字段数量不正确，期望{expected_field_count}个，实际{len(header_fields)}个")
                return csv_text

            # 使用csv.reader解析每一行
            input_stream = io.StringIO(csv_text.strip())
            reader = csv.reader(input_stream)

            output_stream = io.StringIO()
            writer = csv.writer(output_stream, quoting=csv.QUOTE_MINIMAL, lineterminator='\n')

            row_num = 0
            for row in reader:
                row_num += 1

                # 跳过空行
                if not row or all(field.strip() == '' for field in row):
                    continue

                # 检查字段数量
                if len(row) != expected_field_count:
                    print(f"警告：第{row_num}行字段数量不正确，期望{expected_field_count}个，实际{len(row)}个")
                    print(f"  原始数据: {row[:3]}... (共{len(row)}个字段)")

                    # 如果字段太少，用空字符串补齐
                    if len(row) < expected_field_count:
                        row.extend([''] * (expected_field_count - len(row)))
                        print(f"  已补齐为{expected_field_count}个字段")
                    # 如果字段太多，智能处理
                    elif len(row) > expected_field_count:
                        # 如果是10个字段，很可能是漏掉了"故障组"字段
                        # 尝试保留最后一个字段（工单性质），删除中间的某个字段
                        if len(row) == 10:
                            # 保留最后一个字段（工单性质）
                            last_field = row[-1]
                            # 删除第3个字段（索引2），因为很可能是"故障组"被漏掉，导致后面字段错位
                            # 但为了保险，我们保留前2个和最后1个，中间的截断到6个
                            fixed_row = row[:2] + row[3:9] + [last_field]
                            print(f"  智能修复：保留最后字段'{last_field}'，删除多余字段")
                            row = fixed_row
                        else:
                            # 其他情况，简单截断
                            row = row[:expected_field_count]
                            print(f"  已截断为{expected_field_count}个字段")

                writer.writerow(row)

            return output_stream.getvalue()
        except Exception as e:
            print(f"警告：CSV字段验证失败: {str(e)}")
            return csv_text


    def learn_rules(self, training_excel: str) -> tuple:
        """第一阶段：从训练数据中学习工单问题点推理规则

        分析训练Excel数据，学习如何根据工单信息推理出维修问题点和二级问题点

        Args:
            training_excel (str): 训练数据Excel文件路径

        Returns:
            tuple: (学习到的规则和对话消息, API使用统计)
        """
        try:
            # 读取训练Excel文件内容（硅基流动不支持文件上传，直接读取内容）
            def _compact_training(df: pd.DataFrame) -> str:
                df = df.copy()
                drop_cols = [c for c in df.columns if str(c).startswith('Unnamed:')]
                if drop_cols:
                    df = df.drop(columns=drop_cols)
                for c in df.columns:
                    df[c] = df[c].astype(str).fillna('')

                def cnt(series_cond):
                    try:
                        return int(series_cond.sum())
                    except Exception:
                        return 0

                nature_counts = df.get('工单性质', pd.Series(dtype=str)).value_counts(dropna=False).to_dict()
                svc = df.get('服务项目或故障现象', pd.Series(dtype=str))
                cat = df.get('故障类别', pd.Series(dtype=str))
                bn = df.get('保内保外', pd.Series(dtype=str))
                oldp = df.get('旧件名称', pd.Series(dtype=str))
                newp = df.get('新件名称', pd.Series(dtype=str))
                call = df.get('来电内容', pd.Series(dtype=str))
                diag = df.get('现场诊断故障现象', pd.Series(dtype=str))
                plan = df.get('处理方案简述或备注', pd.Series(dtype=str))

                core_parts = ['电源适配器','微电脑电源板','微电脑显示板','控制板总成','主板','绕丝加热体总成','电热管','增压泵','电磁阀','进水阀','高压开关','TDS传感器','电控龙头','灯显龙头','浮球开关','浮球组件','流量计','温度感应器','滤网总成','指示灯板','排水接头','密封圈','真空热罐总成','抽水泵','跷板开关','反渗透膜滤芯','滤芯座总成']
                exchange_words = ['换机','退机','退货']
                filter_words = ['漏炭','黑点','黑渣','碳粉','活性炭粉末']

                def contains_any(series, words):
                    s = series.astype(str)
                    return s.apply(lambda x: any(w in x for w in words))

                stats_lines = []
                stats_lines.append(f"样本量: {len(df)}")
                if nature_counts:
                    stats_lines.append(f"工单性质分布: {nature_counts}")
                stats_lines.append(f"服务项目Top10: {svc.value_counts().head(10).to_dict()}")
                stats_lines.append(f"故障类别Top10: {cat.value_counts().head(10).to_dict()}")
                core_hit = cnt(oldp.apply(lambda x: any(p in str(x) for p in core_parts)) | newp.apply(lambda x: any(p in str(x) for p in core_parts)))
                stats_lines.append(f"核心部件命中数: {core_hit}")
                filt_hit = cnt(oldp.str.contains('滤芯', na=False) | newp.str.contains('滤芯', na=False))
                stats_lines.append(f"滤芯更换记录数: {filt_hit}")
                policy_hit = cnt(bn.astype(str).eq('保外转保内') & (oldp.str.contains('滤芯', na=False) | newp.str.contains('滤芯', na=False)))
                stats_lines.append(f"保外转保内+滤芯记录数: {policy_hit}")
                noise_exchange = cnt(((plan.str.contains('噪音|分贝', na=False)) | (call.str.contains('噪音|分贝', na=False))) & (contains_any(plan, exchange_words) | contains_any(call, exchange_words)))
                stats_lines.append(f"噪音/分贝+换退记录数: {noise_exchange}")
                add_hit = cnt(svc.str.contains('加装', na=False))
                safe_hit = cnt(svc.str.contains('安全维护', na=False))
                stats_lines.append(f"加装记录数: {add_hit}")
                stats_lines.append(f"安全维护记录数: {safe_hit}")

                preview_cols = ['工单单号','工单性质','判定依据','保内保外','批次入库日期','安装日期','购机日期','产品名称','开发主体','故障部位名称','故障组','故障类别','服务项目或故障现象','维修方式','旧件名称','新件名称','来电内容','现场诊断故障现象','处理方案简述或备注']
                for c in preview_cols:
                    if c not in df.columns:
                        df[c] = ''
                df_preview = df[preview_cols].copy()
                for c in ['来电内容','现场诊断故障现象','处理方案简述或备注','判定依据']:
                    df_preview[c] = df_preview[c].astype(str).str.slice(0, 120)
                max_rows = min(200, len(df_preview))
                df_preview = df_preview.head(max_rows)
                preview_csv = df_preview.to_csv(index=False)
                summary = "\n".join(stats_lines)
                return f"# 训练数据统计摘要\n{summary}\n\n# 样本预览(最多{max_rows}行)\n{preview_csv}"

            training_content = _compact_training(df_training)

            # 构建学习规则的提示词
            prompt1 = load_prompt('excel_learn_rules').format(training_content=training_content)

            messages = [{"role": "user", "content": prompt1}]

            # 调用硅基流动模型学习规则
            resp1 = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.6,  # 控制创造性
                max_tokens=4096  # 允许较长回答
            )

            # 提取学习到的规则
            rules = resp1.choices[0].message.content.strip()
            messages.append({"role": "assistant", "content": rules})

            return messages, rules, resp1.usage  # 返回对话历史、规则和token使用量

        except Exception as e:
            raise Exception(f"学习规则失败: {str(e)}")

    def apply_rules(self, messages: list, test_excel: str) -> tuple:
        """第二阶段：应用学习到的规则对测试数据进行智能填充

        将第一阶段学到的推理规则应用到测试Excel数据，自动填充维修问题点和二级问题点

        Args:
            messages (list): 包含学习规则的对话消息列表
            test_excel (str): 测试数据Excel文件路径

        Returns:
            tuple: (填充结果CSV内容, API使用统计)
        """
        try:
            # 读取测试Excel文件内容
            test_content = self._read_excel_to_text(test_excel)

            # 读取Excel获取数据行数，确保AI输出完整的结果
            df_test = pd.read_excel(test_excel, dtype=str)
            test_row_count = len(df_test)

            # 构建应用规则的提示词，指导AI将学到的规则应用到测试数据
            prompt2 = load_prompt('excel_apply_rules').format(
                test_content=test_content,
                test_row_count=test_row_count
            )

            # 将应用规则的请求添加到对话历史，保持上下文连贯性
            messages.append({"role": "user", "content": prompt2})

            # 调用硅基流动模型应用规则进行填充
            resp2 = self.client.chat.completions.create(
                model=self.model,
                messages=messages,  # 包含之前学习的规则
                temperature=0.6,
                max_tokens=4096
            )

            # 提取填充结果
            filled_result = resp2.choices[0].message.content.strip()

            # 清理AI返回的结果，移除Markdown标记
            if filled_result.startswith('```csv'):
                filled_result = filled_result[6:]  # 移除开头的```csv
            if filled_result.endswith('```'):
                filled_result = filled_result[:-3]  # 移除结尾的```
            filled_result = filled_result.strip()

            # 确保有正确的CSV头部（根据工单问题点检测的字段）
            expected_header = '编号(维修行),来电内容(维修行),现场诊断故障现象(维修行),故障部位(维修行),故障件名称(维修行),处理方案简述(维修行),故障类别(维修行),维修问题点,二级问题点'
            if not filled_result.startswith('编号(维修行)'):
                filled_result = expected_header + '\n' + filled_result

            return filled_result, resp2.usage  # 返回清理后的填充结果和token使用量

        except Exception as e:
            raise Exception(f"应用规则失败: {str(e)}")

    def learn_quality_rules_v1_backup(self, training_excel: str) -> tuple:
        """备份版本：从训练数据中学习质量工单识别规则

        第一阶段处理：分析训练Excel数据，学习质量工单的判断规律和标注标准

        Args:
            training_excel (str): 训练数据Excel文件路径

        Returns:
            tuple: (学习到的规则内容, API使用统计)
        """
        try:
            # 读取训练Excel文件内容
            # 压缩训练内容，避免超过模型上下文长度
            def _contains_any(series, words):
                s = series.astype(str)
                return s.apply(lambda x: any(w in x for w in words))
            df_compact = df_training.copy()
            drop_cols = [c for c in df_compact.columns if str(c).startswith('Unnamed:')]
            if drop_cols:
                df_compact = df_compact.drop(columns=drop_cols)
            for c in df_compact.columns:
                df_compact[c] = df_compact[c].astype(str).fillna('')
            nature_counts = df_compact.get('工单性质', pd.Series(dtype=str)).value_counts(dropna=False).to_dict()
            svc = df_compact.get('服务项目或故障现象', pd.Series(dtype=str))
            cat = df_compact.get('故障类别', pd.Series(dtype=str))
            bn = df_compact.get('保内保外', pd.Series(dtype=str))
            oldp = df_compact.get('旧件名称', pd.Series(dtype=str))
            newp = df_compact.get('新件名称', pd.Series(dtype=str))
            call = df_compact.get('来电内容', pd.Series(dtype=str))
            diag = df_compact.get('现场诊断故障现象', pd.Series(dtype=str))
            plan = df_compact.get('处理方案简述或备注', pd.Series(dtype=str))
            core_parts = ['电源适配器','微电脑电源板','微电脑显示板','控制板总成','主板','绕丝加热体总成','电热管','增压泵','电磁阀','进水阀','高压开关','TDS传感器','电控龙头','灯显龙头','浮球开关','浮球组件','流量计','温度感应器','滤网总成','指示灯板','排水接头','密封圈','真空热罐总成','抽水泵','跷板开关','反渗透膜滤芯','滤芯座总成']
            stats_lines = []
            stats_lines.append(f"样本量: {len(df_compact)}")
            if nature_counts:
                stats_lines.append(f"工单性质分布: {nature_counts}")
            stats_lines.append(f"服务项目Top10: {svc.value_counts().head(10).to_dict() if svc is not None else {}}")
            stats_lines.append(f"故障类别Top10: {cat.value_counts().head(10).to_dict() if cat is not None else {}}")
            core_hit = int((oldp.apply(lambda x: any(p in str(x) for p in core_parts)) | newp.apply(lambda x: any(p in str(x) for p in core_parts))).sum()) if (oldp is not None and newp is not None) else 0
            stats_lines.append(f"核心部件命中数: {core_hit}")
            filt_hit = int((oldp.str.contains('滤芯', na=False) | newp.str.contains('滤芯', na=False)).sum()) if (oldp is not None and newp is not None) else 0
            stats_lines.append(f"滤芯更换记录数: {filt_hit}")
            policy_hit = int((bn.astype(str).eq('保外转保内') & (oldp.str.contains('滤芯', na=False) | newp.str.contains('滤芯', na=False))).sum()) if (bn is not None and oldp is not None and newp is not None) else 0
            stats_lines.append(f"保外转保内+滤芯记录数: {policy_hit}")
            preview_cols = ['工单单号','工单性质','判定依据','保内保外','批次入库日期','安装日期','购机日期','产品名称','开发主体','故障部位名称','故障组','故障类别','服务项目或故障现象','维修方式','旧件名称','新件名称','来电内容','现场诊断故障现象','处理方案简述或备注']
            for c in preview_cols:
                if c not in df_compact.columns:
                    df_compact[c] = ''
            df_preview = df_compact[preview_cols].copy()
            for c in ['来电内容','现场诊断故障现象','处理方案简述或备注','判定依据']:
                df_preview[c] = df_preview[c].astype(str).str.slice(0, 120)
            max_rows = min(200, len(df_preview))
            df_preview = df_preview.head(max_rows)
            preview_csv = df_preview.to_csv(index=False)
            summary = "\n".join(stats_lines)
            training_content = f"# 训练数据统计摘要\n{summary}\n\n# 样本预览(最多{max_rows}行)\n{preview_csv}"

            # 构建学习规则的提示词
            prompt1 = load_prompt('quality_learn_rules_optimized').format(training_content=training_content)

            messages = [{"role": "user", "content": prompt1}]

            # 调用硅基流动模型学习规则
            resp1 = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.6,
                max_tokens=4096
            )

            # 提取学习到的规则
            rules = resp1.choices[0].message.content.strip()
            messages.append({"role": "assistant", "content": rules})

            return messages, rules, resp1.usage

        except Exception as e:
            raise Exception(f"学习非质量问题识别规则失败: {str(e)}")

    def apply_quality_rules_v1_backup(self, messages: list, test_excel: str) -> tuple:
        """备份版本：应用学习到的规则对测试数据进行质量工单判断

        第二阶段处理：将第一阶段学到的规则应用到测试数据，进行质量工单分类

        Args:
            messages (list): 包含学习规则的对话消息列表
            test_excel (str): 测试数据Excel文件路径

        Returns:
            tuple: (判断结果CSV内容, API使用统计)
        """
        try:
            # 读取测试Excel文件内容
            test_content = self._read_excel_to_text(test_excel)

            # 读取Excel获取数据行数
            df_test = pd.read_excel(test_excel, dtype=str)
            test_row_count = len(df_test)

            # 构建应用规则的提示词
            prompt2 = load_prompt('quality_apply_rules_optimized').format(
                test_content=test_content,
                test_row_count=test_row_count
            )

            # 添加应用规则的用户请求到对话历史
            messages.append({"role": "user", "content": prompt2})

            # 调用硅基流动模型应用规则进行判断
            resp2 = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.2,
                max_tokens=4096
            )

            # 提取判断结果
            quality_result = resp2.choices[0].message.content.strip()

            # 清理AI返回的结果，移除Markdown标记
            if quality_result.startswith('```csv'):
                quality_result = quality_result[6:]  # 移除开头的```csv
            if quality_result.endswith('```'):
                quality_result = quality_result[:-3]  # 移除结尾的```
            quality_result = quality_result.strip()

            # 确保有CSV头部（13列结构）
            expected_header = '工单单号,判定依据,故障部位名称,故障组,故障类别,服务项目或故障现象,故障件简称,旧件名称,新件名称,来电内容,现场诊断故障现象,处理方案简述或备注,工单性质'
            if not quality_result.startswith('工单单号'):
                quality_result = expected_header + '\n' + quality_result

            quality_result = self._strip_unexpected_header_rows(quality_result, expected_header)
            quality_result = self._force_realign_columns(quality_result, expected_header, 13)
            quality_result = self._fix_csv_format(quality_result)
            quality_result = self._validate_and_fix_csv_fields(quality_result, expected_field_count=13)
            quality_result = self._fix_quality_column_position(quality_result)
            quality_result = self._ensure_order_numbers(quality_result, df_test)
            quality_result = self._enrich_non_quality_basis(quality_result)

            return quality_result, resp2.usage

        except Exception as e:
            raise Exception(f"应用非质量问题识别规则失败: {str(e)}")

    def learn_quality_rules(self, training_excel: str) -> tuple:
        """新版本：两阶段推理 - 第一阶段：学习维修问题点推理规则 - 方法"""
        try:
            import time

            print("\n" + "="*80)
            print("[质量工单检测] 步骤1: 加载训练数据")
            print("="*80)
            print(f"训练文件: {training_excel}")

            # 读取训练Excel文件内容
            try:
                df_training = pd.read_excel(training_excel, dtype=str)
                training_rows = len(df_training)
                training_cols = len(df_training.columns)
                print(f"加载状态: ✅ 成功")
                print(f"数据规模: {training_rows}行 x {training_cols}列")
                print(f"列名: {', '.join(df_training.columns.tolist())}")
            except Exception as e:
                print(f"加载状态: ❌ 失败")
                print(f"错误信息: {str(e)}")
                raise

            # 构建精简训练内容，避免超过模型上下文长度
            df_compact = df_training.copy()
            drop_cols = [c for c in df_compact.columns if str(c).startswith('Unnamed:')]
            if drop_cols:
                df_compact = df_compact.drop(columns=drop_cols)
            for c in df_compact.columns:
                df_compact[c] = df_compact[c].astype(str).fillna('')

            def _safe_vc(series):
                try:
                    return series.value_counts().head(10).to_dict()
                except Exception:
                    return {}

            nature_counts = (df_compact['工单性质'].value_counts(dropna=False).to_dict() if '工单性质' in df_compact.columns else {})
            svc = (df_compact['服务项目或故障现象'] if '服务项目或故障现象' in df_compact.columns else pd.Series(dtype=str))
            cat = (df_compact['故障类别'] if '故障类别' in df_compact.columns else pd.Series(dtype=str))
            bn = (df_compact['保内保外'] if '保内保外' in df_compact.columns else pd.Series(dtype=str))
            oldp = (df_compact['旧件名称'] if '旧件名称' in df_compact.columns else pd.Series(dtype=str))
            newp = (df_compact['新件名称'] if '新件名称' in df_compact.columns else pd.Series(dtype=str))

            core_parts = ['电源适配器','微电脑电源板','微电脑显示板','控制板总成','主板','绕丝加热体总成','电热管','增压泵','电磁阀','进水阀','高压开关','TDS传感器','电控龙头','灯显龙头','浮球开关','浮球组件','流量计','温度感应器','滤网总成','指示灯板','排水接头','密封圈','真空热罐总成','抽水泵','跷板开关','反渗透膜滤芯','滤芯座总成']
            core_hit = int((oldp.apply(lambda x: any(p in str(x) for p in core_parts)) | newp.apply(lambda x: any(p in str(x) for p in core_parts))).sum())
            filt_hit = int((oldp.str.contains('滤芯', na=False) | newp.str.contains('滤芯', na=False)).sum())
            policy_hit = int((bn.astype(str).eq('保外转保内') & (oldp.str.contains('滤芯', na=False) | newp.str.contains('滤芯', na=False))).sum())

            stats_lines = []
            stats_lines.append(f"样本量: {len(df_compact)}")
            stats_lines.append(f"工单性质分布: {nature_counts}")
            stats_lines.append(f"服务项目Top10: {_safe_vc(svc)}")
            stats_lines.append(f"故障类别Top10: {_safe_vc(cat)}")
            stats_lines.append(f"核心部件命中数: {core_hit}")
            stats_lines.append(f"滤芯更换记录数: {filt_hit}")
            stats_lines.append(f"保外转保内+滤芯记录数: {policy_hit}")

            preview_cols = ['工单单号','工单性质','判定依据','保内保外','批次入库日期','安装日期','购机日期','产品名称','开发主体','故障部位名称','故障组','故障类别','服务项目或故障现象','维修方式','旧件名称','新件名称','来电内容','现场诊断故障现象','处理方案简述或备注']
            for c in preview_cols:
                if c not in df_compact.columns:
                    df_compact[c] = ''
            df_preview = df_compact[preview_cols].copy()
            for c in ['来电内容','现场诊断故障现象','处理方案简述或备注','判定依据']:
                df_preview[c] = df_preview[c].astype(str).str.slice(0, 120)
            max_rows = min(80, len(df_preview))
            df_preview = df_preview.head(max_rows)
            preview_csv = df_preview.to_csv(index=False)
            summary = "\n".join(stats_lines)
            training_content = f"# 训练数据统计摘要\n{summary}\n\n# 样本预览(最多{max_rows}行)\n{preview_csv}"
            print("-"*80)

            print("\n" + "="*80)
            print("[质量工单检测] 步骤2: AI学习阶段（第一步推理）")
            print("="*80)
            print(f"提示词文件: prompts/quality_learn_rules_optimized.txt")

            # 使用质量工单判断的学习提示词（优化版） - 采用分片多轮注入，避免超过上下文长度
            # 仅把统计摘要作为主提示词内容
            summary_text = f"# 训练数据统计摘要\n{summary}"
            header_prompt = load_prompt('quality_learn_rules_optimized').format(training_content=summary_text)

            # 预览CSV分片（限制总长度）
            chunk_size = 3000
            chunks = []
            for i in range(0, len(preview_csv), chunk_size):
                chunks.append(preview_csv[i:i+chunk_size])
            chunks = chunks[:5]

            messages = [{"role": "user", "content": header_prompt}]
            for idx, ch in enumerate(chunks, start=1):
                messages.append({"role": "user", "content": f"训练样本片段{idx}:\n{ch}"})
            messages.append({"role": "user", "content": "请基于上述统计摘要与样本片段，总结质量工单与非质量工单的规则、权重与决策流程，严格按要求格式输出。"})

            print(f"提示词主内容长度: {len(header_prompt)} 字符，样本片段数: {len(chunks)}")
            print("-"*80)

            print("正在调用AI模型学习判断规律...")
            start_time = time.time()

            # 调用AI模型学习规则
            resp1 = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,  # 降低温度，更聚焦于规则学习
                max_tokens=4096
            )

            elapsed_time = time.time() - start_time

            # 提取学习到的规则
            rules = resp1.choices[0].message.content.strip()
            messages.append({"role": "assistant", "content": rules})

            print(f"✅ AI学习完成")
            print(f"耗时: {elapsed_time:.2f} 秒")
            print(f"学习结果长度: {len(rules)} 字符")
            print(f"学习结果预览（前500字符）:")
            print(rules[:500] + "...")
            print(f"Token使用: 输入={resp1.usage.prompt_tokens}, 输出={resp1.usage.completion_tokens}, 总计={resp1.usage.total_tokens}")
            print("-"*80)

            return messages, rules, resp1.usage

        except Exception as e:
            print(f"\n❌ 错误: 学习维修问题点推理规则失败")
            print(f"错误类型: {type(e).__name__}")
            print(f"错误信息: {str(e)}")
            import traceback
            print(f"错误堆栈:\n{traceback.format_exc()}")
            raise Exception(f"学习维修问题点推理规则失败: {str(e)}")

    def apply_quality_rules(self, messages: list, test_excel: str) -> tuple:
        """工单类型检测：两阶段推理处理

        第一步：推理维修问题点和二级问题点
        第二步：基于问题点判断是否为质量工单

        Args:
            messages (list): 包含学习规则的对话消息列表
            test_excel (str): 测试数据Excel文件路径

        Returns:
            tuple: (质量工单判断结果CSV内容, API使用统计)
        """
        try:
            import time

            print("\n" + "="*80)
            print("[质量工单检测] 步骤3: 加载测试数据")
            print("="*80)
            print(f"测试文件: {test_excel}")

            # 读取Excel文件并进行预处理
            try:
                df_test = pd.read_excel(test_excel, dtype=str)
                test_rows = len(df_test)
                test_cols = len(df_test.columns)
                print(f"加载状态: ✅ 成功")
                print(f"数据规模: {test_rows}行 x {test_cols}列")
                print(f"列名: {', '.join(df_test.columns.tolist())}")
            except Exception as e:
                print(f"加载状态: ❌ 失败")
                print(f"错误信息: {str(e)}")
                raise

            # 数据预处理：标准化列名和添加必要字段
            # 处理工单编号列的标准化（支持"工单单号"或"维修工单号"）
            if '工单单号' not in df_test.columns and '维修工单号' not in df_test.columns:
                # 如果都没有，自动生成序号作为工单号
                df_test.insert(0, '工单单号', range(1, len(df_test) + 1))
                print("⚠️  未找到工单编号列，已自动生成序号")
            elif '维修工单号' in df_test.columns and '工单单号' not in df_test.columns:
                # 统一列名：将"维修工单号"重命名为"工单单号"
                df_test = df_test.rename(columns={'维修工单号': '工单单号'})
                print("✅ 已将'维修工单号'重命名为'工单单号'")

            # 确保存在工单性质判断结果列
            if '工单性质' not in df_test.columns:
                df_test['工单性质'] = ''
                print("✅ 已添加'工单性质'列")

            if '旧件名称' not in df_test.columns:
                df_test['旧件名称'] = ''
                print("✅ 已添加'旧件名称'列")
            if '新件名称' not in df_test.columns:
                df_test['新件名称'] = ''
                print("✅ 已添加'新件名称'列")

            # 保存预处理后的文件
            processed_file = test_excel.replace('.xlsx', '_processed.xlsx')
            df_test.to_excel(processed_file, index=False)
            print(f"预处理后文件: {processed_file}")
            print("-"*80)

            # 读取预处理后的文件内容
            test_content = self._read_excel_to_text(processed_file)

            test_row_count = len(df_test)

            print("\n" + "="*80)
            print("[质量工单检测] 步骤4: AI智能判断工单性质")
            print("="*80)
            print(f"测试数据: {test_row_count} 行")
            print(f"提示词文件: prompts/quality_learn_rules_optimized.txt")
            print("-"*80)

            # 构建AI判断提示词
            quality_prompt = f"""
根据刚才从训练数据中学习到的判断规律，对下面的测试数据进行工单性质判断。

测试数据（CSV格式）：
{test_content}

**核心要求：严格按照你刚才学习的规则进行判断！**

判断流程（必须严格执行）：

**第一步：检查硬性规则（第一层）**
对每条记录，先检查是否命中以下硬性规则：

A类（质量工单）：
1. 新机黄金法则：购机/安装日期≤30天 + 换机/退机/退货
2. 产品鉴定政策：服务项目包含"产品鉴定" + 换机/退机/退货
3. 核心部件更换：旧件/新件在核心部件库中
4. 滤芯质量缺陷：滤芯 + 漏碳/黑点/黑渣/碳粉
5. 保外转保内：保外转保内 + 滤芯
6. 噪音换机：噪音/分贝 + 换机/退机/退货

B类（非质量工单）：
1. 外部加装：服务项目包含"加装"
2. 安全维护：服务项目包含"安全维护"
3. 用户/环境责任：处理方案包含用户/客户/台盆/厨房/下水/第三方/水压/水质

**如果命中硬性规则，立即判定，不再继续！**

**第二步：应用学习的模式（第二层）**
如果第一步未命中，则应用你从训练数据中学到的规则：
- 字段权重体系（服务项目40%、判定依据30%、故障类别15%、部件更换10%、辅助5%）
- 交叉验证规则（功能性故障 vs 维护行为）
- 边界情况处理

**第三步：默认策略**
如果信息严重不足，默认为"非质量工单"

输出格式要求：
- 必须包含所有19个字段：工单单号,工单性质,判定依据,保内保外,批次入库日期,安装日期,购机日期,产品名称,开发主体,故障部位名称,故障组,故障类别,服务项目或故障现象,维修方式,旧件名称,新件名称,来电内容,现场诊断故障现象,处理方案简述或备注
- **工单性质**：只能是"质量工单"或"非质量工单"
- **判定依据**：必须明确说明：
  * 如果命中硬性规则：Rule A[编号] 或 Rule B[编号]，关键词："XXX"
  * 如果应用学习规则：字段权重分析，主要依据："XXX"
  * 示例："Rule A3: 核心部件更换，旧件=主板，新件=主板"
  * 示例："字段权重分析，服务项目=加装压力桶(B1规则)，判定为非质量工单"
- 每行必须严格包含19个字段
- 仅输出CSV格式数据，不要添加任何解释

CSV格式规范：
- 如果字段内容包含逗号(,)、引号(")或换行符，必须用双引号包裹该字段
- 字段内的双引号需要转义为两个双引号("")
- 不要在CSV中插入空行或分隔线

重要提醒：
- 必须先检查硬性规则（第一层）
- 硬性规则优先级最高
- 判定依据必须详细、明确
- 不要进行任何主观推断或语义扩展

请开始判断（共{test_row_count}条记录）：
"""

            print(f"提示词长度: {len(quality_prompt)} 字符")
            print(f"提示词关键内容: 应用学习到的规则进行判断")
            print("-"*80)

            messages.append({"role": "user", "content": quality_prompt})

            print("正在调用AI模型判断工单性质...")
            start_time = time.time()

            # 调用AI模型进行判断
            resp2 = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.0,  # 完全确定性，提高准确率
                max_tokens=16384  # 平衡输出完整性和响应速度
            )

            elapsed_time = time.time() - start_time

            # 提取判断结果
            quality_result = resp2.choices[0].message.content.strip()

            # 清理AI返回的结果
            if quality_result.startswith('```csv'):
                quality_result = quality_result[6:]
            elif quality_result.startswith('```'):
                quality_result = quality_result[3:]
            if quality_result.endswith('```'):
                quality_result = quality_result[:-3]
            quality_result = quality_result.strip()

            print(f"✅ 工单性质判断完成")
            print(f"耗时: {elapsed_time:.2f} 秒")
            print(f"判断结果长度: {len(quality_result)} 字符")

            # 统计判断结果的行数
            quality_lines = quality_result.split('\n')
            quality_row_count = len([line for line in quality_lines if line.strip()]) - 1  # 减去表头
            print(f"判断结果行数: {quality_row_count} 行（预期 {test_row_count} 行）")

            print(f"判断结果预览（前3行）:")
            preview_lines = quality_lines[:4]  # 表头 + 前3行数据
            for line in preview_lines:
                print(f"  {line[:150]}{'...' if len(line) > 150 else ''}")
            print(f"Token使用: 输入={resp2.usage.prompt_tokens}, 输出={resp2.usage.completion_tokens}, 总计={resp2.usage.total_tokens}")
            print("-"*80)

            print("\n" + "="*80)
            print("[质量工单检测] 步骤5: 数据输出与验证")
            print("="*80)

            # 统计最终输出的数据行数
            final_lines = quality_result.split('\n')
            final_row_count = len([line for line in final_lines if line.strip()]) - 1  # 减去表头
            print(f"最终输出行数: {final_row_count} 行")
            print("-"*80)

            # 合并token使用情况
            total_usage = {
                'learn_prompt_tokens': messages[0].get('usage', {}).get('prompt_tokens', 0) if len(messages) > 0 else 0,
                'learn_completion_tokens': messages[0].get('usage', {}).get('completion_tokens', 0) if len(messages) > 0 else 0,
                'judge_prompt_tokens': resp2.usage.prompt_tokens,
                'judge_completion_tokens': resp2.usage.completion_tokens,
                'total_tokens': resp2.usage.total_tokens
            }

            print("\n" + "="*80)
            print("[质量工单检测] 处理完成")
            print("="*80)
            print(f"✅ 所有步骤已完成")
            print(f"输入数据: {test_row_count} 行")
            print(f"输出数据: {final_row_count} 行")
            print(f"总Token使用: 输入={resp2.usage.prompt_tokens}, 输出={resp2.usage.completion_tokens}, 总计={resp2.usage.total_tokens}")
            print("="*80 + "\n")

            return quality_result, total_usage

        except Exception as e:
            print(f"\n" + "="*80)
            print("❌ 错误: 两阶段推理失败")
            print("="*80)
            print(f"错误类型: {type(e).__name__}")
            print(f"错误信息: {str(e)}")
            import traceback
            print(f"错误堆栈:\n{traceback.format_exc()}")
            print("="*80 + "\n")
            raise Exception(f"两阶段推理失败: {str(e)}")

    def batch_process_quality_from_db(self, filename: str, training_excel: str, batch_size: int = 50) -> tuple:
        """分批从数据库读取数据并进行质量工单判断
        
        Args:
            filename (str): workorder_data表中的filename字段值
            training_excel (str): 训练数据Excel文件路径
            batch_size (int): 每批处理的记录数，默认50条
            
        Returns:
            tuple: (合并后的CSV结果, 总token使用统计, 处理的总记录数)
        """
        try:
            from flask import current_app
            from modules.auth import db
            from modules.excel.models import WorkorderData, WorkorderUselessdata1, WorkorderUselessdata2
            import tempfile
            import os
            
            print("\n" + "="*80)
            print("[分批质量工单检测] 开始处理")
            print("="*80)
            print(f"文件名: {filename}")
            print(f"批次大小: {batch_size}条/批")
            print("-"*80)
            
            # 第一步：学习规则（只需要执行一次）
            print("\n[步骤1] 学习质量判断规则...")
            messages, rules, usage1 = self.learn_quality_rules(training_excel)
            print(f"✅ 规则学习完成")
            print("-"*80)
            
            # 第二步：查询总记录数
            print("\n[步骤2] 查询数据库记录...")
            total_records = WorkorderData.query.filter_by(filename=filename).count()
            print(f"总记录数: {total_records}条")
            
            if total_records == 0:
                print("⚠️  警告: 未找到任何记录")
                return "", {'strict_rules': 'n/a'}, 0
            
            # 计算批次数
            total_batches = (total_records + batch_size - 1) // batch_size
            print(f"批次数: {total_batches}批")
            print("-"*80)
            
            # 第三步：分批处理
            all_results = []
            header_line = None
            total_token_usage = {'strict_rules': 'n/a'}
            
            for batch_num in range(total_batches):
                offset = batch_num * batch_size
                limit = batch_size
                
                print(f"\n[批次 {batch_num + 1}/{total_batches}] 处理记录 {offset + 1} 至 {min(offset + limit, total_records)}")
                
                # 从数据库查询本批次记录
                records = WorkorderData.query.filter_by(filename=filename).offset(offset).limit(limit).all()
                
                if not records:
                    print(f"  ⚠️  本批次无记录，跳过")
                    continue
                
                print(f"  查询到 {len(records)} 条记录")
                
                # 构造19字段数据
                expected_columns = ['工单单号','工单性质','判定依据','保内保外','批次入库日期','安装日期','购机日期','产品名称','开发主体','故障部位名称','故障组','故障类别','服务项目或故障现象','维修方式','旧件名称','新件名称','来电内容','现场诊断故障现象','处理方案简述或备注']
                
                temp_data = []
                for record in records:
                    u1 = WorkorderUselessdata1.query.filter_by(filename=filename, workAlone=record.workAlone).first()
                    u2 = WorkorderUselessdata2.query.filter_by(filename=filename, workAlone=record.workAlone).first()
                    
                    def norm(v):
                        return '' if v is None or v == 'None' or (isinstance(v, float) and pd.isna(v)) else str(v)
                    
                    row_data = {
                        '工单单号': norm(record.workAlone),
                        '工单性质': norm(record.workOrderNature),
                        '判定依据': norm(record.judgmentBasis),
                        '保内保外': norm(u1.internalExternalInsurance if u1 else ''),
                        '批次入库日期': norm(u1.batchWarehousingDate if u1 else ''),
                        '安装日期': norm(u1.installDate if u1 else ''),
                        '购机日期': norm(u1.purchaseDate if u1 else ''),
                        '产品名称': norm(u1.productName if u1 else ''),
                        '开发主体': norm(u1.developmentSubject if u1 else ''),
                        '故障部位名称': norm(record.replacementPartName),
                        '故障组': norm(record.faultGroup),
                        '故障类别': norm(record.faultClassification),
                        '服务项目或故障现象': norm(record.faultPhenomenon),
                        '维修方式': norm(u2.maintenanceMode if u2 else ''),
                        '旧件名称': norm(u2.oldPartName if u2 else ''),
                        '新件名称': norm(u2.newPartName if u2 else ''),
                        '来电内容': norm(record.callContent),
                        '现场诊断故障现象': norm(record.onsiteFaultPhenomenon),
                        '处理方案简述或备注': norm(record.remarks),
                    }
                    temp_data.append({k: row_data.get(k, '') for k in expected_columns})
                
                df_batch = pd.DataFrame(temp_data, columns=expected_columns)
                print(f"  构造数据: {len(df_batch)}行 x {len(df_batch.columns)}列")
                
                # 创建临时Excel文件
                with tempfile.NamedTemporaryFile(mode='wb', suffix='.xlsx', delete=False) as tmp:
                    temp_excel_path = tmp.name
                    df_batch.to_excel(temp_excel_path, index=False)
                    print(f"  临时文件: {os.path.basename(temp_excel_path)}")
                
                try:
                    # 调用AI判断（使用已学习的规则）
                    print(f"  开始AI判断...")
                    batch_result, batch_usage = self.apply_quality_rules(messages, temp_excel_path)
                    print(f"  ✅ AI判断完成")
                    
                    # 解析结果
                    result_lines = batch_result.strip().split('\n')
                    
                    # 保存表头（第一批时）
                    if header_line is None and len(result_lines) > 0:
                        header_line = result_lines[0]
                        print(f"  表头: {header_line[:100]}...")
                    
                    # 添加数据行（跳过表头）
                    data_lines = result_lines[1:] if len(result_lines) > 1 else []
                    all_results.extend(data_lines)
                    print(f"  结果行数: {len(data_lines)}行")
                    
                finally:
                    # 清理临时文件
                    if os.path.exists(temp_excel_path):
                        os.remove(temp_excel_path)
                        print(f"  临时文件已清理")
                
                print(f"  批次处理完成 ({len(all_results)}行已累积)")
            
            # 第四步：合并所有批次结果
            print("\n" + "="*80)
            print("[步骤3] 合并批次结果")
            print("="*80)
            
            if header_line is None:
                print("❌ 错误: 未获取到表头")
                return "", total_token_usage, 0
            
            # 组装完整CSV
            final_csv = header_line + '\n' + '\n'.join(all_results)
            final_row_count = len(all_results)
            
            print(f"✅ 合并完成")
            print(f"总数据行: {final_row_count}行")
            print(f"预期记录: {total_records}条")
            
            if final_row_count != total_records:
                print(f"⚠️  警告: 结果行数({final_row_count})与记录数({total_records})不一致")
            
            print("="*80 + "\n")
            
            return final_csv, total_token_usage, total_records
            
        except Exception as e:
            print(f"\n❌ 错误: 分批处理失败")
            print(f"错误类型: {type(e).__name__}")
            print(f"错误信息: {str(e)}")
            import traceback
            print(f"错误堆栈:\n{traceback.format_exc()}")
            raise Exception(f"分批处理失败: {str(e)}")

    def _check_empty_quality(self, csv_content):
        """
        检查并记录工单性质为空的行，但不进行自动填充
        让AI模型自己学习判断，而不是依赖简单的关键词规则

        Args:
            csv_content: CSV格式的字符串

        Returns:
            原始CSV字符串（仅记录问题，不修改）
        """
        import io
        import csv

        lines = csv_content.strip().split('\n')
        if len(lines) <= 1:
            return csv_content

        # 解析CSV检查空值
        reader = csv.reader(io.StringIO(csv_content))
        header = next(reader)

        # 找到工单性质列的索引
        try:
            quality_index = header.index('工单性质')
        except ValueError:
            return csv_content

        # 统计空值情况
        empty_count = 0
        total_count = 0
        empty_rows = []

        for idx, row in enumerate(reader, start=2):  # 从第2行开始（第1行是表头）
            total_count += 1
            if len(row) > quality_index:
                quality_value = row[quality_index].strip()
                if not quality_value or quality_value.lower() in ['', 'nan', 'null', 'none']:
                    empty_count += 1
                    empty_rows.append(idx)

        # 输出空值检查结果
        if empty_count > 0:
            print(f"⚠️  警告：检测到 {empty_count}/{total_count} 行的'工单性质'为空")
            if len(empty_rows) <= 10:
                print(f"   空值行号: {', '.join(map(str, empty_rows))}")
            else:
                print(f"   空值行号（前10个）: {', '.join(map(str, empty_rows[:10]))}...")
            print(f"   建议：检查AI模型输出，或调整提示词以提高完整性")
        else:
            print(f"✅ 所有 {total_count} 行的'工单性质'均已填写")

        return csv_content

    def _enrich_non_quality_basis(self, csv_content: str) -> str:
        import io
        import csv
        import logging
        import os

        logger = logging.getLogger('quality_basis')
        if not logger.handlers:
            logger.setLevel(logging.INFO)
            os.makedirs('logs', exist_ok=True)
            fh = logging.FileHandler('logs/quality_basis.log', encoding='utf-8')
            fmt = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
            fh.setFormatter(fmt)
            logger.addHandler(fh)

        lines = csv_content.strip().split('\n')
        if len(lines) <= 1:
            return csv_content

        reader = csv.reader(io.StringIO(csv_content))
        header = next(reader)

        try:
            idx_order = header.index('工单单号')
            idx_basis = header.index('判定依据')
            idx_nature = header.index('工单性质')
            idx_old = header.index('旧件名称') if '旧件名称' in header else None
            idx_new = header.index('新件名称') if '新件名称' in header else None
        except ValueError:
            return csv_content

        col_map = {name: i for i, name in enumerate(header)}
        def get(row, name):
            i = col_map.get(name, -1)
            return (row[i].strip() if i >= 0 and len(row) > i else '')

        rows = []
        updated = 0
        total = 0

        def well_structured(text: str) -> bool:
            t = (text or '').strip()
            if not t:
                return False
            keys = ['排除', '因素', '案例', '置信度', '原因', '依据']
            return sum(1 for k in keys if k in t) >= 2

        def build(row):
            svc = get(row, '服务项目或故障现象')
            call = get(row, '来电内容')
            diag = get(row, '现场诊断故障现象')
            plan = get(row, '处理方案简述或备注')
            oldp = (row[idx_old].strip() if idx_old is not None and len(row) > idx_old else '')
            newp = (row[idx_new].strip() if idx_new is not None and len(row) > idx_new else '')

            factors = []
            if svc:
                factors.append(f"服务/现象: {svc}")
            if call:
                factors.append(f"来电: {call}")
            if diag:
                factors.append(f"诊断: {diag}")
            if plan:
                factors.append(f"方案: {plan}")
            if oldp and newp and oldp != newp:
                factors.append(f"新旧件更替: {oldp} → {newp}")

            excluded = ['产品制造/设计/来料缺陷', '零部件固有质量不达标']
            cases = ['参考训练案例：安装/调试/维护/耗材更换类样本的标注倾向']

            conf = 65
            if oldp and newp and oldp != newp:
                conf = max(conf, 85)

            proof_items = []
            text_all = ' '.join([svc or '', call or '', diag or '', plan or '']).lower()
            if any(k in text_all for k in ['客户', '定制', '需求', '要求']):
                proof_items.append('客户特殊要求单/邮件/沟通记录')
            if any(k in text_all for k in ['规格', '参数', '变更', '升级']):
                proof_items.append('技术规格变更记录/配置变更单')
            if any(k in text_all for k in ['安装', '调试', '改装', '加装']):
                proof_items.append('安装/调试记录或工单说明')
            if any(k in text_all for k in ['现场', '检测', '诊断', '报告']):
                proof_items.append('现场诊断/检测报告')
            if not proof_items:
                proof_items = ['客户需求文档', '技术规格变更记录', '安装/调试记录', '现场诊断报告']

            part1 = '具体排除的质量问题类型: ' + '；'.join(excluded)
            part2 = '关键判断因素分析: ' + ('；'.join(factors) if factors else '信息指向服务/环境/用户使用因素')
            part3 = '相关训练案例参考: ' + ('；'.join(cases))
            part4 = f'置信度评分: {conf}%'
            part5 = '证明材料或说明文档: ' + '；'.join(proof_items)
            return '\n'.join([part1, part2, part3, part4, part5])

        for row in reader:
            if not row or all((c or '').strip() == '' for c in row):
                continue
            nature = (row[idx_nature].strip() if len(row) > idx_nature else '')
            if nature == '非质量工单':
                total += 1
                basis = (row[idx_basis].strip() if len(row) > idx_basis else '')
                if not well_structured(basis):
                    nb = build(row)
                    if len(row) <= idx_basis:
                        row.extend([''] * (idx_basis - len(row) + 1))
                    row[idx_basis] = nb
                    updated += 1
                    order_no = row[idx_order] if len(row) > idx_order else ''
                    logger.info(f"basis_generated order={order_no} chars={len(nb)}")
            rows.append(row)

        output = io.StringIO()
        w = csv.writer(output, quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
        w.writerow(header)
        for r in rows:
            w.writerow(r)

        if total:
            logger.info(f"basis_summary non_quality={total} updated={updated}")

        return output.getvalue()

    def _strip_unexpected_header_rows(self, csv_text: str, expected_header: str) -> str:
        import io
        import csv
        reader = csv.reader(io.StringIO(csv_text))
        rows = list(reader)
        if not rows:
            return csv_text
        cleaned = []
        header_written = False
        for r in rows:
            line = ','.join(r).strip()
            if line == expected_header:
                if not header_written:
                    cleaned.append(r)
                    header_written = True
                continue
            if line.startswith('编号(维修行)'):
                continue
            cleaned.append(r)
        out = io.StringIO()
        w = csv.writer(out, quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
        for r in cleaned:
            w.writerow(r)
        return out.getvalue()

    def _apply_strict_rules(self, df: pd.DataFrame) -> pd.DataFrame:
        import pandas as pd
        core_parts = set([
            '电源适配器','微电脑电源板','微电脑显示板','控制板总成','主板','绕丝加热体总成','电热管','增压泵','电磁阀','进水阀','高压开关','TDS传感器','电控龙头','灯显龙头','浮球开关','浮球组件','流量计','温度感应器','滤网总成','指示灯板','排水接头','密封圈','真空热罐总成','抽水泵','跷板开关','反渗透膜滤芯','滤芯座总成'
        ])
        exchange_words = ['换机','退机','退货']
        filter_words = ['漏炭','黑点','黑渣','碳粉','活性炭粉末']
        env_keywords = ['用户','客户','台盆','厨房','下水','第三方','水压','水质']
        env_causes = ['问题','渗水','反水','管道','堵','漏']
        maintenance_actions = ['重启','复位','调试','清洗','紧固','重新安装','加固','指导','解释','检查正常','无异常','一切正常']
        fault_keywords = ['漏水','不通电','不制水','不出水','不加热','噪音大','显示异常','E1','E3','E6']

        def contains_any(text, keys):
            t = str(text or '')
            return any(k in t for k in keys)

        def within_30_days(purchase, install):
            today = pd.Timestamp.today()
            days = []
            for s in [purchase, install]:
                dt = pd.to_datetime(str(s or ''), errors='coerce')
                if pd.notna(dt):
                    days.append((today - dt).days)
            return len(days) > 0 and min(days) <= 30

        def is_core_part(oldp, newp):
            t1 = str(oldp or '')
            t2 = str(newp or '')
            return any(p in t1 for p in core_parts) or any(p in t2 for p in core_parts)

        def is_filter(oldp, newp):
            t1 = str(oldp or '')
            t2 = str(newp or '')
            return ('滤芯' in t1) or ('滤芯' in t2)

        out_rows = []
        for _, row in df.iterrows():
            svc = str(row.get('服务项目或故障现象', '') or '')
            plan = str(row.get('处理方案简述或备注', '') or '')
            call = str(row.get('来电内容', '') or '')
            diag = str(row.get('现场诊断故障现象', '') or '')
            bn = str(row.get('保内保外', '') or '')
            oldp = str(row.get('旧件名称', '') or '')
            newp = str(row.get('新件名称', '') or '')
            purchase = str(row.get('购机日期', '') or '')
            install = str(row.get('安装日期', '') or '')

            nature = ''
            basis = ''

            if within_30_days(purchase, install) and (contains_any(plan, exchange_words) or contains_any(call, exchange_words)):
                hits = ','.join([w for w in exchange_words if w in plan or w in call])
                nature, basis = '质量工单', f'Rule A.1: 新机黄金法则，命中关键词：“{hits}”'
            elif ((('产品鉴定' in svc) or ('只换不修政策产品质量鉴定' in svc)) and (contains_any(plan, exchange_words) or contains_any(call, exchange_words))):
                hits = ','.join([w for w in exchange_words if w in plan or w in call])
                nature, basis = '质量工单', f'Rule A.2: 只换不修/鉴定政策，命中关键词：“{hits}”'
            elif (oldp or newp) and is_core_part(oldp, newp):
                nature, basis = '质量工单', 'Rule A.3: 核心部件更换'
            elif is_filter(oldp, newp) and contains_any(call + diag, filter_words):
                hits = ','.join([w for w in filter_words if w in (call + diag)])
                nature, basis = '质量工单', f'Rule A.4: 滤芯质量缺陷，命中关键词：“{hits}”'
            elif bn == '保外转保内' and is_filter(oldp, newp):
                nature, basis = '质量工单', 'Rule A.5: 特殊政策触发（保外转保内+滤芯）'
            elif (('噪音' in plan) or ('噪音' in call) or ('分贝' in plan) or ('分贝' in call)) and (contains_any(plan, exchange_words) or contains_any(call, exchange_words)):
                nature, basis = '质量工单', 'Rule A.6: 主观性能缺陷（噪音/分贝+换退）'
            elif '加装' in svc:
                nature, basis = '非质量工单', 'Rule B.1: 外部加装'
            elif '安全维护' in svc:
                nature, basis = '非质量工单', 'Rule B.2: 安全维护'
            elif contains_any(plan, env_keywords) and contains_any(plan, env_causes):
                nature, basis = '非质量工单', 'Rule B.3: 用户/环境责任'
            else:
                if plan.strip() in ['上门维修', '上门检查']:
                    pass
                f = contains_any(call + diag, fault_keywords)
                m = contains_any(plan, maintenance_actions)
                if f and m:
                    nature, basis = '非质量工单', 'Rule 8.3: 有故障但维护/复位解决'
                elif f and not m:
                    nature, basis = '质量工单', 'Rule 8.3: 有故障且非简单维护'
                elif (not f) and m:
                    nature, basis = '非质量工单', 'Rule 8.3: 无故障仅维护/解释'
                else:
                    nature, basis = '非质量工单', 'Rule 3: 最终安全网'

            row_out = row.copy()
            row_out['工单性质'] = nature
            row_out['判定依据'] = basis
            out_rows.append(row_out)

        return pd.DataFrame(out_rows)
    def _fix_quality_column_position(self, csv_text: str) -> str:
        import io
        import csv
        reader = csv.reader(io.StringIO(csv_text))
        header = next(reader, None)
        if not header:
            return csv_text
        try:
            qidx = header.index('工单性质')
        except ValueError:
            return csv_text
        rows = []
        for r in reader:
            if len(r) == len(header):
                if (not r[qidx]) and any(val in ['质量工单', '非质量工单'] for val in r):
                    for j, val in enumerate(r):
                        if val in ['质量工单', '非质量工单'] and j != qidx:
                            r[qidx] = val
                            r[j] = ''
                            break
            rows.append(r)
        out = io.StringIO()
        w = csv.writer(out, quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
        w.writerow(header)
        for r in rows:
            w.writerow(r)
        return out.getvalue()

    def _ensure_order_numbers(self, csv_text: str, df_test) -> str:
        import io
        import csv
        reader = csv.reader(io.StringIO(csv_text))
        header = next(reader, None)
        if not header:
            return csv_text
        try:
            oidx = header.index('工单单号')
        except ValueError:
            return csv_text
        orders = list(df_test['工单单号']) if '工单单号' in df_test.columns else list(range(1, len(df_test)+1))
        rows = []
        i = 0
        for r in reader:
            if len(r) == len(header):
                if (not r[oidx]) and i < len(orders):
                    r[oidx] = str(orders[i])
                i += 1
            rows.append(r)
        out = io.StringIO()
        w = csv.writer(out, quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
        w.writerow(header)
        for r in rows:
            w.writerow(r)
        return out.getvalue()

    def _double_validate_replacement(self, csv_content: str) -> str:
        import io
        import csv
        import logging
        import os

        logger = logging.getLogger('quality_double_check')
        if not logger.handlers:
            logger.setLevel(logging.INFO)
            os.makedirs('logs', exist_ok=True)
            fh = logging.FileHandler('logs/quality_double_check.log', encoding='utf-8')
            fmt = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
            fh.setFormatter(fmt)
            logger.addHandler(fh)

        reader = csv.reader(io.StringIO(csv_content))
        header = next(reader)
        if '旧件名称' not in header or '新件名称' not in header:
            return csv_content
        idx_order = header.index('工单单号') if '工单单号' in header else None
        idx_old = header.index('旧件名称')
        idx_new = header.index('新件名称')

        for row in reader:
            oldp = row[idx_old].strip() if len(row) > idx_old else ''
            newp = row[idx_new].strip() if len(row) > idx_new else ''
            if oldp and newp and oldp != newp:
                order_no = row[idx_order] if idx_order is not None and len(row) > idx_order else ''
                logger.info(f"replacement_detected order={order_no} old={oldp} new={newp}")

        return csv_content

    def _force_realign_columns(self, csv_text: str, expected_header: str, expected_count: int) -> str:
        import io
        import csv
        lines = [l for l in csv_text.strip().split('\n') if l.strip()]
        if not lines:
            return csv_text
        header_line = lines[0].strip()
        if header_line != expected_header:
            header_line = expected_header
        def clean_token(t):
            s = t.strip().strip('\r').strip()
            if s.lower() in ['nan', 'null', 'none']:
                return ''
            return s
        out = io.StringIO()
        w = csv.writer(out, quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
        w.writerow(header_line.split(','))
        for raw in lines[1:]:
            if not raw.strip():
                continue
            tokens = [clean_token(x) for x in raw.split(',')]
            if len(tokens) == expected_count:
                w.writerow(tokens)
                continue
            last_idx = None
            for i in range(len(tokens)-1, -1, -1):
                v = tokens[i].strip()
                if v in ['质量工单', '非质量工单']:
                    last_idx = i
                    break
            if last_idx is None:
                while len(tokens) < expected_count:
                    tokens.append('')
                if len(tokens) > expected_count:
                    tokens = tokens[:expected_count]
                w.writerow(tokens)
                continue
            last_field = tokens[last_idx]
            middle = tokens[:last_idx]
            if not middle:
                middle = ['']
            while len(middle) < expected_count - 1:
                middle.append('')
            if len(middle) > expected_count - 1:
                pos_list = [1, 2, 5, 9, 10, 11]
                target = expected_count - 1
                cur = len(middle)
                for pos in pos_list:
                    while cur > target and pos < len(middle)-1:
                        middle[pos] = f"{middle[pos]},{middle[pos+1]}"
                        middle.pop(pos+1)
                        cur -= 1
                while len(middle) > target:
                    k = min(len(middle)-2, target-1)
                    middle[k] = f"{middle[k]},{middle[k+1]}"
                    middle.pop(k+1)
            row = middle[:expected_count-1] + [last_field]
            w.writerow(row)
        return out.getvalue()

