# Rule: 识别接口必须返回完整 schema

## 追溯
- **Principle**: P2（AI 输出质量是产品底线）
- **Evidence**：（待积累 corrections 后填写）

## 判定标准
- 识别接口返回 JSON 包含 `confidence: number`
- 取值范围 [0, 1]
- 包含 `question_text: string`（非空）

## 过期条件
- 当 Gate `check-schema.sh` 部署后，此 rule 可退休
- 或连续 30 天无此类违规时重新评估
