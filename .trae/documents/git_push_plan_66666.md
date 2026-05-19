# Git 推送执行计划（远程仓库）

## Summary
- 目标：将当前项目中的“代码相关改动”提交并推送到远程仓库 `origin`。
- 远程：保持当前 HTTPS 地址（`https://github.com/RONALFFON/SDTMIG_RAG.git`），不切换 SSH。
- 推送策略：创建并推送新分支 `66666`，不直接推 `main`。
- Git 身份：仅在当前仓库设置 `user.name=RONALFFON`、`user.email=1669258578@qq.com`。
- 提交信息：由执行阶段根据实际暂存文件自动生成规范化 commit message。

## Current State Analysis
- 当前分支：`main`（跟踪 `origin/main`）。
- 远程配置：`origin` 已存在，且使用 HTTPS（fetch/push 均为 GitHub HTTPS）。
- 工作区存在大量变更，包含：
  - 代码与配置文件改动（应纳入本次提交）。
  - 本地/临时/IDE 文件与大文件（应排除），例如：`.idea/`、`.trae/`、`debug.log`、`SDTMIG.pdf` 等。
- 结论：需要先“选择性暂存”再提交，避免把非代码噪音推送到远程。

## Proposed Changes

### 1) 仓库级 Git 身份配置
- 文件/范围：仅 `.git/config`（通过 git 命令写入，不改全局）。
- 操作：
  - `git config user.name "RONALFFON"`
  - `git config user.email "1669258578@qq.com"`
- 原因：满足你的身份要求，并避免污染全局 Git 配置。

### 2) 创建并切换分支
- 分支：`66666`
- 操作：
  - `git checkout -b 66666`（若已存在则 `git checkout 66666`）
- 原因：按你的要求“新建分支推送”，隔离 `main` 风险。

### 3) 仅纳入代码相关文件（排除本地噪音）
- 文件策略：
  - 纳入：后端源码、前端源码、测试、必要依赖声明与项目文档（如 `api_integration.py`、`vector_db_manager.py`、`vector_retriever.py`、`rag_front/src/components/RagChat.vue`、`tests/`、`requirements.txt`、`main.py`、`README.md` 等）。
  - 排除：`.idea/`、`.trae/`、`debug.log`、`SDTMIG.pdf` 以及其他临时产物。
- 操作：
  - 先 `git add` 目标代码路径（白名单方式）。
  - 用 `git status --short` 复核暂存结果，确保未误纳入排除项。
- 原因：符合“仅代码文件”要求，并降低仓库噪音与体积。

### 4) 生成并创建提交
- 提交信息策略（自动生成）：
  - 采用简洁规范格式，例如：`feat: improve upload progress and rag pipeline reliability`
  - 若实际暂存内容偏修复，改为 `fix:` 前缀。
- 操作：
  - `git commit -m "<自动生成的提交信息>"`
- 原因：保证可读、可追溯的历史记录。

### 5) 推送到远程分支
- 操作：
  - `git push -u origin 66666`
- 原因：建立本地分支与远程分支跟踪关系，后续 push/pull 更简洁。

## Assumptions & Decisions
- 已确认决策：
  - 仅提交代码文件。
  - 保持 HTTPS 远程，不改 SSH。
  - 新建并推送分支 `66666`。
  - Git 用户信息仅配置当前仓库。
  - commit message 自动生成。
- 前置假设：
  - 当前终端具备 GitHub 认证权限（HTTPS 凭据可用）。
  - 本地不存在阻断提交的 Git hook（如有会在执行时反馈并处理）。

## Verification Steps
- 提交前校验：
  - `git status --short`：确认暂存区只含代码相关文件。
  - `git diff --cached --name-only`：复核提交文件清单。
- 推送后校验：
  - `git branch --show-current` 应为 `66666`。
  - `git remote -v` 仍为 HTTPS。
  - `git push -u origin 66666` 成功返回。
  - `git status` 显示工作区与暂存区干净（允许未纳入提交的本地文件继续存在）。

