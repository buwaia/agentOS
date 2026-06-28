#!/bin/bash
# 测试 check-drishti-keywords.sh
# 验证 Rule R002: AI 幻觉信号必须被 Drishti 捕获

KEYWORDS="(ai|AI).{0,5}(幻觉|觉)|幻觉|confidence|阈值|知识点|错题|识别|遗忘曲线|复习计划|DynamoDB|Bedrock|FastAPI|Lambda|ADR|tech debt|技术债|auth|sprint|阻塞|上线|性能|测试覆盖"
PASS=0
FAIL=0

run_case() {
  local label="$1"
  local input="$2"
  local expect="$3"  # "hit" or "miss"

  matched=$(echo "$input" | grep -oiE "$KEYWORDS" | sort -u | tr '\n' ',')

  if [ "$expect" = "hit" ] && [ -n "$matched" ]; then
    echo "✅ PASS [$label] 命中: $matched"
    PASS=$((PASS+1))
  elif [ "$expect" = "miss" ] && [ -z "$matched" ]; then
    echo "✅ PASS [$label] 正确跳过"
    PASS=$((PASS+1))
  else
    echo "❌ FAIL [$label] 期望=$expect 实际=$([ -n "$matched" ] && echo "命中:$matched" || echo 未命中)"
    FAIL=$((FAIL+1))
  fi
}

echo "=== R002 Drishti 关键字捕获测试 ==="
echo ""
echo "--- AI幻觉变体（应命中）---"
run_case "标准写法"       "你产生了AI幻觉"              "hit"
run_case "小写"           "你产生了ai幻觉"              "hit"
run_case "缺字错别字"     "你产生了ai觉"               "hit"
run_case "中间有空格"     "AI 幻觉问题"                "hit"
run_case "单独幻觉"       "这是幻觉"                   "hit"
run_case "人工智能幻觉"   "人工智能幻觉问题很严重"       "hit"

echo ""
echo "--- 产品关键字（应命中）---"
run_case "confidence"     "confidence阈值设为0.8"      "hit"
run_case "阈值"           "阈值需要重新设计"            "hit"
run_case "识别"           "识别准确率太低了"            "hit"
run_case "DynamoDB"       "DynamoDB查询性能问题"        "hit"
run_case "tech debt"      "这是tech debt需要解决"       "hit"

echo ""
echo "--- 无关内容（应跳过）---"
run_case "数学证明"       "帮我证明琴生不等式"          "miss"
run_case "日常问候"       "你好今天天气不错"            "miss"
run_case "拉马努金"       "用拉马努金方式解答"          "miss"
run_case "几何解答"       "用半圆几何类比来证明"        "miss"

echo ""
echo "结果：$PASS 通过 / $FAIL 失败"
[ $FAIL -eq 0 ] && exit 0 || exit 1
