# 4. 数据库设计

使用 MySQL 作为事务主库，SQLAlchemy 管理模型和迁移。所有业务表建议包含 `id`、`tenant_id`、`created_at`、`updated_at`、`created_by`、`version`；软删除只用于可恢复的配置数据，审计事件不得更新或删除。

## 4.1 约 36 张表分类

| 分类 | 表 |
|---|---|
| 租户与权限（7） | tenants、users、roles、permissions、user_roles、role_permissions、departments |
| 业务主数据（5） | employees、suppliers、cost_centers、tax_rates、expense_categories |
| 报销与发票（8） | expense_reports、expense_items、invoices、invoice_lines、invoice_checks、invoice_matches、budgets、budget_usages |
| 审批与付款（5） | approval_flows、approval_nodes、approval_tasks、payment_requests、payment_records |
| 合同（5） | contracts、contract_versions、contract_clauses、contract_risks、contract_reviews |
| 文件与知识（4） | files、file_chunks、knowledge_bases、knowledge_documents |
| Agent/任务（2） | agent_runs、agent_messages |
| 审计与系统（5） | audit_logs、system_configs、idempotency_keys、notifications、job_records |

## 4.2 关键表字段

`expense_reports(id, tenant_id, applicant_id, total_amount, currency, category, status, risk_level, current_node, submitted_at)`；`invoices(id, report_id, invoice_no, invoice_type, invoice_date, seller_tax_no, buyer_tax_no, amount, tax_amount, total_amount, status, source_file_id, ocr_confidence)`；`budgets(id, tenant_id, fiscal_year, cost_center_id, category_id, allocated_amount, used_amount, frozen_amount, version)`。

`contracts(id, tenant_id, owner_id, counterparty_id, title, contract_no, status, risk_level, current_version_id)`；`contract_clauses(id, version_id, clause_no, clause_type, text, page_no, required, found)`；`contract_risks(id, contract_id, clause_id, risk_type, severity, description, evidence, recommendation, status)`。

`approval_tasks(id, business_type, business_id, flow_id, node_id, assignee_id, status, decision, comment, acted_at)`；`agent_runs(id, business_type, business_id, graph_name, graph_version, status, model_name, input_hash, output_json, started_at, ended_at)`；`audit_logs(id, tenant_id, actor_id, action, resource_type, resource_id, request_id, before_json, after_json, evidence_json, created_at)`。

## 4.3 一致性约定

预算冻结、审批决定和付款状态变化必须在事务内完成；乐观锁 `version` 防止重复审批。向量库只保存可重建索引，原始文本和权限归属仍以 MySQL/SeaweedFS（S3） 为准。跨租户查询必须由服务端自动追加 `tenant_id` 条件。

