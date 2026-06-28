#!/bin/bash
# Drishti 一键安装脚本
# 将 Drishti Hook 配置合并进 ~/.claude/settings.json

set -e

SETTINGS="$HOME/.claude/settings.json"
KNOWLEDGE_DIR="$(pwd)/knowledge"
BACKUP="$HOME/.claude/settings.backup.$(date +%Y%m%d%H%M%S).json"

echo "╔══════════════════════════════════════╗"
echo "║   Drishti 安装向导                   ║"
echo "╚══════════════════════════════════════╝"
echo ""

# 检查依赖
for cmd in jq bash; do
  if ! command -v $cmd &>/dev/null; then
    echo "❌ 缺少依赖: $cmd，请先安装"
    exit 1
  fi
done
echo "✅ 依赖检查通过"

# 备份现有配置
if [ -f "$SETTINGS" ]; then
  cp "$SETTINGS" "$BACKUP"
  echo "✅ 已备份现有配置 → $BACKUP"
else
  echo "{}" > "$SETTINGS"
  echo "✅ 创建新配置文件"
fi

# 知识库目标路径
read -rp "知识库存放路径 [默认: $KNOWLEDGE_DIR]: " input_dir
KNOWLEDGE_DIR="${input_dir:-$KNOWLEDGE_DIR}"
mkdir -p "$KNOWLEDGE_DIR"
echo "✅ 知识库路径: $KNOWLEDGE_DIR"

# 写入 hooks 配置
HOOK_SESSION_START='KDIR="'"$KNOWLEDGE_DIR"'"; FILES=("PRODUCT.md" "PROJECT.md" "TECH.md" "IMPROVEMENT.md"); LABELS=("产品知识" "项目状态" "技术决策" "改进建议"); ctx="## 项目知识库\\n"; found=0; for i in "${!FILES[@]}"; do f="$KDIR/${FILES[$i]}"; if [ -f "$f" ] && [ -s "$f" ]; then ctx="$ctx\\n### ${LABELS[$i]}\\n$(cat $f)\\n"; found=1; fi; done; if [ "$found" = "1" ]; then jq -n --arg c "$ctx" '"'"'{hookSpecificOutput:{hookEventName:"SessionStart",additionalContext:$c}}'"'"'; else echo "{}"; fi'

HOOK_KEYWORD='msg=$(cat | jq -r ".user_message // .prompt // .content // empty" 2>/dev/null || true); [ -z "$msg" ] && exit 0; KEYWORDS="(ai|AI).{0,5}(幻觉|觉)|幻觉|confidence|阈值|知识点|错题|识别|遗忘曲线|复习计划|DynamoDB|Bedrock|FastAPI|Lambda|ADR|tech debt|技术债|auth|sprint|阻塞|上线|性能|测试覆盖"; matched=$(echo "$msg" | grep -oiE "$KEYWORDS" | sort -u | tr '"'"'\\n'"'"' '"'"','"'"' | sed '"'"'s/,$//'"'"'); [ -n "$matched" ] && echo "$matched" >> /tmp/claude-session-keywords.txt; exit 0'

HOOK_POST_TOOL='touch /tmp/claude-session-had-writes 2>/dev/null; exit 0'

HOOK_STOP_GATE='[ -s /tmp/claude-session-keywords.txt ] || exit 0'

HOOK_STOP_AGENT="读取文件 /tmp/claude-session-keywords.txt 获取关键字列表。然后根据关键字判断需要更新哪些知识库文档（$KNOWLEDGE_DIR/PRODUCT.md、PROJECT.md、TECH.md、IMPROVEMENT.md）。规则：1. 先读取目标文档现有内容；2. 检查是否已有相似条目（去重）；3. 仅追加新洞见，不修改已有内容；4. 每个洞见带日期标记；5. 操作完成后删除 /tmp/claude-session-keywords.txt 和 /tmp/claude-session-had-writes。"

# 用 jq 合并配置
TEMP="$(mktemp)"
jq --arg ss "$HOOK_SESSION_START" \
   --arg kw "$HOOK_KEYWORD" \
   --arg pt "$HOOK_POST_TOOL" \
   --arg sg "$HOOK_STOP_GATE" \
   --arg sa "$HOOK_STOP_AGENT" \
   '.hooks.SessionStart = [{"hooks":[{"type":"command","command":$ss,"statusMessage":"Drishti: 读取知识库..."}]}]
  | .hooks.UserPromptSubmit = [{"hooks":[{"type":"command","command":$kw}]}]
  | .hooks.PostToolUse = (.hooks.PostToolUse // []) + [{"matcher":"Write|Edit","hooks":[{"type":"command","command":$pt}]}]
  | .hooks.Stop = [{"hooks":[{"type":"command","command":$sg},{"type":"agent","prompt":$sa,"statusMessage":"Drishti: 同步洞见到知识库..."}]}]
' "$SETTINGS" > "$TEMP" && mv "$TEMP" "$SETTINGS"

echo "✅ Hook 配置写入完成"

# 初始化知识库文档（如果不存在）
init_doc() {
  local file="$KNOWLEDGE_DIR/$1"
  local title="$2"
  if [ ! -f "$file" ]; then
    echo "# $title" > "$file"
    echo "" >> "$file"
    echo "> 使用 Claude Code 时自动维护。请填写你的项目内容。" >> "$file"
    echo "✅ 初始化: $1"
  else
    echo "⏭  已存在: $1 (跳过)"
  fi
}

echo ""
echo "初始化知识库文档..."
init_doc "PRODUCT.md"     "产品知识"
init_doc "PROJECT.md"     "项目状态"
init_doc "TECH.md"        "技术决策"
init_doc "IMPROVEMENT.md" "改进方向"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Drishti 安装完成！"
echo ""
echo "下一步："
echo "  1. 编辑 $KNOWLEDGE_DIR/ 下四个文档，填入你的项目内容"
echo "  2. 重启 claude 或运行 /hooks 刷新配置"
echo "  3. 正常使用 Claude Code，知识库自动维护"
echo ""
echo "如需回滚，恢复备份："
echo "  cp $BACKUP $SETTINGS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
