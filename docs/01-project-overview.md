# 1. 开源项目与二次开发选型

## 1.1 项目定位

FinAgent 采用“业务底座复用 + Python Agent 服务自研”的方式。目标是得到一个能演示真实企业财税流程的系统，而不是把所有 Agent 代码塞进一个 OA 项目。

## 1.2 复用与自研边界

建议参考 JeecgBoot 的用户、组织、角色、菜单、权限、BPM、表单、日志和基础管理能力；如果采用其现成模块，应通过清晰的服务边界集成，不把 ExpenseAgent、ContractAgent、RuleEngine 直接改造成 Java 内部模块。

自研部分统一放在 Python/FastAPI 服务：报销和合同领域模型、规则引擎、OCR/文档解析适配器、Qdrant 检索、LangGraph 编排、审计事件和业务 API。

## 1.3 技术选型表

| 能力 | 选型 | 二次开发内容 |
|---|---|---|
| Web UI | Vue3 + TypeScript + Element Plus | 企业财税工作台、审批详情、风险面板 |
| 图表 | ECharts | 预算执行、风险分布、审批时效 |
| API | FastAPI + Pydantic | 领域 API、鉴权、统一错误和 OpenAPI |
| ORM/事务 | SQLAlchemy + MySQL | 多组织数据、状态和审计持久化 |
| Agent | LangGraph | ExpenseGraph、ContractGraph、人工中断 |
| LLM | DeepSeek / Qwen / Ollama | 统一模型适配和降级策略 |
| OCR/文档 | PaddleOCR、Docling/MinerU | 发票/合同抽取和版面保留 |
| 向量检索 | Qdrant | 制度、合同条款、历史案例知识库 |
| 缓存/队列 | Redis | 会话、幂等、任务状态、限流 |
| 文件 | SeaweedFS（S3 兼容） | 原件、解析件、版本和下载授权 |

## 1.4 开源合规与落地要求

建立 `THIRD_PARTY.md` 记录依赖、版本、许可证和修改说明；生产环境锁定版本。所有模型输出均记录模型、版本、提示词版本、输入文档版本和结果摘要，避免无法复盘。

## 1.5 阶段交付物

阶段一只要求基础项目、健康检查、用户/组织骨架、数据库迁移、SeaweedFS（S3）/Qdrant/Redis 连接和一个无需 LLM 的示例规则接口；不得以“接入模型”替代业务闭环。
