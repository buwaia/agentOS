#!/bin/bash
# Knowledge 系统健康检查

AGENTOS_DIR="$(dirname "$(dirname "$0")")"
WARNINGS=0
ERRORS=0

echo "=== Knowledge Health Check ==="
echo ""

# 1. 新鲜度检查
echo "Freshness Check:"
for doc in PRODUCT TECH IMPROVEMENT PROJECT; do
  FILE="$AGENTOS_DIR/knowledge/$doc.md"
  if [ -f "$FILE" ]; then
    DAYS_OLD=$(( ($(date +%s) - $(stat -c %Y "$FILE" 2>/dev/null || stat -f %m "$FILE" 2>/dev/null)) / 86400 ))
    if [ "$doc" = "PROJECT" ] && [ "$DAYS_OLD" -gt 3 ]; then
      echo "  WARNING $doc.md: ${DAYS_OLD} days old (threshold: 3)"
      WARNINGS=$((WARNINGS + 1))
    elif [ "$DAYS_OLD" -gt 14 ]; then
      echo "  WARNING $doc.md: ${DAYS_OLD} days old (threshold: 14)"
      WARNINGS=$((WARNINGS + 1))
    else
      echo "  OK $doc.md: ${DAYS_OLD} days old"
    fi
  else
    echo "  ERROR $doc.md: MISSING"
    ERRORS=$((ERRORS + 1))
  fi
done
echo ""

# 2. 体积检查
echo "Size Check:"
TOTAL_WORDS=0
for f in $(find "$AGENTOS_DIR/knowledge" "$AGENTOS_DIR/governance" -name "*.md" 2>/dev/null); do
  WORDS=$(wc -w < "$f")
  TOTAL_WORDS=$((TOTAL_WORDS + WORDS))
done
ESTIMATED_TOKENS=$((TOTAL_WORDS * 4 / 3))
echo "  Total words: $TOTAL_WORDS"
echo "  Estimated tokens: ~$ESTIMATED_TOKENS"
if [ "$ESTIMATED_TOKENS" -gt 15000 ]; then
  echo "  WARNING Exceeds injection budget (15K). Consider distilling."
  WARNINGS=$((WARNINGS + 1))
else
  echo "  OK Within budget"
fi
echo ""

# 3. Rules 数量检查
echo "Rules Check:"
ACTIVE_COUNT=$(find "$AGENTOS_DIR/governance/rules" -maxdepth 1 -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
RETIRED_COUNT=$(find "$AGENTOS_DIR/governance/rules/_retired" -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
echo "  Active rules: $ACTIVE_COUNT"
echo "  Retired rules: $RETIRED_COUNT"
if [ "$ACTIVE_COUNT" -gt 15 ]; then
  echo "  WARNING Too many active rules (>15). Distill needed."
  WARNINGS=$((WARNINGS + 1))
fi
echo ""

# 4. Corrections log 检查
echo "Corrections Log:"
LOG="$AGENTOS_DIR/corrections.log"
if [ -f "$LOG" ]; then
  COUNT=$(grep -c "CORRECTION:" "$LOG" 2>/dev/null || echo 0)
  echo "  Corrections captured: $COUNT"
else
  echo "  WARNING corrections.log missing"
  WARNINGS=$((WARNINGS + 1))
fi
echo ""

# Summary
echo "=== Summary ==="
echo "  Warnings: $WARNINGS | Errors: $ERRORS"
if [ "$ERRORS" -gt 0 ]; then
  echo "  UNHEALTHY - fix errors before proceeding"
  exit 1
elif [ "$WARNINGS" -gt 2 ]; then
  echo "  DEGRADED - schedule maintenance"
  exit 2
else
  echo "  HEALTHY"
  exit 0
fi
