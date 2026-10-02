# FinAgent：企业财税智能审批与合同风控 Agent 平台

FinAgent 是面向中小企业的财税审批与合同风控平台。它不是单纯的问答机器人，而是把业务申请、材料上传、AI 解析、规则校验、制度检索、风险分析、人工审批、付款/归档和审计追踪串成可追溯闭环。

## 规划范围（1～9）

| 编号 | 文档 | 目标 |
|---|---|---|
| 1 | [开源项目与二次开发选型](docs/01-project-overview.md) | 明确哪些能力复用、哪些能力自研 |
| 2 | [业务流程](docs/02-business-process.md) | 报销、发票、预算、审批、合同风控闭环 |
| 3 | [系统架构](docs/03-system-architecture.md) | 前后端、数据、AI 基础设施和安全边界 |
| 4 | [数据库设计](docs/04-database-design.md) | 约 36 张表的分类、核心字段和状态 |
| 5 | [Agent 设计](docs/05-agent-design.md) | LangGraph 状态、节点、工具与人工介入 |
| 6 | [API 设计](docs/06-api-design.md) | REST 接口、鉴权、错误和审计约定 |
| 7 | [前端设计](docs/07-frontend-design.md) | Vue 菜单、页面、组件和交互 |
| 8 | [部署设计](docs/08-deployment.md) | Docker Compose、环境变量和运维 |
| 9 | [Demo 与验收](docs/09-demo-test-cases.md) | 三个端到端演示和验收指标 |

## 技术基线

- 前端：Vue 3、TypeScript、Element Plus、ECharts
- 后端：FastAPI、SQLAlchemy、Pydantic
- Agent：LangGraph；模型支持 DeepSeek、Qwen、Ollama
- 文档智能：PaddleOCR、Docling/MinerU
- 数据与基础设施：MySQL、Redis、SeaweedFS（S3）、Qdrant、Docker Compose

## 推荐实施顺序

先完成基础工程和身份权限，再完成数据库与文件中心；随后实现报销主链路和确定性规则，接入 OCR/RAG，再实现 LangGraph 与合同 Agent，最后补齐前端体验、部署和验收 Demo。每阶段都应保留可运行的最小闭环。

## 重要原则

1. LLM 负责理解、抽取、解释和候选建议；金额、税率、预算、权限、状态转移等强约束由确定性规则和业务服务执行。
2. 所有外部动作遵循：`LLM → Tool → 权限检查 → 业务服务 → 数据库事务 → 审计日志`。
3. 高风险、不确定或涉及付款的节点必须 Human-in-the-loop，Agent 不得绕过人工审批。
4. 文档中的接口、表和状态是 V1 约定；实现时若需调整，必须同步更新本文档和审计记录。
