# Gemini Google AI Pro 本地交接提示模板（2026-10-06）

## 使用方式

在 Gemini 的原對話中貼上「建立任務卡」提示，補充需求後，將產生的 Markdown 任務卡放入 GitHub Private Inbox。執行完成後，把 Result Packet 或 Issue URL 貼回同一對話並使用「續談」提示。

Gemini 的 GitHub／Connected Apps 不可視為同步任務帳本；GitHub Issue 才是本案唯一可核准、稽核及回復的執行來源。

不要貼入 Token、密碼、cookie、session ID、`.env`、SSH key、本機絕對路徑或未遮蔽的私人資料。

## 建立任務卡

```text
請把我們目前已確認的工作整理成 GitHub Local Handoff Task Brief。

限制：
1. 只輸出下方固定 Markdown 格式，不呼叫 Connected App、不修改 GitHub、不捏造 repo、branch、host 或驗收結果。
2. 所有 scope 必須是 repository-relative path。
3. 缺少 Target Repo、Base Branch、Host 或驗收條件時，以 <NEEDS_USER_INPUT> 標記。
4. 不包含 Token、密碼、cookie、session ID、conversation URL、本機絕對路徑或聊天全文。
5. Origin Surface 固定為 gemini_google_ai_pro；Client 依我目前入口填 web 或 mobile。
6. 新任務 Parent Task ID 留空、Revision 填 1；後續任務填前一個 Task ID 並遞增 Revision。

固定格式：
## Task ID
<UNASSIGNED>
## Goal
<單一可驗收目標>
## Target Repo
<OWNER/repository>
## Base Branch
<branch>
## Read Scope
- <path>
## Write Scope
- <path>
## Forbidden
- secrets
- force push
- automatic merge
## Acceptance
- <可驗證條件>
## Host
<host id>
## Lane
standard
## Risk
low
## Origin Surface
gemini_google_ai_pro
## Client
web
## Parent Task ID

## Revision
1
```

## 執行結果續談

```text
以下是本地 Codex Receiver 回傳的 Result Packet。請只依據其中 evidence 與 validation_results 判斷，不補造執行結果。

請依序輸出：
1. 已完成與證據
2. 尚未完成／風險
3. 是否需要後續本地修改
4. 若需要，產生新的 child Task Brief；不得重用舊 Task ID、digest 或 nonce，Parent Task ID 指向上一任務並將 Revision 加一

<貼上已遮蔽的 Result Packet 或提供 Issue 摘要>
```

