# Rule R002: AI 幻觉信号必须被 Drishti 捕获

## 追溯
- **Principle**: P2（AI 输出质量是产品底线）
- **Evidence**: 2026-06-27，用户说"ai觉"（含错别字），旧关键字正则漏捕获；优化后正则 `(ai|AI).{0,5}(幻觉|觉)` 修复此问题

## 适用范围
- Drishti UserPromptSubmit hook 关键字配置
- 所有涉及 AI 输出质量反馈的用户消息

## 判定标准
以下用户表达必须触发 Drishti 关键字捕获：
- 明确指出："AI幻觉"、"幻觉"、"ai觉"（含错别字）
- 质量否定："你错了"、"不对"、"重新"（已在 UserPromptSubmit hook 覆盖）
- 质量要求：confidence、阈值、识别准确率

验证方式：
```bash
echo "你产生了ai觉" | grep -oiE "(ai|AI).{0,5}(幻觉|觉)|幻觉"
# 应输出: ai觉
```

## 过期条件
- 当 Gate `check-drishti-keywords.sh` 部署并覆盖所有已知表达变体后，此 Rule 退休
- 或连续 60 天无漏捕获事件时重新评估
