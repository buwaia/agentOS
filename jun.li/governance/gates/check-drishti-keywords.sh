#!/bin/bash
# Gate: 验证 Drishti 关键字捕获覆盖已知 AI 幻觉表达
# 追溯: Principle P2 "AI 输出质量是产品底线"
# 蒸馏自: R002-ai-hallucination-must-be-captured
# 毕业条件: 连续 60 天无漏捕获事件后退休

KEYWORDS="(ai|AI).{0,5}(幻觉|觉)|幻觉|confidence|阈值|知识点|错题|识别|遗忘曲线|复习计划|DynamoDB|Bedrock|FastAPI|Lambda|ADR|tech debt|技术债|auth|sprint|阻塞|上线|性能|测试覆盖"

# 测试用例：已知应该被捕获的表达
TEST_CASES=(
  "你产生了ai觉"
  "你有AI幻觉"
  "这是幻觉"
  "confidence阈值需要调整"
  "识别准确率太低"
)

PASS=0
FAIL=0

for msg in "${TEST_CASES[@]}"; do
  matched=$(echo "$msg" | grep -oiE "$KEYWORDS" | sort -u | tr '\n' ',')
  if [ -n "$matched" ]; then
    echo "✅ 命中 [$matched]：$msg"
    PASS=$((PASS + 1))
  else
    echo "❌ 漏捕获：$msg"
    FAIL=$((FAIL + 1))
  fi
done

echo ""
echo "结果：$PASS 通过 / $FAIL 漏捕获"

if [ "$FAIL" -gt 0 ]; then
  echo "❌ GATE BLOCKED: 存在漏捕获，请更新 KEYWORDS 正则（P2 违规）"
  exit 1
fi

echo "✅ Gate passed: 所有已知 AI 幻觉表达均可被捕获"
exit 0
