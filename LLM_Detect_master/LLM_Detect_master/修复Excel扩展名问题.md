# 修复Excel结果文件扩展名问题

## 问题描述

在生成Excel结果文件时出现错误：
```
ValueError: No engine for filetype: ''
```

## 问题原因

API上传的数据使用的文件名（batch_id）没有 `.xlsx` 扩展名，例如：
- `batch_001_20251219_112649_558180_5039`

在生成结果文件时，直接使用了这个文件名：
```python
result_filename = f"quality_result_{filename}"
# 结果：quality_result_batch_001_20251219_112649_558180_5039
# 问题：没有扩展名！
```

pandas的 `to_excel()` 方法需要文件扩展名来确定使用哪个引擎（openpyxl、xlsxwriter等）。

## 解决方案

修改 `modules/excel/queue_manager.py` 第453-460行，添加扩展名检查：

```python
# 生成结果文件名（使用原始filename，保持一致性）
# 确保文件名以.xlsx结尾
if filename.lower().endswith('.xlsx'):
    result_filename = f"quality_result_{filename}"
else:
    result_filename = f"quality_result_{filename}.xlsx"
```

## 修改后的行为

### 网页上传（filename有扩展名）
- 输入：`20251218_194158_工作簿1.xlsx`
- 输出：`quality_result_20251218_194158_工作簿1.xlsx`

### API上传（filename无扩展名）
- 输入：`batch_001_20251219_112649_558180_5039`
- 输出：`quality_result_batch_001_20251219_112649_558180_5039.xlsx`

## 测试步骤

1. **重启Flask应用**
   ```bash
   # 停止应用（Ctrl+C）
   python app.py
   ```

2. **通过API上传测试数据**
   - 等待检测完成
   - 查看日志，应该显示：
     ```
     ✅ Excel结果文件已生成: quality_result_batch_xxx.xlsx
     ```

3. **验证文件**
   ```bash
   # 检查results目录
   ls results/quality_result_batch_*.xlsx
   ```

4. **测试下载**
   - 访问历史记录页面
   - 点击下载按钮
   - 应该能成功下载Excel文件

## 预期结果

- ✅ 不再出现 "No engine for filetype" 错误
- ✅ Excel文件成功生成
- ✅ 文件名格式正确（包含.xlsx扩展名）
- ✅ 可以正常下载

## 注意事项

这个修复是向后兼容的：
- 对于有扩展名的文件名（网页上传），行为不变
- 对于无扩展名的文件名（API上传），自动添加.xlsx扩展名

## 总结

问题已修复！现在API上传的数据也能正确生成Excel结果文件了。🎉
