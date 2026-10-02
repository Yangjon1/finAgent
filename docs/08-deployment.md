# 8. 部署设计

## 8.1 Docker Compose 服务

开发环境至少包含：`frontend`、`backend`、`worker`、`mysql`、`redis`、`storage`（SeaweedFS S3）、`qdrant`；可选 `ollama`。前端通过 Nginx 或开发服务器转发 `/api` 到 backend，worker 执行 OCR、文档解析和 Agent 异步任务。

## 8.2 环境变量

```env
APP_ENV=dev
SECRET_KEY=change-me-change-me-change-me-change-me
DATABASE_URL=mysql+pymysql://finagent:password@mysql:3306/finagent
REDIS_URL=redis://redis:6379/0
S3_ENDPOINT=storage:8333
S3_ACCESS_KEY=change-me
S3_SECRET_KEY=change-me
S3_BUCKET=finagent
S3_PUBLIC_ENDPOINT=http://localhost:8333
QDRANT_URL=http://qdrant:6333
LLM_PROVIDER=ollama
DEEPSEEK_API_KEY=
QWEN_API_KEY=
OLLAMA_BASE_URL=http://ollama:11434
OCR_PROVIDER=paddleocr
# PaddleOCR is installed separately when OCR execution is enabled:
# pip install -e ".[ocr]"
```

密钥只放本地 `.env` 或正式环境密钥管理，不提交真实密钥。启动顺序由健康检查控制；数据库先迁移，再启动业务 worker。

## 8.3 数据与安全

MySQL、SeaweedFS 做卷持久化和定期备份；Qdrant 索引可重建但应备份配置；Redis 不作为唯一事实来源。文件下载走短时签名 URL，限制 MIME、大小和路径；API 使用 HTTPS、CORS 白名单、限流、结构化日志和 request ID。

## 8.4 开发命令约定

```text
docker compose up -d mysql redis storage qdrant
后端迁移 → 启动 backend/worker → 启动 frontend
健康检查：/health、/ready
```

具体脚本由实现阶段补充，但必须保持本文件的服务名、端口和环境变量语义稳定。
