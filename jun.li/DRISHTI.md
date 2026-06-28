# Drishti Hook System

> **Drishti**（梵文 दृष्टि）— 直接看见的能力。
>
> 灵感来自拉马努金：不记推导过程，只沉淀洞见。笔记本里全是干货，没有废话。

---

## 是什么

Drishti 是基于 Claude Code Hook 系统构建的**项目知识库自动维护机制**。

它做两件事：
- **Session 开始**：自动把项目知识库注入给 Claude，让它一开口就了解项目背景
- **Session 结束**：自动把本次对话中出现的关键洞见追加写回知识库

知识库越用越丰富，不需要手动维护。

---

## 知识库结构

```
/workshop/jun.li/knowledge/
├── PRODUCT.md     产品知识（用户、核心概念、业务规则）
├── PROJECT.md     项目状态（当前 Sprint、进行中、阻塞）
├── TECH.md        技术决策（技术栈、ADR 不可逆决策）
└── IMPROVEMENT.md 改进方向（优先级、Tech Debt、禁止事项）
```

---

## 原理

### 整体流程

```
Session 开始
    └─ SessionStart hook
          读取四个文档 → 注入给 Claude 作为上下文
          spinner: "Drishti: 读取知识库..."

对话过程中
    └─ UserPromptSubmit hook（每条消息触发）
          扫描关键字 → 命中则写入 /tmp/claude-session-keywords.txt

Claude 写文件时
    └─ PostToolUse Write|Edit hook
          touch /tmp/claude-session-had-writes（标记本次有代码改动）

Session 结束
    └─ Stop hook [command]
          检查 keywords 文件是否非空
          为空 → 直接退出，不触发 agent
    └─ Stop hook [agent]
          spinner: "Drishti: 同步洞见到知识库..."
          读关键字 → 读相关文档 → 判断去重 → 仅追加 → 清理哨兵
```

### 三条设计边界

| 边界 | 设计 | 原因 |
|------|------|------|
| **触发时机** | 只在 Session 结束触发 | 避免打断对话，批量处理 |
| **关键字过滤** | 命中预设关键字才写哨兵 | 闲聊不触发，只捕捉项目信号 |
| **文档操作** | 只追加，不修改已有内容 | 知识库只增不减，像拉马努金的笔记本 |

### 哨兵文件机制

```
/tmp/claude-session-keywords.txt   — 关键字日志，非空才触发 agent
/tmp/claude-session-had-writes     — 代码写入标记，有才触发知识库更新
```

两个文件都在 `/tmp/` 下，Session 结束时由 agent 自动清理，下次 session 重新积累。

### 关键字列表

```
AI幻觉相关：  (ai|AI).{0,5}(幻觉|觉) | 幻觉
产品相关：    confidence | 阈值 | 知识点 | 错题 | 识别 | 遗忘曲线 | 复习计划
技术相关：    DynamoDB | Bedrock | FastAPI | Lambda | ADR | tech debt | 技术债 | auth
项目相关：    sprint | 阻塞 | 上线 | 性能 | 测试覆盖
```

---

## 配置位置

Hook 配置在全局用户设置：

```
~/.claude/settings.json
```

包含以下 Hook 事件：

| 事件 | 类型 | 作用 |
|------|------|------|
| `SessionStart` | command | 读知识库注入上下文 |
| `UserPromptSubmit` | command | 关键字扫描写哨兵 |
| `PostToolUse Write\|Edit` | command | 标记代码写入 + 自动格式化 |
| `Stop` | command + agent | 门控检查 + 知识库追加 |

---

## 操作方式

### 日常使用（全自动）

正常使用 Claude Code 即可，无需任何额外操作：

```bash
claude   # 开始 session，自动读入知识库
# ... 正常对话、写代码 ...
# session 结束时自动同步洞见
```

### 当前 Session 内验证（`/test-hooks`）

由于 `UserPromptSubmit` hook 无法回溯历史消息，提供验证命令在当前 session 内模拟完整链路：

```
/test-hooks <消息内容>
```

**示例：**

```
/test-hooks 我认为识别模块会产生ai幻觉，confidence阈值需要重新设计
```

**输出示例：**

```
✅ Drishti 看见：ai幻觉,confidence,阈值 → 写入笔记本
=== Drishti 笔记本 ===
ai幻觉,confidence,阈值
🔮 Drishti: 同步洞见到知识库...
=== IMPROVEMENT.md 最后10行 ===
...
```

### 手动查看知识库

```bash
cat /workshop/jun.li/knowledge/PRODUCT.md
cat /workshop/jun.li/knowledge/PROJECT.md
cat /workshop/jun.li/knowledge/TECH.md
cat /workshop/jun.li/knowledge/IMPROVEMENT.md
```

### 手动触发同步（无需等 session 结束）

```bash
# 写入关键字
echo "DynamoDB,ADR" >> /tmp/claude-session-keywords.txt

# 查看哨兵状态
cat /tmp/claude-session-keywords.txt

# 清理哨兵（放弃本次同步）
rm -f /tmp/claude-session-keywords.txt /tmp/claude-session-had-writes
```

---

## 扩展关键字

在 `~/.claude/settings.json` 的 `UserPromptSubmit` hook 中修改 `KEYWORDS` 变量：

```bash
KEYWORDS="(ai|AI).{0,5}(幻觉|觉)|幻觉|你的新关键字|..."
```

支持标准 `grep -E` 正则语法。

---

## 扩展知识库文档

在 `SessionStart` hook 的 `FILES` 和 `LABELS` 数组中添加新文档：

```bash
FILES=("PRODUCT.md" "PROJECT.md" "TECH.md" "IMPROVEMENT.md" "新文档.md")
LABELS=("产品知识" "项目状态" "技术决策" "改进建议" "新分类")
```

同时在 Stop agent 的 prompt 中补充对应的写入规则。

---

## 设计理念

拉马努金从不记推导过程，他的笔记本里只有结论和洞见。Drishti 的设计遵循同样的原则：

- **不记录每一条对话**（不推导）
- **只捕捉关键信号**（直接看见模式）
- **沉淀到活的文档**（就是他的笔记本）
- **只追加，不涂改**（新洞见另起一行）

知识库是项目的长期记忆，不是对话的流水账。
