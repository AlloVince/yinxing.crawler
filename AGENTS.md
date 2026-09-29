<!-- agent.protocol: https://github.com/AlloVince/agent.protocol @ 0f98a089a5f3b176171a9059cc9968cbb5c1dd0f (clean v0.3.0 worktree; release tag not verified). -->

# AGENTS.md

## 项目与入口

- yinxing.crawler 是 EvaScrapy 的被动同步与 Docker 镜像发布仓，只承接已授权的 Spider 代码同步和镜像打包，不开发 Spider 业务逻辑。Spider 开发唯一源为 `/Users/allovince/Developer/EvaScrapy`。
- 使用根 `README.md` 和相关 `docs/*.md` 理解发布物及已同步 Spider；Dockerfile、CI 和 `.releaserc.json` 是构建、镜像和发布行为的原生事实。不要为本仓另建业务实现入口。
- 所属系统、职责与路由见 `/Users/allovince/Developer/yinxing.super/docs/index.md`、`../yinxing.super/docs/architecture/repositories.md` 和 `../yinxing.super/docs/architecture/subprojects.md`。NAS 部署进入 `../nas.ops/AGENTS.md` 和其正式 Compose 入口。本仓构建使用 Docker CLI（如 `docker build -t yinxing-crawler:local .`），自动发布使用 `.github/workflows/ci.yml`；不另建 Agent 私有操作路径。

## 权威、同步与验收

人类指令优先，其次是 owner 长期意图和适用 `AGENTS.md`；`owner/` 默认只读，仅当前人类明确指定具体文件修改时可写。实际行为以同步 diff、Dockerfile、CI、镜像构建和运行结果验证，README/旧计划不能替代验证。

- 同步必须得到明确授权，并保留 EvaScrapy 的本地开发副本；不得在本仓设计、重写或修复 Spider 业务逻辑。
- 发布顺序固定：先发布 EvaScrapy，再更新本仓 Dockerfile 的 `FROM`，最后发布 yinxing.crawler。CI 不证明目标镜像的运行时依赖、tag/digest 或 NAS 已拉取新镜像；这些需分别验收。
- 进入前检查 HEAD、branch、status，保护现有用户和其他 Agent 改动，不 reset、不覆盖。

## 工程默认与纪律

- 默认使用 fnm + pnpm；新项目或明确运行时升级采用最新 Node LTS，无业务要求不维护历史 Node。Python 默认 pyenv + uv，按需 venv；新项目或明确升级采用最新稳定版。
- 本仓 Python 镜像、CI 和发布机制以 Dockerfile、CI、lockfile/原生配置为准；不因默认值改 Python 镜像、CI、npm 发布流程、工具链、main 或 Git 历史。采用 SemVer、Conventional Commits 和默认 main 集成主干，已有明确项目约束优先、冲突报告，一次聚焦一个功能；除非人类要求，不 commit/push/release。
- 不混入无关重构、依赖/镜像大升级或格式化；长任务为当前功能进行必要重构不受此限制；不删除测试或忽略失败制造绿灯。新增基础能力前先检查 EvaScrapy、已有镜像层和总仓共享能力，优先复用。只有能力不足或复用破坏明确依赖/部署/数据边界时才新增并解释原因。
- 对构建/发布变更检查配置校验、生产模式、可重复构建、错误/超时、密钥、缓存和静态/文本压缩责任，CDN/反代已承担则不重复，不适用时说明；批处理或长任务应提供进度、失败原因、摘要和退出状态。

## 文档与交付

- `README.md` 与 `owner/` 面向人类；docs 只保存稳定、难从代码/配置/CLI恢复且能减少误判或重建成本的知识；不新建 memory、workflow、迁移报告或进度文档。
- 大改动先说明问题、现有能力缺口、最简方案、影响和验收；持续指导实现且难从代码恢复的设计才写普通 docs；仅高返工、真实替代方案且理由长期有用时新增 ADR。
- 代码用清晰命名、直接控制流和显式数据/副作用，避免过度抽象、复杂泛型、元编程和隐式魔法。先定义最终用户成果与 verifier，每轮按真实代码和产物自纠偏，旧计划非权威；已授权且无真实阻塞时继续。
- 每个可验证阶段结束前整理本任务累计代码/配置，不累积超长函数/文件与混杂职责，消除重复和废弃实现并保持可复核；大产物使用分块、流式或已有存储进行有界处理，格式强制的单体输入/交付保持兼容。保护不可重建输入，按需保留输入来源、生成命令和校验以便重建，清理无用可重建产物。收尾核验 diff、范围、文档、Git 状态及真实验收边界。
