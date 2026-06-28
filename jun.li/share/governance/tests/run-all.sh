#!/bin/bash
# Drishti 治理层完整测试
# 运行所有 Gate 测试，输出汇总报告

DIR="$(dirname "$0")"
TOTAL_PASS=0
TOTAL_FAIL=0
SUITES=0

run_suite() {
  local name="$1"
  local script="$2"

  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  bash "$script"
  local code=$?
  SUITES=$((SUITES+1))
  if [ $code -eq 0 ]; then
    TOTAL_PASS=$((TOTAL_PASS+1))
    echo "→ Suite [$name]: 全部通过 ✅"
  else
    TOTAL_FAIL=$((TOTAL_FAIL+1))
    echo "→ Suite [$name]: 存在失败 ❌"
  fi
}

echo "╔══════════════════════════════════════╗"
echo "║   Drishti 治理层测试套件              ║"
echo "╚══════════════════════════════════════╝"

for f in "$DIR"/test-*.sh; do
  name=$(basename "$f" .sh | sed 's/^test-//')
  run_suite "$name" "$f"
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "总结：$TOTAL_PASS/$SUITES 个套件通过"

if [ $TOTAL_FAIL -eq 0 ]; then
  echo "✅ 所有治理 Gate 验证通过"
  exit 0
else
  echo "❌ $TOTAL_FAIL 个套件存在失败，请检查上方输出"
  exit 1
fi
