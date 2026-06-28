#!/bin/bash
# Gate: 识别接口响应 schema 必须包含 confidence 字段且值合法
# 追溯: Principle P4（契约必须被代码验证，而非被人记住）
# 毕业条件: 连续 30 天不触发后退休，或纳入 CI pipeline 后退休

INPUT="${1:-$(cat)}"

# 检查 confidence 字段存在
if ! echo "$INPUT" | jq -e 'has("confidence")' > /dev/null 2>&1; then
  echo "❌ GATE BLOCKED: 响应缺少 confidence 字段（API 契约违反）"
  exit 1
fi

# 检查 confidence 值在 [0, 1]
CONF=$(echo "$INPUT" | jq -r '.confidence')
VALID=$(echo "$CONF" | awk 'BEGIN{valid=0} /^[0-9]+(\.[0-9]+)?$/{v=$1+0; if(v>=0 && v<=1) valid=1} END{print valid}')
if [ "$VALID" != "1" ]; then
  echo "❌ GATE BLOCKED: confidence 值 '$CONF' 不在 [0,1] 范围内"
  exit 1
fi

# 检查必要字段
for field in "content" "subject"; do
  if ! echo "$INPUT" | jq -e "has(\"$field\")" > /dev/null 2>&1; then
    echo "❌ GATE BLOCKED: 响应缺少必要字段 '$field'"
    exit 1
  fi
done

echo "✅ Gate passed: API 契约验证通过（confidence=$CONF，必要字段齐全）"
exit 0
