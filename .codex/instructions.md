# FinAgent Codex 实施说明

## 工作范围

你负责按 `README.md` 与 `docs/` 分阶段实现 FinAgent。当前文档是 V1 设计基线。先阅读全部文档、检查仓库现状，再实施用户明确要求的阶段；不要一次性编写全部业务代码。

## 不可擅自改变的技术路线

前端使用 Vue3 + TypeScript + Element Plus + ECharts；后端使用 FastAPI + SQLAlchemy + Pydantic；Agent 使用 LangGraph；模型适配 DeepSeek/Qwen/Ollama；向量库 Qdrant；解析使用 PaddleOCR 与 Docling/MinerU；事务数据使用 MySQL，缓存/任务使用 Redis，文件使用 MinIO，开发编排使用 Docker Compose。

## 实施规则

1. 先做可运行骨架、迁移和健康检查，再按报销、合同、Agent、前端和部署顺序推进。
2. LLM 只负责理解、抽取、分类、检索解释和候选建议；规则、权限、状态、预算、付款和事务必须在确定性业务服务中执行。
3. 所有工具调用遵循 `LLM → Tool → 权限检查 → 业务服务 → 事务 → 审计日志`，不暴露任意 SQL、任意文件路径或绕过审批的工具。
4. 涉及付款、高风险、低置信度、无证据或模型失败时必须 Human-in-the-loop。
5. 每个阶段添加测试、更新文档和 `.env.example`，不得提交真实密钥；变更数据库要同步迁移和回滚说明。
6. 保留用户已有修改，先检查 Git 状态；不使用破坏性重置命令。

## 阶段完成标准

完成后报告：改动文件、运行的检查、测试结果、未完成项和下一步建议。若需求与文档冲突，先指出冲突并采用最小改动；不要凭空替换核心技术路线。
