# 3. 系统架构

## 3.1 总体拓扑

```text
Vue3/TS/Element Plus/ECharts
            │ REST/JSON
         FastAPI
   ┌────────┼────────┐
业务服务   Agent服务  文件/知识服务
   │       LangGraph   │
   │  Expense/Contract  │
   ├── MySQL             ├── SeaweedFS（S3）
   ├── Redis             └── Qdrant
   └── Audit Log
模型：DeepSeek / Qwen / Ollama
解析：PaddleOCR / Docling / MinerU
```

## 3.2 分层职责

- 表现层：页面、表单校验、审批操作和 ECharts；不在浏览器决定最终权限或业务状态。
- API 层：鉴权、组织隔离、输入校验、幂等和错误映射。
- 领域层：报销、发票、预算、合同、审批、归档和规则。
- Agent 层：状态图、检索、工具选择、结构化输出和人工中断。
- 基础设施层：MySQL、Redis、SeaweedFS（S3）、Qdrant、模型/OCR适配器。

## 3.3 LLM 与确定性规则边界

LLM 负责 OCR 后语义归一化、条款分类、风险说明、制度问答和候选审批路径；所有结果必须带置信度、来源片段和结构化 schema。规则服务负责金额计算、税率白名单、预算扣减、重复检测、权限、状态机、审批矩阵和付款条件。LLM 不得直接写业务表、付款或改变审批状态。

## 3.4 工具调用安全链

任何会读写业务或触发外部动作的工具都必须走：`LLM → Tool → 权限检查 → 业务服务 → 事务 → 审计日志`。工具只暴露窄接口，例如 `get_budget_balance`、`validate_invoice`、`search_policy`、`create_approval_task`，禁止暴露任意 SQL 或任意文件路径。

## 3.5 目录基线

```text
finAgent/
├── README.md
├── docs/
├── .codex/instructions.md
├── backend/app/{api,agents,domain,models,schemas,services,tools,core}/
├── backend/tests/
├── frontend/src/{api,components,layouts,router,stores,views}/
├── migrations/
├── docker-compose.yml
├── .env.example
└── THIRD_PARTY.md
```
