#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel字段映射配置 - 定义83个Excel列名到数据库字段的映射关系
"""

# Excel列名到workorder_data表字段的映射（20个字段）
EXCEL_TO_WORKORDER_DATA = {
    '工单单号': 'workAlone',
    '工单性质': 'workOrderNature',
    '判定依据': 'judgmentBasis',
    '产品类型': 'productType',
    '产品一级分类': 'productTypeLevelOne',
    '产品二级分类': 'productTypeLevelTwo',
    '维修类别': 'maintenanceCategory',
    '故障部位': 'faultPartCode',
    '故障部位名称': 'replacementPartName',
    '故障组': 'faultGroup',
    '故障类别': 'faultClassification',
    '服务项目或故障现象': 'faultPhenomenon',
    '故障件简称': 'faultPartAbbreviation',
    '来电内容': 'callContent',
    '现场诊断故障现象': 'onsiteFaultPhenomenon',
    '处理方案简述或备注': 'remarks',
}

# Excel列名到workorder_uselessdata_1表字段的映射（39个字段）
# 注意：产品类型、产品一级分类、产品二级分类、维修类别这4个字段属于workorder_data表
EXCEL_TO_WORKORDER_USELESSDATA_1 = {
    '保内保外': 'internalExternalInsurance',
    '维修保养行号': 'maintenanceLineNumber',
    '维修保养行保外': 'maintenanceLineShelflife',
    '换件行号': 'replacementLineNumber',
    '工单状态': 'workStatus',
    '整机保内结束时间': 'wholeMachineWarrantyEndDate',
    '报修日期': 'repairDate',
    '网点接单日期': 'dotReceivingDate',
    '网点完工日期': 'dotCompletionDate',
    '服务工作结束日期': 'serviceWorkEndDate',
    '维修时间': 'maintenanceTime',
    '工单类型': 'workType',
    '创建来源': 'createSource',
    '是否咨询完工': 'completionOfConsultation',
    '网点': 'dot',
    '服务片区': 'serviceArea',
    '服务区域': 'serviceRegion',
    '网格信息': 'gridInformation',
    '服务工程师': 'serviceEngineer',
    '客户': 'customer',
    '客户地址': 'customerAddress',
    '是否总部派工': 'headquartersDispatching',
    '联系电话': 'mobilePhone',
    '物流码': 'logisticsCode',
    '物流码入库时间': 'logisticsInboundTime',
    '物流码批次': 'logisticsCodeBatch',
    '生产工单号': 'productionWorkOrderNumber',
    '批次入库日期': 'batchWarehousingDate',
    '安装日期': 'installDate',
    '供应商代码': 'vendor',
    '供应商名称': 'vendorName',
    '购机单位名称': 'buyerCompanyName',
    '购机日期': 'purchaseDate',
    '产品编号': 'productNumber',
    '产品名称': 'productName',
    '开发主体': 'developmentSubject',
    '产品类别组': 'productCategoryGroup',
    '是否战略机型': 'strategicType',
    '订单渠道': 'orderChannel',
}

# Excel列名到workorder_uselessdata_2表字段的映射（28个字段）
# 注意：故障相关字段（故障部位、故障组、故障类别等）属于workorder_data表
EXCEL_TO_WORKORDER_USELESSDATA_2 = {
    '责任归属': 'accountability',
    '维修方式': 'maintenanceMode',
    '旧件名称': 'oldPartName',
    '旧件别名': 'oldPartAlias',
    '新件别名': 'newPartAlias',
    '新件名称': 'newPartName',
    '维修费': 'maintenanceCost',
    '结算金额': 'settlementAmount',
    '实际价格': 'actualPrice',
    '总部拟回访时间': 'headquartersVisitingTime',
    '总部拟回访结果': 'headquartersVisitingResult',
    '判定结果': 'judgeResult',
    '回访说明': 'returnVisitInstructions',
    '回访人': 'visitor',
    '满意度': 'satisfactionDegree',
    '旧件订单价格': 'oldPartOrderPrice',
    '购机月份': 'purchaseMonth',
    '旧件回收条码': 'oldPartRecycleBarcode',
    'ERP收货时间': 'erpReceiptTime',
    '旧件供应商': 'oldPartVendor',
    '旧件入库状态': 'oldPartInventoryStatus',
    '新件订单价格': 'newPartOrderPrice',
    '旧件鉴定结果': 'oldPartAnalysisResult',
    '旧件鉴定备注': 'oldPartAnalysisRemark',
    '旧件鉴定日期': 'oldPartAnalysisDate',
    '旧件鉴定人': 'oldPartAppraiser',
    '旧件提交期限': 'oldPartSubmissionDeadline',
    '旧件任务周期': 'oldPartDutyCycle',
}

# 质量工单检测所需的10个输入字段（按顺序）
# 注意：不包括"工单性质"，因为这是AI判断的输出字段
QUALITY_DETECTION_INPUT_FIELDS = [
    'workAlone',  # 工单单号
    'judgmentBasis',  # 判定依据
    'replacementPartName',  # 故障部位名称
    'faultGroup',  # 故障组
    'faultClassification',  # 故障类别
    'faultPhenomenon',  # 服务项目或故障现象
    'faultPartAbbreviation',  # 故障件简称
    'callContent',  # 来电内容
    'onsiteFaultPhenomenon',  # 现场诊断故障现象
    'remarks',  # 处理方案简述或备注
]

# 质量工单检测输入字段的中文名称（按顺序）
QUALITY_DETECTION_INPUT_FIELDS_CN = [
    '工单单号',
    '判定依据',
    '故障部位名称',
    '故障组',
    '故障类别',
    '服务项目或故障现象',
    '故障件简称',
    '来电内容',
    '现场诊断故障现象',
    '处理方案简述或备注',
]

# 完整的11个字段（包括工单性质）- 用于训练数据
QUALITY_DETECTION_FIELDS_WITH_RESULT = QUALITY_DETECTION_INPUT_FIELDS + ['workOrderNature']
QUALITY_DETECTION_FIELDS_CN_WITH_RESULT = QUALITY_DETECTION_INPUT_FIELDS_CN + ['工单性质']

# 数据库字段到中文名称的映射
DB_FIELD_TO_CN = {
    'workAlone': '工单单号',
    'workOrderNature': '工单性质',
    'judgmentBasis': '判定依据',
    'productType': '产品类型',
    'productTypeLevelOne': '产品一级分类',
    'productTypeLevelTwo': '产品二级分类',
    'maintenanceCategory': '维修类别',
    'faultPartCode': '故障部位',
    'replacementPartName': '故障部位名称',
    'faultGroup': '故障组',
    'faultClassification': '故障类别',
    'faultPhenomenon': '服务项目或故障现象',
    'faultPartAbbreviation': '故障件简称',
    'callContent': '来电内容',
    'onsiteFaultPhenomenon': '现场诊断故障现象',
    'remarks': '处理方案简述或备注',
}


def get_workorder_data_mapping():
    """获取workorder_data表的字段映射"""
    return EXCEL_TO_WORKORDER_DATA


def get_workorder_uselessdata_1_mapping():
    """获取workorder_uselessdata_1表的字段映射"""
    return EXCEL_TO_WORKORDER_USELESSDATA_1


def get_workorder_uselessdata_2_mapping():
    """获取workorder_uselessdata_2表的字段映射"""
    return EXCEL_TO_WORKORDER_USELESSDATA_2


def get_quality_detection_fields():
    """获取质量工单检测所需的10个输入字段（数据库字段名）
    注意：不包括"工单性质"，因为这是AI判断的输出字段
    """
    return QUALITY_DETECTION_INPUT_FIELDS


def get_quality_detection_fields_cn():
    """获取质量工单检测所需的10个输入字段（中文名称）
    注意：不包括"工单性质"，因为这是AI判断的输出字段
    """
    return QUALITY_DETECTION_INPUT_FIELDS_CN


def get_quality_detection_fields_with_result():
    """获取完整的11个字段（包括工单性质）- 用于训练数据"""
    return QUALITY_DETECTION_FIELDS_WITH_RESULT


def get_quality_detection_fields_cn_with_result():
    """获取完整的11个字段的中文名称（包括工单性质）- 用于训练数据"""
    return QUALITY_DETECTION_FIELDS_CN_WITH_RESULT


def db_field_to_chinese(field_name):
    """将数据库字段名转换为中文名称"""
    return DB_FIELD_TO_CN.get(field_name, field_name)

