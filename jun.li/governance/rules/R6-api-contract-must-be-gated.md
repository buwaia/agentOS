# Rule R6: API 契约必须有 Gate 保护

## 追溯
- **Principle**: P4（契约必须被代码验证，而非被人记住）
- **Evidence**: 2026-06-27，识别接口（/recognize）数据格式变更未被检测，上线后前端直接崩溃

## 判定标准
识别接口（/recognize）的响应 schema 必须有自动化 Gate 脚本，且上线前必须通过；缺失脚本或脚本未通过则阻断发布。

## 违规示例
上线前在 Checklist 里写"记得检查 API 格式" → 没有人执行 → 格式变了 → 前端崩溃

## 满足示例
`check-api-contract.sh` 存在且可执行，CI 流程中调用它，验证 `/recognize` 返回的 JSON 包含 `confidence` 字段且值为 [0,1]

## 过期条件
- 当 Gate `check-api-contract.sh` 稳定运行 30 天无误报后退休
- 或当 API 契约测试被正式纳入 CI pipeline 并有覆盖率要求时退休
