# 6. API 设计

API 前缀为 `/api/v1`，返回格式统一为 `{code, message, data, request_id}`。认证建议使用 JWT/OIDC；服务端从令牌取得 `tenant_id`、`user_id`、角色和部门，不接受客户端覆盖。

## 6.1 核心接口

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/auth/login` | 登录并返回令牌 |
| GET | `/me` | 当前用户和权限 |
| POST | `/files/presign` | 获取 SeaweedFS（S3） 上传地址 |
| POST | `/expenses` | 创建报销单 |
| POST | `/expenses/{id}/submit` | 提交并启动 ExpenseGraph |
| GET | `/expenses/{id}` | 报销详情、解析和风险 |
| POST | `/invoices/validate` | 发票确定性校验 |
| GET | `/budgets/{id}/balance` | 查询预算余额 |
| POST | `/contracts` | 创建合同记录 |
| POST | `/contracts/{id}/analyze` | 启动合同解析与风控 |
| GET | `/approvals/tasks` | 当前人的待办 |
| POST | `/approvals/tasks/{id}/decision` | 同意、驳回或退回 |
| GET | `/agent-runs/{id}` | Agent 运行过程和证据 |
| GET | `/audit-logs` | 按资源查询审计 |

## 6.2 提交与审批示例

`POST /expenses/{id}/submit` 请求：`{idempotency_key, expected_version}`；成功返回 `202` 和 `{run_id, status: "PROCESSING"}`。`POST /approvals/tasks/{id}/decision` 请求：`{decision: "APPROVE|REJECT|RETURN", comment, expected_version}`，服务端先做权限、状态和规则校验，再事务性更新任务、业务单据和审计日志。

## 6.3 错误与幂等

使用 `400` 参数错误、`401` 未认证、`403` 无权限、`404` 不存在、`409` 状态/版本冲突、`422` 业务规则不通过、`500` 内部错误。提交、审批和付款接口必须支持幂等键；重复请求返回原结果，不重复扣预算或写付款记录。

