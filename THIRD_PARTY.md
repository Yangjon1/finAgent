# Third party dependencies

阶段一基础依赖按 `backend/pyproject.toml` 和 `frontend/package.json` 管理。对象存储使用 SeaweedFS 的 S3 兼容接口，Python 侧使用 boto3 客户端。正式发布前应锁定完整版本、补充许可证和修改说明；当前没有提交真实密钥。
