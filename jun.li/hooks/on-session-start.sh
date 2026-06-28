#!/bin/bash
# 触发时机：Claude Code session 启动时
# 做什么：注入 Knowledge 到 context

AGENTOS_DIR="$(dirname "$(dirname "$0")")"

echo "=== PRINCIPLES (最高优先级约束) ==="
cat "$AGENTOS_DIR/governance/principles.md"
echo ""

echo "=== CURRENT ENGINE STATE ==="
cat "$AGENTOS_DIR/engine/STATE.md"
echo ""

echo "=== DOMAIN KNOWLEDGE (摘要) ==="
for doc in PRODUCT TECH IMPROVEMENT PROJECT; do
  if [ -f "$AGENTOS_DIR/knowledge/$doc.md" ]; then
    echo "--- $doc ---"
    head -15 "$AGENTOS_DIR/knowledge/$doc.md"
    echo "..."
    echo ""
  fi
done

echo "=== Health Status ==="
bash "$AGENTOS_DIR/knowledge/health.sh" 2>/dev/null | tail -5
