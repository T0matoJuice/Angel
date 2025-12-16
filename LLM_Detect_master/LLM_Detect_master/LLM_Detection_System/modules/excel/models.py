#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工单数据模型 - 定义质量工单检测的数据库模型
"""
from modules.auth import db


class WorkorderData(db.Model):
    """工单核心数据模型 - 映射到 MySQL angel.workorder_data 表
    
    存储质量工单检测所需的20个字段
    """
    __tablename__ = 'workorder_data'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    account = db.Column(db.String(255), nullable=True)  # 上传用户
    datatime = db.Column(db.String(255), nullable=True)  # 数据写入时间
    filename = db.Column(db.String(255), nullable=True)  # Excel文件名（带时间戳）
    workAlone = db.Column(db.String(255), nullable=True)  # 工单单号（关联字段）
    workOrderNature = db.Column(db.String(255), nullable=True)  # 工单性质（AI判断结果）
    judgmentBasis = db.Column(db.String(255), nullable=True)  # 判定依据
    productType = db.Column(db.String(255), nullable=True)  # 产品类型
    productTypeLevelOne = db.Column(db.String(255), nullable=True)  # 产品一级分类
    productTypeLevelTwo = db.Column(db.String(255), nullable=True)  # 产品二级分类
    maintenanceCategory = db.Column(db.String(255), nullable=True)  # 维修类别
    faultPartCode = db.Column(db.String(255), nullable=True)  # 故障部位
    replacementPartName = db.Column(db.Text, nullable=True)  # 故障部位名称
    faultGroup = db.Column(db.String(255), nullable=True)  # 故障组
    faultClassification = db.Column(db.String(255), nullable=True)  # 故障类别
    faultPhenomenon = db.Column(db.String(255), nullable=True)  # 服务项目或故障现象
    faultPartAbbreviation = db.Column(db.String(255), nullable=True)  # 故障件简称
    callContent = db.Column(db.Text, nullable=True)  # 来电内容
    onsiteFaultPhenomenon = db.Column(db.Text, nullable=True)  # 现场诊断故障现象
    remarks = db.Column(db.Text, nullable=True)  # 处理方案简述或备注

    def __repr__(self):
        return f'<WorkorderData {self.workAlone}>'


class WorkorderUselessdata1(db.Model):
    """工单辅助数据表1 - 映射到 MySQL angel.workorder_uselessdata_1 表

    存储39个辅助字段（保内保外、维修保养行号、工单状态等）
    注意：产品类型、产品一级分类、产品二级分类、维修类别这4个字段属于workorder_data表
    """
    __tablename__ = 'workorder_uselessdata_1'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    filename = db.Column(db.String(255), nullable=True)  # Excel文件名（关联字段）
    workAlone = db.Column(db.String(255), nullable=True)  # 工单单号（关联字段）

    # 39个辅助字段
    internalExternalInsurance = db.Column(db.String(255), nullable=True)  # 保内保外
    maintenanceLineNumber = db.Column(db.String(255), nullable=True)  # 维修保养行号
    maintenanceLineShelflife = db.Column(db.String(255), nullable=True)  # 维修保养行保外
    replacementLineNumber = db.Column(db.String(255), nullable=True)  # 换件行号
    workStatus = db.Column(db.String(255), nullable=True)  # 工单状态
    wholeMachineWarrantyEndDate = db.Column(db.String(255), nullable=True)  # 整机保内结束时间
    repairDate = db.Column(db.String(255), nullable=True)  # 报修日期
    dotReceivingDate = db.Column(db.String(255), nullable=True)  # 网点接单日期
    dotCompletionDate = db.Column(db.String(255), nullable=True)  # 网点完工日期
    serviceWorkEndDate = db.Column(db.String(255), nullable=True)  # 服务工作结束日期
    maintenanceTime = db.Column(db.String(255), nullable=True)  # 维修时间
    workType = db.Column(db.String(255), nullable=True)  # 工单类型
    createSource = db.Column(db.String(255), nullable=True)  # 创建来源
    completionOfConsultation = db.Column(db.String(255), nullable=True)  # 是否咨询完工
    dot = db.Column(db.String(255), nullable=True)  # 网点
    serviceArea = db.Column(db.String(255), nullable=True)  # 服务片区
    serviceRegion = db.Column(db.String(255), nullable=True)  # 服务区域
    gridInformation = db.Column(db.String(255), nullable=True)  # 网格信息
    serviceEngineer = db.Column(db.String(255), nullable=True)  # 服务工程师
    customer = db.Column(db.String(255), nullable=True)  # 客户
    customerAddress = db.Column(db.Text, nullable=True)  # 客户地址
    headquartersDispatching = db.Column(db.String(255), nullable=True)  # 是否总部派工
    mobilePhone = db.Column(db.String(255), nullable=True)  # 联系电话
    logisticsCode = db.Column(db.String(255), nullable=True)  # 物流码
    logisticsInboundTime = db.Column(db.String(255), nullable=True)  # 物流码入库时间
    logisticsCodeBatch = db.Column(db.String(255), nullable=True)  # 物流码批次
    productionWorkOrderNumber = db.Column(db.String(255), nullable=True)  # 生产工单号
    batchWarehousingDate = db.Column(db.String(255), nullable=True)  # 批次入库日期
    installDate = db.Column(db.String(255), nullable=True)  # 安装日期
    vendor = db.Column(db.String(255), nullable=True)  # 供应商代码
    vendorName = db.Column(db.String(255), nullable=True)  # 供应商名称
    buyerCompanyName = db.Column(db.String(255), nullable=True)  # 购机单位名称
    purchaseDate = db.Column(db.String(255), nullable=True)  # 购机日期
    productNumber = db.Column(db.String(255), nullable=True)  # 产品编号
    productName = db.Column(db.String(255), nullable=True)  # 产品名称
    developmentSubject = db.Column(db.String(255), nullable=True)  # 开发主体
    productCategoryGroup = db.Column(db.String(255), nullable=True)  # 产品类别组
    strategicType = db.Column(db.String(255), nullable=True)  # 是否战略机型
    orderChannel = db.Column(db.String(255), nullable=True)  # 订单渠道

    def __repr__(self):
        return f'<WorkorderUselessdata1 {self.workAlone}>'


class WorkorderUselessdata2(db.Model):
    """工单辅助数据表2 - 映射到 MySQL angel.workorder_uselessdata_2 表

    存储28个辅助字段（责任归属、维修方式、旧件新件信息等）
    注意：故障相关字段（故障部位、故障组、故障类别等）属于workorder_data表
    """
    __tablename__ = 'workorder_uselessdata_2'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    filename = db.Column(db.String(255), nullable=True)  # Excel文件名（关联字段）
    workAlone = db.Column(db.String(255), nullable=True)  # 工单单号（关联字段）

    # 28个辅助字段
    accountability = db.Column(db.String(255), nullable=True)  # 责任归属
    maintenanceMode = db.Column(db.String(255), nullable=True)  # 维修方式
    oldPartName = db.Column(db.String(255), nullable=True)  # 旧件名称
    oldPartAlias = db.Column(db.String(255), nullable=True)  # 旧件别名
    newPartAlias = db.Column(db.String(255), nullable=True)  # 新件别名
    newPartName = db.Column(db.String(255), nullable=True)  # 新件名称
    maintenanceCost = db.Column(db.String(255), nullable=True)  # 维修费
    settlementAmount = db.Column(db.String(255), nullable=True)  # 结算金额
    actualPrice = db.Column(db.String(255), nullable=True)  # 实际价格
    headquartersVisitingTime = db.Column(db.String(255), nullable=True)  # 总部拟回访时间
    headquartersVisitingResult = db.Column(db.String(255), nullable=True)  # 总部拟回访结果
    judgeResult = db.Column(db.String(255), nullable=True)  # 判定结果
    returnVisitInstructions = db.Column(db.Text, nullable=True)  # 回访说明
    visitor = db.Column(db.String(255), nullable=True)  # 回访人
    satisfactionDegree = db.Column(db.String(255), nullable=True)  # 满意度
    oldPartOrderPrice = db.Column(db.String(255), nullable=True)  # 旧件订单价格
    purchaseMonth = db.Column(db.String(255), nullable=True)  # 购机月份
    oldPartRecycleBarcode = db.Column(db.String(255), nullable=True)  # 旧件回收条码
    erpReceiptTime = db.Column(db.String(255), nullable=True)  # ERP收货时间
    oldPartVendor = db.Column(db.String(255), nullable=True)  # 旧件供应商
    oldPartInventoryStatus = db.Column(db.String(255), nullable=True)  # 旧件入库状态
    newPartOrderPrice = db.Column(db.String(255), nullable=True)  # 新件订单价格
    oldPartAnalysisResult = db.Column(db.String(255), nullable=True)  # 旧件鉴定结果
    oldPartAnalysisRemark = db.Column(db.Text, nullable=True)  # 旧件鉴定备注
    oldPartAnalysisDate = db.Column(db.String(255), nullable=True)  # 旧件鉴定日期
    oldPartAppraiser = db.Column(db.String(255), nullable=True)  # 旧件鉴定人
    oldPartSubmissionDeadline = db.Column(db.String(255), nullable=True)  # 旧件提交期限
    oldPartDutyCycle = db.Column(db.String(255), nullable=True)  # 旧件任务周期

    def __repr__(self):
        return f'<WorkorderUselessdata2 {self.workAlone}>'

