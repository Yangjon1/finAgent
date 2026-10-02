# FinAgent 企业财税智能审批与合同风控 Agent 平台

> 项目代号：FinAgent  
> 项目类型：企业级 AI Agent 应用 / 财税审批自动化 / 合同智能风控  
> 项目定位：真实企业业务场景复刻 + 成熟开源项目二次开发思路 + AI Agent 工程化落地  
> 当前阶段：项目设计完成，进入工程实现阶段

---

# 1. 项目概述

## 1.1 项目背景

中小企业日常经营过程中存在大量财税和审批业务，包括：

- 员工报销
- 发票提交与验真
- 发票重复报销检查
- 费用标准检查
- 部门预算检查
- 多级审批
- 财务复核
- 付款申请
- 合同审批
- 合同条款风险识别
- 合同归档
- 审计追踪

传统系统通常采用固定表单 + 固定审批流的方式实现。

这种方式能够解决基础业务流程，但对于：

- 非结构化发票
- PDF 合同
- 复杂费用说明
- 企业制度文件
- 合同条款
- 风险描述

等内容，需要大量人工阅读和判断。

因此，本项目计划构建一个基于大语言模型和 Agent 工作流的企业财税智能审批平台。

---

# 2. 项目目标

## 2.1 总体目标

构建一个能够模拟真实中小企业财税审批流程的 AI Agent 平台，实现：

```text
业务申请
    ↓
材料上传
    ↓
OCR / 文档解析
    ↓
结构化信息提取
    ↓
企业规则检查
    ↓
预算检查
    ↓
AI 风险分析
    ↓
智能审批路由
    ↓
人工审核 / 自动处理
    ↓
付款 / 归档
    ↓
审计追踪
```

最终形成一个完整的企业级 AI Agent 闭环。

---

# 3. 项目核心原则

## 3.1 Agent 不是简单聊天机器人

本项目不以“AI 聊天窗口”为核心。

Agent 的核心职责是：

```text
理解业务
↓
分析业务材料
↓
调用工具
↓
获取业务数据
↓
执行规则
↓
判断风险
↓
决定下一步流程
↓
必要时请求人工介入
```

---

## 3.2 LLM 与确定性程序职责分离

这是整个项目最重要的工程原则之一。

### LLM 负责

- 非结构化文本理解
- OCR 结果理解
- 合同条款理解
- 费用说明理解
- 企业制度语义检索
- 风险描述
- 风险原因解释
- Tool 选择
- 审批建议
- 自然语言问答

### 普通程序负责

- 金额计算
- 税额计算
- 预算计算
- 权限判断
- 用户身份判断
- 发票重复判断
- 审批金额阈值
- 审批状态流转
- 数据库事务
- 付款状态
- 审计日志

核心原则：

```text
LLM
 ↓
Tool
 ↓
Permission Check
 ↓
Business Service
 ↓
Database Transaction
 ↓
Audit Log
```

Agent 不允许直接修改数据库。

---

# 4. 项目最终业务范围

项目第一阶段主要实现两个核心业务。

## 4.1 智能报销

完整流程：

```text
员工创建报销单
    ↓
上传发票
    ↓
上传附件
    ↓
OCR
    ↓
发票字段提取
    ↓
发票验真
    ↓
重复发票检查
    ↓
费用标准检查
    ↓
部门预算检查
    ↓
企业制度 RAG
    ↓
AI 风险分析
    ↓
审批路由
    ↓
部门负责人审批
    ↓
财务审批
    ↓
付款申请
    ↓
模拟 ERP
    ↓
归档
    ↓
审计日志
```

---

# 5. 合同智能风控

合同业务流程：

```text
创建合同申请
    ↓
上传合同 PDF
    ↓
文档解析
    ↓
合同结构化提取
    ↓
合同条款识别
    ↓
企业合同制度 RAG
    ↓
确定性规则检查
    ↓
AI 风险分析
    ↓
风险等级判断
    ↓
业务负责人审批
    ↓
法务审批
    ↓
财务审批
    ↓
管理层审批
    ↓
合同归档
```

重点识别：

- 付款风险
- 预付款比例
- 违约责任
- 赔偿责任
- 验收条款
- 付款条件
- 交付时间
- 自动续约
- 单方解除
- 争议解决
- 保密条款
- 知识产权
- 合同金额

---

# 6. 技术路线

## 6.1 前端

```text
Vue 3
TypeScript
Element Plus
ECharts
Pinia
Vue Router
Axios
```

---

## 6.2 后端

```text
Python
FastAPI
SQLAlchemy
Pydantic
Alembic
```

---

## 6.3 Agent

```text
LangGraph
```

主要负责：

- Agent 状态管理
- 节点编排
- Tool Calling
- 条件路由
- Human-in-the-loop
- interrupt / resume
- Agent Trace

---

## 6.4 大模型

第一阶段支持：

```text
DeepSeek
Qwen
Ollama
```

通过统一 Model Provider 接口进行封装。

避免业务代码直接绑定某一家模型。

---

## 6.5 RAG

```text
Qdrant
Embedding Model
Document Parser
```

主要知识：

```text
企业报销制度
费用标准
差旅制度
合同模板
合同审核制度
财务制度
审批制度
```

---

## 6.6 OCR

```text
PaddleOCR
```

用于：

- 发票识别
- 图片文字识别
- OCR 字段提取

---

## 6.7 文档解析

支持：

```text
Docling
MinerU
```

主要用于：

- PDF
- Word
- 合同
- 制度文档

---

## 6.8 数据库

```text
MySQL
```

---

## 6.9 缓存

```text
Redis
```

用于：

- Session
- 缓存
- Agent 临时状态
- 异步任务
- 分布式锁

---

## 6.10 文件存储

```text
SeaweedFS（S3）
```

用于：

- 发票图片
- PDF
- 合同
- 附件
- OCR 原始文件
- Agent 相关文件

---

# 7. 系统总体架构

```text
                    Vue3
                      │
                      ▼
                 FastAPI API
                      │
                      ▼
                Agent Gateway
                      │
                      ▼
              LangGraph Orchestrator
                 │       │       │
                 ▼       ▼       ▼
          ExpenseAgent ContractAgent FinanceAgent
                 │       │       │
                 └───────┼───────┘
                         ▼
                       Tools
                         │
                         ▼
                  Business Services
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
           MySQL       Redis      SeaweedFS（S3）
              │
              ▼
        Rule / Risk Engine

              Agent
                │
        ┌───────┴────────┐
        ▼                ▼
      RAG              LLM
        │                │
        ▼                ▼
     Qdrant       DeepSeek/Qwen
```

---

# 8. 项目开发阶段

整个项目不一次性开发完成，而采用分阶段实施。

---

## Phase 0：工程基础设施

### 目标

建立可以持续开发的项目骨架。

### 工作内容

- 初始化 Git
- 创建 backend
- 创建 frontend
- 创建 docs
- 创建 Docker Compose
- 配置环境变量
- 配置 FastAPI
- 配置 Vue3
- 配置 MySQL
- 配置 Redis
- 配置 SeaweedFS（S3）
- 配置 Qdrant
- 建立基础日志系统

### 验收

```text
docker compose up
```

后核心基础设施能够正常启动。

---

# 9. Phase 1：用户认证与 RBAC

### 目标

实现企业系统最基础的权限体系。

### 功能

- 登录
- JWT
- 用户
- 角色
- 部门
- 权限
- 用户角色
- 角色权限

### 初始角色

```text
普通员工
部门负责人
财务人员
法务人员
管理人员
系统管理员
```

### 验收

不同角色登录后看到不同菜单，并且后端 API 权限检查生效。

---

# 10. Phase 2：报销基础业务

### 目标

先不引入复杂 Agent，实现传统报销业务闭环。

### 功能

- 创建报销单
- 修改报销单
- 删除报销单
- 提交报销
- 查看报销
- 上传附件
- 报销明细
- 报销状态

### 状态

```text
DRAFT
↓
SUBMITTED
↓
APPROVING
↓
APPROVED
↓
PAYING
↓
PAID
↓
ARCHIVED
```

异常：

```text
REJECTED
CANCELLED
```

---

# 11. Phase 3：文件上传与 OCR

### 目标

实现真实文件处理能力。

### 流程

```text
Vue
 ↓
FastAPI
 ↓
SeaweedFS（S3）
 ↓
Worker
 ↓
PaddleOCR
 ↓
Structured Data
 ↓
MySQL
```

### 支持

- JPG
- PNG
- PDF

### 发票核心字段

```text
invoice_code
invoice_no
invoice_date
seller_name
buyer_name
amount
tax_amount
total_amount
```

---

# 12. Phase 4：财税规则引擎

### 目标

建立确定性的业务判断能力。

### 规则

#### 发票规则

- 发票号码重复
- 发票金额异常
- 发票日期异常
- 发票状态异常

#### 报销规则

- 超费用标准
- 超单次限额
- 超月度额度
- 超部门预算

#### 权限规则

- 审批人不能审批自己
- 不同金额对应不同审批层级
- 特殊费用必须财务审核

---

# 13. Phase 5：LangGraph Expense Agent

### 目标

把前面的能力编排成真正的 Agent。

核心 Graph：

```text
START
 ↓
load_claim
 ↓
parse_documents
 ↓
extract_invoice
 ↓
verify_invoice
 ↓
check_duplicate
 ↓
retrieve_policy
 ↓
check_budget
 ↓
risk_analysis
 ↓
approval_router
 ├── LOW
 │    ↓
 │  auto_process
 │
 └── MEDIUM/HIGH
      ↓
   human_review
      ↓
   resume
      ↓
   payment
      ↓
   audit
      ↓
     END
```

---

# 14. Phase 6：RAG 企业知识库

### 目标

让 Agent 能够理解企业内部制度。

知识库内容：

```text
报销管理制度
差旅管理制度
费用标准
发票管理制度
合同管理制度
采购管理制度
审批制度
```

流程：

```text
上传制度
 ↓
文档解析
 ↓
文本切分
 ↓
Embedding
 ↓
Qdrant
 ↓
Retriever
 ↓
Agent
```

---

# 15. Phase 7：合同 Agent

### 目标

实现合同智能审核。

核心 Graph：

```text
START
 ↓
load_contract
 ↓
parse_document
 ↓
extract_contract
 ↓
extract_clauses
 ↓
retrieve_policy
 ↓
rule_check
 ↓
risk_analysis
 ↓
risk_classification
 ↓
approval_router
 ↓
human_review
 ↓
archive
 ↓
END
```

---

# 16. Phase 8：Agent 可观测性

### 目标

让用户能够看到 Agent 到底做了什么。

系统需要记录：

```text
Agent Run
Tool Call
Node
Input
Output
Latency
Token
Error
Decision
```

前端提供：

```text
Agent Run List
Agent Run Detail
Agent Trace
Tool Call Detail
```

例如：

```text
ExpenseAgent
│
├── load_claim       120ms
├── extract_invoice  850ms
├── verify_invoice   420ms
├── duplicate_check   30ms
├── retrieve_policy  260ms
├── budget_check      20ms
├── risk_analysis   1.8s
└── approval_router   15ms
```

---

# 17. Phase 9：完整业务闭环

最终将所有模块连接：

```text
员工
 ↓
报销
 ↓
发票
 ↓
OCR
 ↓
验真
 ↓
重复检查
 ↓
制度 RAG
 ↓
预算
 ↓
风险
 ↓
Agent
 ↓
审批
 ↓
财务
 ↓
付款
 ↓
审计
```

合同：

```text
业务人员
 ↓
合同
 ↓
PDF解析
 ↓
条款提取
 ↓
制度RAG
 ↓
规则检查
 ↓
AI风险分析
 ↓
审批
 ↓
法务
 ↓
财务
 ↓
管理层
 ↓
归档
```

---

# 18. 三个核心 Demo

项目最终必须至少准备三个完整演示案例。

## Demo 1：正常报销

场景：

```text
员工出差
酒店费用 380 元
企业标准 400 元
发票有效
未重复
部门预算充足
```

结果：

```text
LOW RISK
↓
正常审批
↓
财务
↓
付款
```

---

## Demo 2：超标准报销

场景：

```text
酒店费用 680 元
企业标准 400 元
```

Agent 应识别：

```text
超标准 280 元
```

进入：

```text
MEDIUM RISK
↓
人工审批
```

Agent 给出：

```text
风险原因
制度依据
超标金额
建议处理方式
```

人工批准后：

```text
interrupt
 ↓
human decision
 ↓
resume
 ↓
finance
 ↓
payment
```

---

## Demo 3：高风险合同

合同金额：

```text
850,000 元
```

包含：

```text
50% 预付款
付款条件不明确
验收条款不完整
违约责任不对称
```

Agent：

```text
HIGH RISK
```

然后：

```text
业务负责人
 ↓
法务
 ↓
财务
 ↓
管理层
```

最终形成合同风险报告。

---

# 19. 项目验收指标

## 19.1 OCR

目标：

```text
核心字段准确率 ≥ 95%
```

---

## 19.2 重复发票

测试集：

```text
重复发票识别率 = 100%
```

---

## 19.3 规则引擎

规则测试：

```text
规则判断正确率 = 100%
```

---

## 19.4 审批状态

要求：

```text
审批状态一致性 = 100%
```

不能出现：

```text
数据库显示已通过
前端显示审批中
```

等状态不一致。

---

## 19.5 高风险业务

高风险：

```text
必须人工介入
```

禁止 Agent 自动付款。

---

## 19.6 合同字段

关键字段提取：

```text
准确率 ≥ 90%
```

---

## 19.7 风险可追溯

每个 AI 风险结论必须能够追溯到：

```text
原始合同
 ↓
具体条款
 ↓
企业制度
 ↓
规则
 ↓
AI 分析
 ↓
风险结论
```

---

# 20. 项目目录规划

最终：

```text
finAgent/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── repositories/
│   │   ├── agents/
│   │   │   ├── expense/
│   │   │   ├── contract/
│   │   │   └── finance/
│   │   ├── tools/
│   │   ├── rules/
│   │   ├── rag/
│   │   └── workers/
│   │
│   └── tests/
│
├── frontend/
│
├── docs/
│
├── docker/
│
├── scripts/
│
├── .codex/
│
├── docker-compose.yml
│
├── .env.example
│
├── README.md
│
└── .gitignore
```

---

# 21. 开发顺序原则

严格遵循：

```text
基础设施
 ↓
数据库
 ↓
认证
 ↓
业务 CRUD
 ↓
文件
 ↓
OCR
 ↓
规则
 ↓
审批
 ↓
Agent
 ↓
RAG
 ↓
合同
 ↓
可观测性
 ↓
完整 Demo
```

不允许一开始直接开发复杂 Agent。

原因是：

```text
没有业务系统
→ Agent 没有真实 Tool

没有 Tool
→ Agent 只能聊天

没有规则
→ Agent 无法进行确定性判断

没有审批状态
→ 无法实现 Human-in-the-loop

没有真实数据
→ 无法验证 Agent
```

因此本项目必须遵循：

> **先构建业务系统，再把 Agent 接入业务系统。**

---

# 22. Git 分支策略

建议：

```text
main
│
├── develop
│
├── feature/auth
├── feature/expense
├── feature/ocr
├── feature/rules
├── feature/agent
├── feature/rag
└── feature/contract
```

每完成一个阶段：

```text
开发
 ↓
单元测试
 ↓
接口测试
 ↓
Demo
 ↓
Git Commit
```

---

# 23. Codex 开发原则

Codex 后续开发必须遵循以下顺序：

```text
阅读 docs/
 ↓
理解当前 Phase
 ↓
检查现有代码
 ↓
设计实现方案
 ↓
修改代码
 ↓
运行测试
 ↓
修复问题
 ↓
更新文档
 ↓
Git Commit
```

不得：

- 一次性生成整个项目
- 随意修改数据库结构
- 跳过测试
- 用 Mock 代替核心业务逻辑
- 用 LLM 替代确定性规则
- 让 Agent 直接操作数据库
- 为了“看起来像 AI”而增加无意义 Agent

---

# 24. 当前项目状态

| 模块 | 状态 |
|---|---|
| 项目定位 | 已完成 |
| 技术选型 | 已完成 |
| 业务流程 | 已完成 |
| 数据库设计 | 已完成 |
| Agent 架构 | 已完成 |
| API 设计 | 已完成 |
| 前端设计 | 已完成 |
| 部署设计 | 已完成 |
| Demo 设计 | 已完成 |
| 项目代码 | Phase 0 已完成 |
| 数据库初始化 | Phase 0 已建立 Alembic 初始迁移 |
| FastAPI | Phase 0 已完成基础骨架 |
| Vue3 | Phase 0 已完成基础布局 |
| OCR | 待开发 |
| RAG | 待开发 |
| LangGraph | 待开发 |
| 合同 Agent | 待开发 |
| 完整 Demo | 待开发 |

---

# 25. 当前第一开发任务

项目现在不要直接开发 Agent。

第一步应该执行：

```text
Phase 0
项目工程骨架
```

具体任务：

1. 初始化 Git
2. 创建 backend
3. 创建 frontend
4. 初始化 FastAPI
5. 初始化 Vue3 + TypeScript
6. 创建 `.env.example`
7. 创建 Docker Compose
8. 启动 MySQL
9. 启动 Redis
10. 启动 SeaweedFS（S3）
11. 启动 Qdrant
12. 建立数据库连接
13. 建立基础日志
14. 建立统一异常处理
15. 建立 API `/health`
16. 建立前端基础布局
17. 确认前后端能够正常通信

完成后再进入：

```text
Phase 1：认证与 RBAC
```

---

# 26. 最终项目目标

FinAgent 最终不是一个：

> “输入问题 → AI 回答”的聊天机器人。

而应该是一个：

> **能够参与真实企业财税业务流程、调用业务工具、执行确定性规则、进行风险分析、发起审批、等待人工决策并继续执行的企业级 AI Agent 系统。**

最终完整链路：

```text
                    FinAgent
                       │
        ┌──────────────┴──────────────┐
        │                             │
    ExpenseAgent                ContractAgent
        │                             │
        ▼                             ▼
    报销业务                       合同业务
        │                             │
        ▼                             ▼
 OCR / Invoice                  PDF / Clause
        │                             │
        ▼                             ▼
   Rule Engine                    Rule Engine
        │                             │
        ▼                             ▼
      RAG                           RAG
        │                             │
        ▼                             ▼
      Risk                          Risk
        │                             │
        └──────────────┬──────────────┘
                       ▼
                Approval Engine
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
          自动处理             人工审批
                                 │
                              Resume
                                 │
                                 ▼
                       Payment / Archive
                                 │
                                 ▼
                           Audit Trail
```

这就是 FinAgent 的最终产品形态。

---

# Phase 1 实施状态

Phase 1 已完成基础 RBAC 闭环：

- RBAC 表结构、SQLAlchemy 模型和 Alembic `0002_rbac` 迁移
- 角色、权限、部门和管理员初始化脚本 `backend/scripts/seed_rbac.py`
- Argon2 密码哈希和 JWT 登录
- FastAPI 当前用户、权限依赖和租户/部门/本人数据范围
- 用户、角色、权限、部门 API
- Vue 登录页、路由鉴权和 `v-permission` 按钮权限指令
- 后端认证与权限测试

Phase 3 已完成文件上传与 OCR 基础链路：

- SeaweedFS S3 预签名上传、上传确认和下载地址
- 文件 MIME、大小、对象路径和租户校验
- Redis OCR 队列与 worker
- PaddleOCR Provider 接口及 PDF 文本解析 fallback
- 文件 OCR 状态、结果、错误和任务记录持久化

Phase 1 后续部署命令：

```text
alembic upgrade head
python scripts/seed_rbac.py
```
