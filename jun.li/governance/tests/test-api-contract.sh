#!/bin/bash
GATE="$(dirname "$0")/../gates/check-api-contract.sh"
PASS=0; FAIL=0

run_case() {
  local label="$1"; local input="$2"; local expect="$3"
  result=$(bash "$GATE" "$input" 2>&1); exit_code=$?
  if [ "$expect" = "pass" ] && [ $exit_code -eq 0 ]; then
    echo "✅ PASS [$label]"; PASS=$((PASS+1))
  elif [ "$expect" = "fail" ] && [ $exit_code -ne 0 ]; then
    echo "✅ PASS [$label] (正确拦截)"; PASS=$((PASS+1))
  else
    echo "❌ FAIL [$label] — 期望 $expect，实际 exit=$exit_code: $result"; FAIL=$((FAIL+1))
  fi
}

echo "=== R6 API 契约 Gate 测试 ==="

run_case "正例：合法响应" \
  '{"confidence":0.92,"content":"二次函数","subject":"数学"}' \
  "pass"

run_case "正例：confidence=1" \
  '{"confidence":1,"content":"积分","subject":"数学"}' \
  "pass"

run_case "反例：缺少 confidence" \
  '{"content":"二次函数","subject":"数学"}' \
  "fail"

run_case "反例：confidence 超范围" \
  '{"confidence":1.5,"content":"二次函数","subject":"数学"}' \
  "fail"

run_case "反例：缺少 content 字段" \
  '{"confidence":0.85,"subject":"数学"}' \
  "fail"

run_case "反例：空对象" \
  '{}' \
  "fail"

echo ""
echo "结果：$PASS 通过 / $FAIL 失败"
[ $FAIL -eq 0 ] && exit 0 || exit 1
