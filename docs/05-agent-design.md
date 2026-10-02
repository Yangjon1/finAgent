# 5. LangGraph Agent 设计

## 5.1 ExpenseState

```python
class ExpenseState(TypedDict):
    run_id: str
    report_id: str
    tenant_id: str
    documents: list[dict]
    extracted_fields: dict
    invoice_results: list[dict]
    budget_result: dict
    policy_hits: list[dict]
    risks: list[dict]
    recommendation: str
    confidence: float
    approval_route: list[dict]
    human_required: bool
    errors: list[dict]
```

## 5.2 ExpenseGraph

```text
load_context
  → parse_documents
  → extract_invoice_fields
  → deterministic_invoice_checks
  → budget_check
  → retrieve_policy
  → risk_assessment
  → route_decision
      ├─ human_review → interrupt / approval task
      ├─ need_info → request_more_info
      └─ ready → create_approval_tasks
  → persist_result → audit
```

合同图复用相同的 `load_context`、`retrieve_policy`、`risk_assessment` 和 `human_review` 思路，增加 `clause_segment`、`required_clause_check`、`contract_risk_assessment` 和版本比较节点。

## 5.3 Tools

`parse_file`、`extract_invoice`、`validate_invoice`、`check_duplicate_invoice`、`get_budget_balance`、`freeze_budget`、`search_policy`、`search_contract_clause`、`calculate_tax`、`resolve_approval_route`、`create_approval_task`、`request_human_review`、`save_agent_result`、`write_audit_log`。

每个 Tool 使用 Pydantic 输入/输出模型，显式声明只读或写入权限、资源类型和审计动作。写入工具必须由业务服务再次校验，不信任模型传入的金额、用户或租户。

## 5.4 模型与降级

通过统一 `LLMProvider` 支持 DeepSeek、Qwen、Ollama；按任务配置模型和温度。模型超时、JSON 不合法、置信度低或无检索证据时，转人工或重试，不得默认“通过”。提示词、schema 和 graph version 都写入 `agent_runs`。

