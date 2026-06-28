# Drishti — 知识库提炼

You are a project knowledge base maintainer. Review the current conversation for actionable knowledge, then update the knowledge files.

## Steps

0. **扫描 Engine 蒸馏事件**（在读对话之前先做）

   查询今天和昨天的蒸馏事件：

   ```bash
   TODAY=$(date -u +%Y-%m-%d)
   YESTERDAY=$(date -u -d "yesterday" +%Y-%m-%d 2>/dev/null || date -u -v-1d +%Y-%m-%d)
   aws dynamodb query \
     --table-name DeliveryEngineLocal \
     --region us-east-1 \
     --key-condition-expression "PK = :pk" \
     --expression-attribute-values "{\":pk\":{\"S\":\"DISTILL#${TODAY}\"}}" \
     --output json 2>/dev/null
   aws dynamodb query \
     --table-name DeliveryEngineLocal \
     --region us-east-1 \
     --key-condition-expression "PK = :pk" \
     --expression-attribute-values "{\":pk\":{\"S\":\"DISTILL#${YESTERDAY}\"}}" \
     --output json 2>/dev/null
   ```

   分析事件，寻找以下模式：
   - 同一 `event` 出现 ≥ 3 次 → 系统性问题
   - `G2_REJECTED` 集中在某个 `problem` 关键词 → 该类题路径质量差
   - `G3_PASSED` 的 `problem_type` 分布 → 了解使用场景
   - Gate 失败事件（`G3_FAILED`、`G4_FAILED`）→ 优先蒸馏

   如果发现系统性模式，在报告末尾追加：

   ```
   ## Engine 蒸馏建议
   发现模式：[描述]
   建议运行：/sara [事件描述，供 sara 蒸馏成 Rule]
   ```

1. **Scan the conversation** for:
   - New technical decisions or architecture changes
   - Project status updates (blockers, completions, deadlines)
   - Product requirement changes
   - Improvement suggestions or lessons learned

2. **Read relevant files** in `/workshop/jun.li/knowledge/`:
   - `TECH.md` — technical decisions and ADRs
   - `PROJECT.md` — project status and sprint state
   - `PRODUCT.md` — product requirements
   - `IMPROVEMENT.md` — improvement suggestions

   Only read files that are relevant to what you found.

3. **Append only new information** — do not modify or rewrite existing lines.
   - Add new ADR entries under the appropriate section
   - Add new incidents or decisions with dates (format: `YYYY-MM-DD`)
   - Add new improvement suggestions with context

4. **Check sentinel file**: if `/tmp/claude-session-keywords.txt` exists, read it (shows topics discussed this session), then delete it.

5. **Report** one line per file updated, e.g.:
   - `TECH.md: appended ADR-004 (Redis caching decision)`
   - `IMPROVEMENT.md: appended 2 suggestions from session`
   - Or: `no update needed`
