# 🤖 LLM智能检测系统

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg) ![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg) ![Kimi](https://img.shields.io/badge/AI-Kimi-orange.svg) ![License](https://img.shields.io/badge/License-MIT-green.svg)

**基于大模型的企业级智能检测平台** - 集成机械制图规范检测和工单数据智能处理功能

---

## ✨ 系统特色

- **🔧 机械制图规范检测**: 基于国家标准GB/T 14689的PDF制图文件智能分析
- **📊 工单数据智能处理**: Excel工单的问题点自动填充和质量类型智能判断
- **🧠 AI驱动智能化**: Kimi大模型深度集成，提供精准的检测结果和改进建议
- **📱 现代化用户体验**: 响应式Web界面，拖拽上传，实时数据对比
- **🏗️ 模块化架构**: Flask蓝图设计，功能模块独立，易于扩展和维护
- **🔒 企业级安全**: 本地部署支持，数据不出企业内网

---

## 🚀 快速开始

### 1. 环境要求
- Python 3.8+ (推荐使用 Anaconda 3.13.5)
- MySQL 数据库 (可选，用于工单数据存储)

### 2. 安装依赖
```bash
cd LLM_Detect_master
python -m pip install -r LLM_Detection_System/requirements.txt
```

### 3. 配置环境变量
在 `LLM_Detection_System` 目录创建 `.env` 文件：
```env
# Kimi API (制图检测)
MOONSHOT_API_KEY=your_kimi_api_key_here
MOONSHOT_MODEL_vision=moonshot-v1-32k
MOONSHOT_MODEL_turbo=moonshot-v1-32k

# 硅基流动 API (Excel工单处理)
SILICONFLOW_API_KEY_EXCEL=your_siliconflow_api_key_here
SILICONFLOW_MODEL_EXCEL=Qwen/Qwen2.5-32B-Instruct
```

### 4. 启动系统
```bash
python LLM_Detection_System/app.py
```

**访问地址**: http://localhost:5000

---

## 🎯 核心功能

### 🔧 机械制图规范检测
- **图纸幅面规范检测**: 检测图纸尺寸是否符合GB/T 14689标准
- **线型使用规范检测**: 验证粗实线、细实线、虚线和点划线的使用
- **尺寸标注规范检测**: 检查尺寸数字位置和标注完整性
- **公差标注检测**: 验证公差标注格式和形位公差符号
- **视图表达规范检测**: 检查视图布局和投影关系

**使用流程**:
1. 上传PDF制图文件 (≤50MB)
2. AI自动分析制图规范
3. 获取检测结论和改进建议
4. 下载检测报告

### 📊 Excel工单智能处理

#### 工单问题点检测
通过两阶段AI推理，自动填充"维修问题点"和"二级问题点"字段

**数据格式要求**:
- 必需列: 编号(维修行), 来电内容(维修行), 现场诊断故障现象(维修行), 故障部位(维修行), 故障件名称(维修行), 处理方案简述(维修行), 故障类别(维修行)
- AI填充列: 维修问题点, 二级问题点

#### 质量工单智能判定
基于工单内容智能识别是否属于质量问题类型

**判断标准**:
- 质量工单: 产品缺陷、制程问题、研发问题、来料问题、设计缺陷
- 非质量工单: 安装服务、环境使用、用户操作问题、维护保养

---

## 🛠️ 技术架构

**后端**: Flask 2.3+ + Kimi API + Pandas 2.0+ + OpenPyXL 3.1+ + PDF2Image  
**前端**: HTML5 + CSS3 + JavaScript (响应式设计)

**项目结构**:
```
LLM_Detection_System/
├── app.py                 # Flask应用入口
├── requirements.txt       # 依赖包列表
├── modules/              # 功能模块
│   ├── common/           # 公共模块(配置、路由、历史记录)
│   ├── drawing/          # 制图检测模块
│   ├── excel/            # Excel工单处理模块
│   └── auth/             # 认证模块(登录/注册/验证码)
├── templates/           # HTML模板文件
├── prompts/            # AI提示词模板
├── data/               # 训练数据和标准文件
├── uploads/            # 用户上传文件(运行时创建)
├── results/            # 处理结果文件(运行时创建)
└── history/            # 历史记录数据(运行时创建)
```

---

## 📋 使用指南

### 制图检测系统
1. 访问 http://localhost:5000/drawing
2. 上传PDF制图文件 (支持拖拽)
3. 点击"开始检测"
4. 查看检测结果和改进建议
5. 下载检测报告

### Excel工单处理系统
1. 访问 http://localhost:5000/excel
2. 选择功能 (问题点检测 / 质量工单判定)
3. 上传Excel文件 (≤100条记录推荐)
4. 等待AI处理 (1-2分钟)
5. 查看结果对比
6. 下载处理结果

---

## ⚠️ 注意事项

### 性能限制
| 功能 | 推荐数据量 | 最大限制 | 处理时间 |
|------|------------|----------|----------|
| 制图检测 | 1个PDF | 50MB | 1-2分钟 |
| 工单问题点检测 | ≤100条 | 200条 | 0.5-2分钟 |
| 质量工单判定 | ≤100条 | 200条 | 0.5-2分钟 |

### 文件格式要求
- **制图检测**: 仅支持PDF格式，图像清晰，文字可识别
- **Excel处理**: 支持.xlsx和.xls格式，UTF-8编码，列名必须严格按照标准格式

---

## 🔧 故障排除

### 常见问题

**1. ModuleNotFoundError**
```bash
python -m pip install -r LLM_Detection_System/requirements.txt
```

**2. 端口被占用**
```bash
# 查找占用端口的进程
netstat -ano | findstr :5000
# 结束进程
taskkill /PID <PID> /F
```

**3. 验证码不显示**
```bash
python -m pip install captcha
```

**4. API密钥未配置**
检查 `.env` 文件是否存在并配置了正确的API密钥

---

## 📝 版本历史

### v2.0 (2025-11-13)
- ✅ 新增CAPTCHA验证码功能
- ✅ Excel质量工单检测功能更新 (9列→11列)
- ✅ 新增字段: 判定依据、服务项目或故障现象
- ✅ 优化requirements.txt依赖管理

### v1.0
- ✅ 机械制图规范检测
- ✅ Excel工单问题点检测
- ✅ 质量工单智能判定
- ✅ 用户认证系统
- ✅ 历史记录管理

---

## 📞 技术支持

**文档**:
- [API文档](./API文档.md) - 详细的API接口说明
- [数据格式说明](./数据格式说明.md) - Excel数据格式和字段说明
- [部署检查清单](./LLM_Detection_System/部署检查清单.md) - 部署验证清单

**快速启动**:
```bash
# 一键启动
cd LLM_Detect_master && python LLM_Detection_System/app.py
```

**访问地址**: http://localhost:5000

---

## 📄 许可证

MIT License - 详见 LICENSE 文件

---

**🎉 祝您使用愉快！**
