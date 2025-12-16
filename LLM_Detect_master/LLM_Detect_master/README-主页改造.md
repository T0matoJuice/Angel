# 主页改造完成 - 快速开始指南

## 📦 改造内容概览

已将 `mainPage.html` 从静态页面改造为动态数据驱动的仪表盘主页。

### ✅ 完成的工作

1. **后端API接口** (`modules/common/dashboard_api.py`)
   - `/api/dashboard/statistics` - 统计数据
   - `/api/dashboard/recent-records` - 最近记录
   - `/api/dashboard/user-info` - 用户信息

2. **前端页面** (`templates/mainPage.html`)
   - 移除所有静态数据
   - 集成API调用
   - 添加加载状态和错误处理
   - 实现自动刷新（30秒）

3. **路由配置** (`modules/common/routes.py`)
   - 添加 `/main` 路由访问新主页
   - 保留 `/` 路由访问旧主页

## 🚀 快速开始

### 1. 启动应用

```bash
cd d:\work\angel_official\LLM_Detect_master\LLM_Detect_master
python LLM_Detection_System/app.py
```

### 2. 访问新主页

打开浏览器访问：
```
http://localhost:5000/main
```

### 3. 测试功能

- ✅ 查看统计数据是否正确显示
- ✅ 查看最近记录是否正确显示
- ✅ 点击卡片是否能正确跳转
- ✅ 数据是否每30秒自动刷新

### 4. 如果测试通过，替换默认主页

**方法1：使用脚本（推荐）**
```bash
python 替换默认主页.py
```

**方法2：手动修改**
编辑 `modules/common/routes.py`：
```python
@common_bp.route('/')
def index():
    """集成系统主页 - 新版仪表盘"""
    return render_template('mainPage.html')
```

### 5. 如需回滚

```bash
python 回滚默认主页.py
```

## 📊 数据说明

### 统计数据来源

| 统计项 | 数据来源 | 计算方式 |
|--------|----------|----------|
| 本月检测次数 | drawing_data + workorder_data | 本月记录数 |
| 历史总次数 | drawing_data + workorder_data | 总记录数 |
| 图纸符合率 | drawing_data | (符合数/完成数)×100% |
| 工单问题比例 | workorder_data | (质量问题数/总数)×100% |

### 最近记录来源

- 制图检测：最近3条记录
- 工单检测：最近2批记录
- 合并后按时间排序，显示前5条

## 🎨 新功能特性

### 1. 动态数据
- 所有数据从数据库实时获取
- 支持自动刷新（30秒）
- 页面可见性检测自动刷新

### 2. 加载状态
- 数据加载时显示旋转动画
- 加载失败显示友好提示
- 无数据显示"暂无记录"

### 3. 交互优化
- 数据更新有动画效果
- 卡片悬停有提升效果
- 支持键盘快捷键（Ctrl+1/2/3/4）

### 4. 响应式设计
- 桌面端：2列布局
- 移动端：1列布局
- 快速导航自适应

## 📁 文件清单

### 新增文件
```
modules/common/dashboard_api.py      # 仪表盘API接口
替换默认主页.py                      # 一键替换脚本
回滚默认主页.py                      # 一键回滚脚本
新主页改造完成报告.md                # 详细报告
测试新主页.md                        # 测试文档
README-主页改造.md                   # 本文件
```

### 修改文件
```
modules/common/routes.py             # 添加/main路由
app.py                               # 注册dashboard_api蓝图
templates/mainPage.html              # 完全重写为动态页面
```

### 保留文件
```
templates/index.html                 # 旧主页（备份）
```

## 🔍 API测试

### 测试统计数据
```bash
curl http://localhost:5000/api/dashboard/statistics
```

预期返回：
```json
{
  "success": true,
  "data": {
    "monthlyCount": 123,
    "totalCount": 456,
    "drawingRate": 94.5,
    "issueRate": 12.3
  }
}
```

### 测试最近记录
```bash
curl http://localhost:5000/api/dashboard/recent-records
```

### 测试用户信息
```bash
curl http://localhost:5000/api/dashboard/user-info
```

## ⚠️ 注意事项

1. **数据库连接**：确保MySQL正常运行
2. **环境变量**：确保.env文件配置正确
3. **依赖安装**：确保所有Python包已安装
4. **测试数据**：建议先添加测试数据再查看效果
5. **浏览器缓存**：测试时建议清除缓存

## 🆘 常见问题

### Q1: 页面显示"加载中..."不消失
**A**: 检查API接口是否正常，查看浏览器控制台错误信息

### Q2: 统计数据显示0
**A**: 数据库中可能没有数据，添加一些测试记录

### Q3: 最近记录显示"暂无记录"
**A**: 正常情况，数据库中确实没有记录

### Q4: 如何回到旧主页
**A**: 访问 http://localhost:5000/ 或运行回滚脚本

## 📞 技术支持

如有问题，请查看：
- `新主页改造完成报告.md` - 详细技术文档
- `测试新主页.md` - 测试指南
- 浏览器开发者工具控制台 - 查看错误信息

## 🎉 总结

新主页已完全改造完成，现在可以：

1. ✅ 显示真实的统计数据
2. ✅ 显示真实的检测记录
3. ✅ 自动刷新数据
4. ✅ 友好的加载和错误提示
5. ✅ 保留旧主页作为备份

**下一步**：启动应用，访问 `/main` 测试新主页！
