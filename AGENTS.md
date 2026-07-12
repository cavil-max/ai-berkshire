# AI Berkshire — Codex 指南

本仓库包含投资研究工作流、报告和共享校验工具。需同时兼容 Claude Code、
Codex 与 OpenClaw 用户。项目通用约定（报告目录结构、命名规范、投研核心原则、
GitHub 操作等）见 `CLAUDE.md`；本文件聚焦 Codex 行为、兼容性与工具链规则。

## 中文使用者交互偏好

- 默认用**中文**与用户交流：回复、解释、状态说明、提问一律用中文。
- 代码、脚本名、文件路径、命令、API 名称保持英文原样，不翻译。
- Git commit message 用中文，清楚描述改了什么（与 `CLAUDE.md` 一致）。
- 报告输出用中文（见 `CLAUDE.md`「报告语言与风格」）。
- 引用文件路径或行号时用 `src/app.ts:42` 形式，不要粘贴整文件内容。
- 遇到歧义先用简短中文提问确认，不要猜关键细节。

## 项目结构

- `skills/*.md`：Claude Code slash-command 源文件（canonical 工作流源）。
- `codex-skills/*/SKILL.md`：Codex skill 包。多数由 `skills/*.md` 生成；
  允许 Codex-only 手写包，但需明确标注且不存在同名 `skills/*.md` 源文件。
- `codex-prompts/*.md`：生成的 Codex 自定义 prompt，作为 slash-command
  兼容层；skill 仍是首选入口。
- `openclaw-skills/*/SKILL.md`：由 `scripts/sync-openclaw-skills.py` 从
  `skills/*.md` 生成的 OpenClaw skill 包，遵循 AgentSkills spec，
  默认从 `~/.openclaw/workspace/skills` 加载。
- `opencode.json`：opencode 项目配置，声明 `AGENTS.md` 为 instructions 源，
  并注册 `.opencode/skills` 为 skill 搜索路径。
- `.opencode/command/*.md`：由 `scripts/sync-opencode.py` 从 `skills/*.md`
  生成的 opencode slash commands，用 `$ARGUMENTS` 接收用户输入。
- `.opencode/skills/*/SKILL.md`：由同一脚本生成的 opencode skills，
  带自动触发描述和 opencode adapter note。
- `tools/*.py`：四套系统共用的金融校验与数据工具。`ashare_data.py` 和
  `us_fundamentals.py` 需要 pip 依赖（见 `requirements.txt`），其余零依赖。
- `requirements.txt`：Python 依赖声明（akshare、pandas、edgartools）。
  安装：`pip install -r requirements.txt`
- `reports/`：研究产出。改工具或 skill 时不要重写无关报告。
- `scripts/sync-codex-skills.py`：从 `skills/*.md` 重新生成 Codex skills。
- `scripts/sync-openclaw-skills.py`：从 `skills/*.md` 重新生成 OpenClaw skills。
- `scripts/sync-opencode.py`：从 `skills/*.md` 重新生成 opencode commands 和 skills。
- `scripts/install-codex-skills.sh` / `.bat`：本地安装 Codex skills。
- `scripts/install-openclaw-skills.sh` / `.bat`：本地安装 OpenClaw skills。
- `scripts/install-codex-prompts.sh` / `.bat`：本地安装生成的 Codex slash prompts。
- `scripts/install-claude-commands.sh` / `.bat`：本地安装 Claude Code commands。
- `scripts/install-opencode.sh` / `.bat`：本地安装 opencode commands（可选 `--skills`
  同时安装 skills）到 `~/.config/opencode/`。

## 兼容性规则

- `skills/*.md` 是 canonical 工作流源。
- 改动 `skills/` 下任何文件后，运行：
  `python3 scripts/sync-codex-skills.py`
- 需要 slash prompt 兼容时，额外运行：
  `python3 scripts/sync-codex-prompts.py`
- 需要 OpenClaw 兼容时，额外运行：
  `python3 scripts/sync-openclaw-skills.py`
- 需要 opencode 兼容时，额外运行：
  `python3 scripts/sync-opencode.py`
- 不要手动编辑生成的 `codex-skills/*/SKILL.md`、
  `openclaw-skills/*/SKILL.md` 或 `.opencode/command/*.md`、
  `.opencode/skills/*/SKILL.md`，除非同时更新对应的 `skills/` 源文件。
- `codex-skills/` 下的 Codex-only 手写包需明确标注 Codex-only；除非有意
  将该工作流也引入 Claude Code，否则不要创建同名 `skills/*.md`。
- 工具路径需兼容文档约定的 checkout 路径：`~/ai-berkshire/tools/...`
- `CLAUDE.md` 管 Claude Code 行为，本 `AGENTS.md` 管 Codex 行为。

## 研究质量规则

- 开始任何研究前，先运行 `date` 命令确认今天日期。以该日期作为"最新"数据
  （价格、市值、最近一次财报）的基线，并在报告头部写明数据截止日期。
  绝不从训练数据假设当前日期。
- skill 要求核验时，财务数据必须来自至少两个独立来源。
- 市值、估值、跨源校验、情景分析用精确算术工具：
  `python3 tools/financial_rigor.py ...`
- 研究产出视为可发布前，用报告审计工具校验：
  `python3 tools/report_audit.py ...`
- 低置信结论、不完整数据、来源缺口需明确标注。
- 本项目用于学习与研究，不构成投资建议。

## 编辑规则

- 除非任务明确要求，否则保留现有报告文件。
- 改动限定在请求的 skill、工具、脚本或文档范围内。
- 完成 skill/工具改动前，运行相关语法或生成检查。兼容性改动需运行：
  `python3 scripts/sync-codex-skills.py`
  `python3 scripts/sync-openclaw-skills.py`
  `python3 scripts/sync-opencode.py`
- 仅校验生成的 Codex 产物是否最新（不重写文件），运行：
  `python3 scripts/sync-codex-skills.py --check`
  slash prompt 相关时：
  `python3 scripts/sync-codex-prompts.py --check`
  OpenClaw skill 相关时：
  `python3 scripts/sync-openclaw-skills.py --check`
  opencode 相关时：
  `python3 scripts/sync-opencode.py --check`
