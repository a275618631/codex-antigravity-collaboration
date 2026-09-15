---
name: pr-review-agent
description: 當需要審查 PR、diff、變更檔案或程式碼修改，優先找 bug、回歸風險、缺少測試、安全風險與可行動意見時使用。
---

# 程式碼審查助手

## Trigger

使用者要求「幫我 review」、「看這個 PR」、「審查 diff」、「合併前風險檢查」時啟用。

## Input Schema

必填：
- `diff_or_changed_files`

選填：
- `test_results`
- `issue_context`
- `architecture_notes`

## Workflow

1. 檢查行為變更。
2. 找 bug、回歸風險與不安全假設。
3. 檢查缺少的測試。
4. 標記安全、資料與相容性風險。
5. 依下方 Security Routing 判定是否需要 Codex Security。
6. 整合 evidence-backed findings，產出可行動 review findings。

## Security Routing

Codex Security 是本 Skill 的安全分析工具，不是第二套 PR review 系統。一般檢查、測試、lint、secret scanner、SCA/CVE 工具與 human review 仍然必須執行。

### Level 0｜Fast Lane

適用於文件、README、typo、非敏感 UI 微調，以及不影響權限、輸入解析、資料流、依賴或外部整合的小修改。

- 執行 project tests、lint 與 deterministic secret/security checks。
- 不呼叫 Codex Security，不增加模型成本或外部 source 傳輸。

### Level 1｜Security Diff Review

只要變更涉及 authentication、authorization、API endpoint、parser、file upload、database query、external input、webhook、bot、shell/command execution、dependency、security-sensitive configuration、secrets handling、GitHub 或其他 third-party integration，就先完成一般 review，再進入 Codex Security diff 或 working-tree scan 的安全升級路由。

命令選擇：

- 已提交的 PR/branch 變更：`npx @openai/codex-security scan <repo> --diff <base> --head <head> --output-dir <outside-worktree>`。
- staged/unstaged 變更：`npx @openai/codex-security scan <repo> --working-tree --base HEAD --output-dir <outside-worktree>`。
- 首次接入或命令變更：先加 `--dry-run`；可再用 `scan --schema --format json` 取得當日 schema。

實際 scan 前必須列出 repository、target、傳輸至外部模型的範圍、認證來源類型、`output-dir`、預估成本與資料保留方式，取得人工同意後才可執行。不得要求或輸出任何 secret 值。

### Level 2｜Deep Security Review

只在 release、大型 auth/permission 改造、sandbox/agent execution、高風險 ingestion、security-critical architecture change，或使用者明確要求完整掃描時觸發。

- 使用 repository/path target 的 `--mode deep`；PR diff 不用 deep mode。
- 必須設定並記錄 workers、subagents、stop-after-no-new、max-discovery-runs 與 max-cost 上限。
- 深掃結果仍須 human review，不得自動 patch、merge、push 或阻擋 production。

## Safety and State Boundary

- 只使用官方 scoped package `@openai/codex-security`；不要使用不明來源或未加 scope 的同名 package。
- findings、reports、coverage、SARIF、history、artifacts 與 state 一律放在 Git worktree 外，且限制權限與 retention。
- 不把上述資料放入設定同步 repository、public repo 或 Git commit；只允許同步 generic routing rules、Skill、non-sensitive config template 與文件。
- Codex Security finding 不得直接觸發 production code 自動修補、merge、push 或 protected/default branch 修改。
- 若 CLI 未安裝、版本不相容、dry-run/schema 失敗或認證／權限不足，回退為既有 review 流程並明確標示未完成 Security scan，不得宣稱已掃描。

## Output Schema

輸出：
- `findings`
- `severity`
- `file_line`
- `why_it_matters`
- `suggested_fix`
- `missing_tests`
- `questions`

## Validation

- 優先回報 bug 與風險，不做風格偏好評論。
- 每個 finding 必須具體且可行動。
- 不輸出模糊建議。