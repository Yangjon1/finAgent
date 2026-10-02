# 2. 业务流程

## 2.1 报销与发票审核闭环

```text
员工创建申请 → 上传发票/附件 → OCR/文档解析 → 字段标准化
→ 发票真伪/重复/抬头/税额校验 → 预算与制度校验
→ 风险分级 → 审批路由 → 人工审批 → 付款或退回补充
→ 凭证/结果归档 → 审计追踪
```

核心状态：`DRAFT`、`SUBMITTED`、`PROCESSING`、`NEED_INFO`、`PENDING_APPROVAL`、`APPROVED`、`REJECTED`、`PAYMENT_PENDING`、`PAID`、`ARCHIVED`、`CANCELLED`。

提交时生成幂等键；解析失败进入 `NEED_INFO`，不自动通过。金额、币种、税率、预算余额由规则服务计算，模型只能提出抽取结果和解释。

## 2.2 合同风控闭环

```text
合同上传 → 文件病毒/格式检查 → OCR/版面解析 → 条款分段
→ 制度与条款知识库检索 → 必备条款检查 → 风险识别与分级
→ 法务/财务审批 → 修改意见/版本回传 → 通过后归档
```

合同状态：`DRAFT`、`UPLOADED`、`PARSING`、`RISK_REVIEW`、`PENDING_APPROVAL`、`CHANGES_REQUESTED`、`APPROVED`、`REJECTED`、`ARCHIVED`。

## 2.3 风险与人工介入

高风险示例：发票金额超预算、重复发票、税率异常、收款方变更、合同缺少付款/违约/争议解决条款、模型置信度低或检索无依据。命中后必须生成 `approval_task` 或 `human_review_task`，由有权限的人员处理。

## 2.4 审计要求

每一次提交、规则命中、模型调用、工具执行、审批决定、付款状态变化、下载和归档都写入不可变的审计事件，包含操作者、组织、请求 ID、前后状态、依据文档和时间。

