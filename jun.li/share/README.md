# Drishti — Claude Code 项目知识库自动维护系统

> Drishti（梵文 दृष्टि）— 直接看见的能力。

## 快速上手

```bash
bash setup.sh
```

脚本会：
1. 备份你的 `~/.claude/settings.json`
2. 注入 Drishti Hook 配置
3. 初始化四个知识库文档模板

## 文件说明

| 文件 | 用途 |
|------|------|
| `setup.sh` | 一键安装脚本 |
| `article.md` | 分享文章（含原理和对比） |
| `knowledge/` | 知识库模板（填你自己的项目内容） |
| `governance/` | 三层治理框架（可选） |

## 工作原理

```
Session 开始 → 读入知识库 → 注入给 Claude
对话过程中  → 关键字命中 → 写哨兵文件
Session 结束 → 检查哨兵  → 追加新洞见到文档
```

## 治理框架（可选）

```bash
# 验证三层治理 Gate 全部通过
bash governance/tests/run-all.sh
```

## 许可

MIT — 随意使用、修改、分享。
