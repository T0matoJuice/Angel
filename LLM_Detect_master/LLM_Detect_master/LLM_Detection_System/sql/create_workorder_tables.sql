-- ========================================
-- 工单数据库表创建脚本
-- 数据库: angel
-- 用途: 质量工单检测系统
-- ========================================

USE angel;

-- ========================================
-- 表1: workorder_data (核心数据表)
-- 存储质量工单检测所需的20个核心字段
-- ========================================
CREATE TABLE IF NOT EXISTS `workorder_data` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键，自增',
  `account` varchar(255) DEFAULT NULL COMMENT '上传用户（对应登录用户的username）',
  `datatime` varchar(255) DEFAULT NULL COMMENT '数据写入时间',
  `filename` varchar(255) DEFAULT NULL COMMENT 'Excel文件名（带时间戳，确保唯一性）',
  `workAlone` varchar(255) DEFAULT NULL COMMENT '工单单号（关联字段）',
  `workOrderNature` varchar(255) DEFAULT NULL COMMENT '工单性质（AI判断结果：质量工单/非质量工单）',
  `judgmentBasis` varchar(255) DEFAULT NULL COMMENT '判定依据',
  `productType` varchar(255) DEFAULT NULL COMMENT '产品类型',
  `productTypeLevelOne` varchar(255) DEFAULT NULL COMMENT '产品一级分类',
  `productTypeLevelTwo` varchar(255) DEFAULT NULL COMMENT '产品二级分类',
  `maintenanceCategory` varchar(255) DEFAULT NULL COMMENT '维修类别',
  `faultPartCode` varchar(255) DEFAULT NULL COMMENT '故障部位',
  `replacementPartName` text COMMENT '故障部位名称',
  `faultGroup` varchar(255) DEFAULT NULL COMMENT '故障组',
  `faultClassification` varchar(255) DEFAULT NULL COMMENT '故障类别',
  `faultPhenomenon` varchar(255) DEFAULT NULL COMMENT '服务项目或故障现象',
  `faultPartAbbreviation` varchar(255) DEFAULT NULL COMMENT '故障件简称',
  `callContent` text COMMENT '来电内容',
  `onsiteFaultPhenomenon` text COMMENT '现场诊断故障现象',
  `remarks` text COMMENT '处理方案简述或备注',
  PRIMARY KEY (`id`),
  KEY `idx_filename` (`filename`),
  KEY `idx_workAlone` (`workAlone`),
  KEY `idx_account` (`account`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工单核心数据表';


-- ========================================
-- 表2: workorder_uselessdata_1 (辅助数据表1)
-- 存储43个辅助字段
-- ========================================
CREATE TABLE IF NOT EXISTS `workorder_uselessdata_1` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键，自增',
  `filename` varchar(255) DEFAULT NULL COMMENT 'Excel文件名（关联字段）',
  `workAlone` varchar(255) DEFAULT NULL COMMENT '工单单号（关联字段）',
  `internalExternalInsurance` varchar(255) DEFAULT NULL COMMENT '保内保外',
  `maintenanceLineNumber` varchar(255) DEFAULT NULL COMMENT '维修保养行号',
  `maintenanceLineShelflife` varchar(255) DEFAULT NULL COMMENT '维修保养行保外',
  `replacementLineNumber` varchar(255) DEFAULT NULL COMMENT '换件行号',
  `workStatus` varchar(255) DEFAULT NULL COMMENT '工单状态',
  `wholeMachineWarrantyEndDate` varchar(255) DEFAULT NULL COMMENT '整机保内结束时间',
  `repairDate` varchar(255) DEFAULT NULL COMMENT '报修日期',
  `dotReceivingDate` varchar(255) DEFAULT NULL COMMENT '网点接单日期',
  `dotCompletionDate` varchar(255) DEFAULT NULL COMMENT '网点完工日期',
  `serviceWorkEndDate` varchar(255) DEFAULT NULL COMMENT '服务工作结束日期',
  `maintenanceTime` varchar(255) DEFAULT NULL COMMENT '维修时间',
  `workType` varchar(255) DEFAULT NULL COMMENT '工单类型',
  `createSource` varchar(255) DEFAULT NULL COMMENT '创建来源',
  `completionOfConsultation` varchar(255) DEFAULT NULL COMMENT '是否咨询完工',
  `dot` varchar(255) DEFAULT NULL COMMENT '网点',
  `serviceArea` varchar(255) DEFAULT NULL COMMENT '服务片区',
  `serviceRegion` varchar(255) DEFAULT NULL COMMENT '服务区域',
  `gridInformation` varchar(255) DEFAULT NULL COMMENT '网格信息',
  `serviceEngineer` varchar(255) DEFAULT NULL COMMENT '服务工程师',
  `customer` varchar(255) DEFAULT NULL COMMENT '客户',
  `customerAddress` text COMMENT '客户地址',
  `headquartersDispatching` varchar(255) DEFAULT NULL COMMENT '是否总部派工',
  `mobilePhone` varchar(255) DEFAULT NULL COMMENT '联系电话',
  `logisticsCode` varchar(255) DEFAULT NULL COMMENT '物流码',
  `logisticsInboundTime` varchar(255) DEFAULT NULL COMMENT '物流码入库时间',
  `logisticsCodeBatch` varchar(255) DEFAULT NULL COMMENT '物流码批次',
  `productionWorkOrderNumber` varchar(255) DEFAULT NULL COMMENT '生产工单号',
  `batchWarehousingDate` varchar(255) DEFAULT NULL COMMENT '批次入库日期',
  `installDate` varchar(255) DEFAULT NULL COMMENT '安装日期',
  `vendor` varchar(255) DEFAULT NULL COMMENT '供应商代码',
  `vendorName` varchar(255) DEFAULT NULL COMMENT '供应商名称',
  `buyerCompanyName` varchar(255) DEFAULT NULL COMMENT '购机单位名称',
  `purchaseDate` varchar(255) DEFAULT NULL COMMENT '购机日期',
  `productNumber` varchar(255) DEFAULT NULL COMMENT '产品编号',
  `productName` varchar(255) DEFAULT NULL COMMENT '产品名称',
  `developmentSubject` varchar(255) DEFAULT NULL COMMENT '开发主体',
  `productCategoryGroup` varchar(255) DEFAULT NULL COMMENT '产品类别组',
  `strategicType` varchar(255) DEFAULT NULL COMMENT '是否战略机型',
  `productType` varchar(255) DEFAULT NULL COMMENT '产品类型',
  `productTypeLevelOne` varchar(255) DEFAULT NULL COMMENT '产品一级分类',
  `productTypeLevelTwo` varchar(255) DEFAULT NULL COMMENT '产品二级分类',
  `orderChannel` varchar(255) DEFAULT NULL COMMENT '订单渠道',
  `maintenanceCategory` varchar(255) DEFAULT NULL COMMENT '维修类别',
  PRIMARY KEY (`id`),
  KEY `idx_filename` (`filename`),
  KEY `idx_workAlone` (`workAlone`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工单辅助数据表1';


-- ========================================
-- 表3: workorder_uselessdata_2 (辅助数据表2)
-- 存储31个辅助字段
-- ========================================
CREATE TABLE IF NOT EXISTS `workorder_uselessdata_2` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键，自增',
  `filename` varchar(255) DEFAULT NULL COMMENT 'Excel文件名（关联字段）',
  `workAlone` varchar(255) DEFAULT NULL COMMENT '工单单号（关联字段）',
  `faultPartCode` varchar(255) DEFAULT NULL COMMENT '故障部位',
  `replacementPartName` text COMMENT '故障部位名称',
  `faultGroup` varchar(255) DEFAULT NULL COMMENT '故障组',
  `faultClassification` varchar(255) DEFAULT NULL COMMENT '故障类别',
  `faultPhenomenon` varchar(255) DEFAULT NULL COMMENT '服务项目或故障现象',
  `accountability` varchar(255) DEFAULT NULL COMMENT '责任归属',
  `maintenanceMode` varchar(255) DEFAULT NULL COMMENT '维修方式',
  `oldPartName` varchar(255) DEFAULT NULL COMMENT '旧件名称',
  `oldPartAlias` varchar(255) DEFAULT NULL COMMENT '旧件别名',
  `newPartAlias` varchar(255) DEFAULT NULL COMMENT '新件别名',
  `newPartName` varchar(255) DEFAULT NULL COMMENT '新件名称',
  `faultPartAbbreviation` varchar(255) DEFAULT NULL COMMENT '故障件简称',
  `callContent` text COMMENT '来电内容',
  `onsiteFaultPhenomenon` text COMMENT '现场诊断故障现象',
  `remarks` text COMMENT '处理方案简述或备注',
  `maintenanceCost` varchar(255) DEFAULT NULL COMMENT '维修费',
  `settlementAmount` varchar(255) DEFAULT NULL COMMENT '结算金额',
  `actualPrice` varchar(255) DEFAULT NULL COMMENT '实际价格',
  `headquartersVisitingTime` varchar(255) DEFAULT NULL COMMENT '总部拟回访时间',
  `headquartersVisitingResult` varchar(255) DEFAULT NULL COMMENT '总部拟回访结果',
  `judgeResult` varchar(255) DEFAULT NULL COMMENT '判定结果',
  `returnVisitInstructions` text COMMENT '回访说明',
  `visitor` varchar(255) DEFAULT NULL COMMENT '回访人',
  `satisfactionDegree` varchar(255) DEFAULT NULL COMMENT '满意度',
  `oldPartOrderPrice` varchar(255) DEFAULT NULL COMMENT '旧件订单价格',
  `purchaseMonth` varchar(255) DEFAULT NULL COMMENT '购机月份',
  `oldPartRecycleBarcode` varchar(255) DEFAULT NULL COMMENT '旧件回收条码',
  `erpReceiptTime` varchar(255) DEFAULT NULL COMMENT 'ERP收货时间',
  `oldPartVendor` varchar(255) DEFAULT NULL COMMENT '旧件供应商',
  `oldPartInventoryStatus` varchar(255) DEFAULT NULL COMMENT '旧件入库状态',
  `newPartOrderPrice` varchar(255) DEFAULT NULL COMMENT '新件订单价格',
  `oldPartAnalysisResult` varchar(255) DEFAULT NULL COMMENT '旧件鉴定结果',
  `oldPartAnalysisRemark` text COMMENT '旧件鉴定备注',
  `oldPartAnalysisDate` varchar(255) DEFAULT NULL COMMENT '旧件鉴定日期',
  `oldPartAppraiser` varchar(255) DEFAULT NULL COMMENT '旧件鉴定人',
  `oldPartSubmissionDeadline` varchar(255) DEFAULT NULL COMMENT '旧件提交期限',
  `oldPartDutyCycle` varchar(255) DEFAULT NULL COMMENT '旧件任务周期',
  PRIMARY KEY (`id`),
  KEY `idx_filename` (`filename`),
  KEY `idx_workAlone` (`workAlone`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工单辅助数据表2';


-- ========================================
-- 索引说明
-- ========================================
-- 1. 所有表都有主键id（自增）
-- 2. filename字段建立索引，用于快速查询某个文件的所有记录
-- 3. workAlone字段建立索引，用于快速查询某个工单号的记录
-- 4. workorder_data表的account字段建立索引，用于用户隔离查询

-- ========================================
-- 使用说明
-- ========================================
-- 1. 三张表通过 filename 和 workAlone 关联
-- 2. workorder_data.workOrderNature 字段初始为空，AI判断后回写
-- 3. 文件名建议格式：{timestamp}_{original_filename}.xlsx
-- 4. datatime 格式：YYYY-MM-DD HH:MM:SS

