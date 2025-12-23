---
description: 修复同一工单号多条数据只有一条写入检测结果的问题
---

# 问题描述

当通过接口上传同一批数据，其中有两条或多条工单号（workAlone）相同的数据时，在存入数据库后进行AI检测时会出现以下问题：

1. **数据库更新问题**：只有一条记录被写入检测结果（工单性质、判定依据）
2. **回传问题**：同一单号的多条数据没有全部回传到外部接口

## 根本原因

在 `modules/excel/queue_manager.py` 的 `_execute_inspection` 方法中（第367-370行），代码使用了 `.first()` 方法：

```python
# 原有代码 - 有问题
record = WorkorderData.query.filter_by(
    workAlone=work_alone,
    filename=filename
).first()  # ← 只获取第一条匹配的记录
```

当数据库中存在多条相同 `workAlone` 的记录时，`.first()` 只会返回第一条记录，导致：
- 其他记录的检测结果（工单性质、判定依据）没有被更新
- 回传payload中也只包含一条记录

## 解决方案

### 修改内容

修改 `queue_manager.py` 第342-389行，主要变更：

1. **使用 `.all()` 替代 `.first()`**：获取所有匹配的记录
2. **循环更新所有记录**：确保每条记录都被更新
3. **将所有记录添加到回传payload**：确保每条记录都会被回传

### 修改后的代码逻辑

```python
# 查询数据库记录 - 使用 .all() 获取所有匹配的记录
records = WorkorderData.query.filter_by(
    workAlone=work_alone,
    filename=filename
).all()

if records:
    # 更新所有匹配的记录
    for record in records:
        record.workOrderNature = work_order_nature if work_order_nature and work_order_nature != 'nan' else None
        record.judgmentBasis = judgment_basis if judgment_basis and judgment_basis != 'nan' else None
        updated_count += 1
        
        # 将每条记录都添加到回传payload中
        records_payload.append({
            "workAlone": work_alone,
            "workOrderNature": work_order_nature,
            "judgmentBasis": judgment_basis
        })
    
    print(f"   ✅ 找到 {len(records)} 条记录，已全部更新")
```

## 修复效果

修复后的行为：

1. ✅ **数据库更新**：所有相同工单号的记录都会被更新检测结果
2. ✅ **回传完整**：所有相同工单号的记录都会被回传到外部接口
3. ✅ **日志清晰**：会打印找到的记录数量，便于调试

## 测试建议

1. 上传包含重复工单号的测试数据
2. 检查数据库中所有相同工单号的记录是否都有 `workOrderNature` 和 `judgmentBasis`
3. 检查外部接口回传的数据是否包含所有记录
4. 查看日志输出，确认找到和更新的记录数量正确

## 相关文件

- `modules/excel/queue_manager.py` - 主要修改文件
- `modules/excel/models.py` - 数据模型定义
- `modules/excel/field_mapping.py` - 字段映射配置
