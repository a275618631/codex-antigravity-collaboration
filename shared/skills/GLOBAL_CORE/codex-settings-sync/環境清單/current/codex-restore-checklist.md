# Codex 環境重建清單

此清單只記錄安裝、設定、登入與驗證步驟；不包含秘密值、登入 session 或本機絕對路徑。

## openaiDeveloperDocs

- 類別：mcp_server
- 目前狀態：configured_not_installed
- 登入需求：not_required
- [ ] 在目標電腦安裝或確認 MCP 執行檔
- [ ] 依 command_template 重新建立 Codex MCP 設定
- [ ] 重新啟動 Codex
- [ ] 執行 codex mcp get 
- [ ] openaiDeveloperDocs
- [ ] 依 verification 欄位重新驗證 initialize 與 tools/list

## context7

- 類別：mcp_server
- 目前狀態：ready
- 登入需求：not_required
- [ ] 在目標電腦安裝或確認 MCP 執行檔
- [ ] 依 command_template 重新建立 Codex MCP 設定
- [ ] 重新啟動 Codex
- [ ] 執行 codex mcp get 
- [ ] context7
- [ ] 依 verification 欄位重新驗證 initialize 與 tools/list

## node_repl

- 類別：mcp_server
- 目前狀態：ready
- 登入需求：manual_verification_required
- [ ] 在目標電腦安裝或確認 MCP 執行檔
- [ ] 依 command_template 重新建立 Codex MCP 設定
- [ ] 重新啟動 Codex
- [ ] 執行 codex mcp get 
- [ ] node_repl
- [ ] 依 verification 欄位重新驗證 initialize 與 tools/list

## headroom

- 類別：mcp_server
- 目前狀態：ready
- 登入需求：manual_verification_required
- [ ] 在目標電腦安裝或確認 MCP 執行檔
- [ ] 依 command_template 重新建立 Codex MCP 設定
- [ ] 重新啟動 Codex
- [ ] 執行 codex mcp get 
- [ ] headroom
- [ ] 依 verification 欄位重新驗證 initialize 與 tools/list

## notion

- 類別：mcp_server
- 目前狀態：configured_not_installed
- 登入需求：not_required
- [ ] 在目標電腦安裝或確認 MCP 執行檔
- [ ] 依 command_template 重新建立 Codex MCP 設定
- [ ] 重新啟動 Codex
- [ ] 執行 codex mcp get 
- [ ] notion
- [ ] 依 verification 欄位重新驗證 initialize 與 tools/list

## agent_bridge

- 類別：mcp_server
- 目前狀態：ready
- 登入需求：not_required
- [ ] 在目標電腦安裝或確認 MCP 執行檔
- [ ] 依 command_template 重新建立 Codex MCP 設定
- [ ] 重新啟動 Codex
- [ ] 執行 codex mcp get 
- [ ] agent_bridge
- [ ] 依 verification 欄位重新驗證 initialize 與 tools/list

## officecli

- 類別：mcp_server
- 目前狀態：ready
- 登入需求：not_required
- [ ] 在目標電腦安裝或確認 MCP 執行檔
- [ ] 依 command_template 重新建立 Codex MCP 設定
- [ ] 重新啟動 Codex
- [ ] 執行 codex mcp get 
- [ ] officecli
- [ ] 依 verification 欄位重新驗證 initialize 與 tools/list

## ollama

- 類別：mcp_server
- 目前狀態：ready
- 登入需求：not_required
- [ ] 在目標電腦安裝或確認 MCP 執行檔
- [ ] 依 command_template 重新建立 Codex MCP 設定
- [ ] 重新啟動 Codex
- [ ] 執行 codex mcp get 
- [ ] ollama
- [ ] 依 verification 欄位重新驗證 initialize 與 tools/list

## codex

- 類別：cli_tool
- 目前狀態：ready
- 登入需求：not_required
- [ ] 確認或安裝 codex 執行 codex --version

## gh

- 類別：cli_tool
- 目前狀態：ready
- 登入需求：expired_or_invalid
- [ ] 確認或安裝 gh 執行 gh --version

## git

- 類別：cli_tool
- 目前狀態：ready
- 登入需求：not_required
- [ ] 確認或安裝 git 執行 git --version

## python

- 類別：cli_tool
- 目前狀態：unknown
- 登入需求：not_required
- [ ] 確認或安裝 python 執行 python --version

## py

- 類別：cli_tool
- 目前狀態：ready
- 登入需求：not_required
- [ ] 確認或安裝 py 執行 py --version

## pwsh

- 類別：cli_tool
- 目前狀態：ready
- 登入需求：not_required
- [ ] 確認或安裝 pwsh 執行 pwsh --version

## node

- 類別：cli_tool
- 目前狀態：ready
- 登入需求：not_required
- [ ] 確認或安裝 node 執行 node --version

## npm

- 類別：cli_tool
- 目前狀態：ready
- 登入需求：not_required
- [ ] 確認或安裝 npm 執行 npm --version

## GitHub

- 類別：external_service
- 目前狀態：login_required
- 登入需求：expired_or_invalid
- [ ] 安裝 GitHub CLI
- [ ] 執行 gh auth login
- [ ] 執行 gh auth status

## OpenAI Codex

- 類別：external_service
- 目前狀態：login_required
- 登入需求：manual_verification_required
- [ ] 安裝 Codex
- [ ] 在 Codex UI／CLI 重新登入
- [ ] 執行 Codex 的唯讀狀態檢查

## artifact-storage-policy

- 類別：codex_skill
- 目前狀態：ready
- 登入需求：not_required
- [ ] 從同步 repo 的 skills 分類套用或重新安裝此自訂 skill

## autonomous-repair

- 類別：codex_skill
- 目前狀態：ready
- 登入需求：not_required
- [ ] 從同步 repo 的 skills 分類套用或重新安裝此自訂 skill

## checklist-validator

- 類別：codex_skill
- 目前狀態：ready
- 登入需求：not_required
- [ ] 從同步 repo 的 skills 分類套用或重新安裝此自訂 skill

## claude-inspired-artifact-design

- 類別：codex_skill
- 目前狀態：ready
- 登入需求：not_required
- [ ] 從同步 repo 的 skills 分類套用或重新安裝此自訂 skill

## code-generation-agent

- 類別：codex_skill
- 目前狀態：ready
- 登入需求：not_required
- [ ] 從同步 repo 的 skills 分類套用或重新安裝此自訂 skill

## codex-settings-sync

- 類別：codex_skill
- 目前狀態：ready
- 登入需求：not_required
- [ ] 從同步 repo 的 skills 分類套用或重新安裝此自訂 skill

## context-pack-builder

- 類別：codex_skill
- 目前狀態：ready
- 登入需求：not_required
- [ ] 從同步 repo 的 skills 分類套用或重新安裝此自訂 skill

## data-analyst-agent

- 類別：codex_skill
- 目前狀態：ready
- 登入需求：not_required
- [ ] 從同步 repo 的 skills 分類套用或重新安裝此自訂 skill

## decision-log-agent

- 類別：codex_skill
- 目前狀態：ready
- 登入需求：not_required
- [ ] 從同步 repo 的 skills 分類套用或重新安裝此自訂 skill

## documentation-agent

- 類別：codex_skill
- 目前狀態：ready
- 登入需求：not_required
- [ ] 從同步 repo 的 skills 分類套用或重新安裝此自訂 skill

## email-triage-agent

- 類別：codex_skill
- 目前狀態：ready
- 登入需求：not_required
- [ ] 從同步 repo 的 skills 分類套用或重新安裝此自訂 skill

## engineering-manager-agent

- 類別：codex_skill
- 目前狀態：ready
- 登入需求：not_required
- [ ] 從同步 repo 的 skills 分類套用或重新安裝此自訂 skill

## error-observability

- 類別：codex_skill
- 目前狀態：ready
- 登入需求：not_required
- [ ] 從同步 repo 的 skills 分類套用或重新安裝此自訂 skill

## file-organizer

- 類別：codex_skill
- 目前狀態：ready
- 登入需求：not_required
- [ ] 從同步 repo 的 skills 分類套用或重新安裝此自訂 skill

## knowledge-base-builder

- 類別：codex_skill
- 目前狀態：ready
- 登入需求：not_required
- [ ] 從同步 repo 的 skills 分類套用或重新安裝此自訂 skill

## legacy-code-analysis

- 類別：codex_skill
- 目前狀態：ready
- 登入需求：not_required
- [ ] 從同步 repo 的 skills 分類套用或重新安裝此自訂 skill

## meeting-action-agent

- 類別：codex_skill
- 目前狀態：ready
- 登入需求：not_required
- [ ] 從同步 repo 的 skills 分類套用或重新安裝此自訂 skill

## ml-engineer-agent

- 類別：codex_skill
- 目前狀態：ready
- 登入需求：not_required
- [ ] 從同步 repo 的 skills 分類套用或重新安裝此自訂 skill

## notion-template-router

- 類別：codex_skill
- 目前狀態：ready
- 登入需求：not_required
- [ ] 從同步 repo 的 skills 分類套用或重新安裝此自訂 skill

## output-contract

- 類別：codex_skill
- 目前狀態：ready
- 登入需求：not_required
- [ ] 從同步 repo 的 skills 分類套用或重新安裝此自訂 skill

## personal-task-router

- 類別：codex_skill
- 目前狀態：ready
- 登入需求：not_required
- [ ] 從同步 repo 的 skills 分類套用或重新安裝此自訂 skill

## portable-tool-delivery

- 類別：codex_skill
- 目前狀態：ready
- 登入需求：not_required
- [ ] 從同步 repo 的 skills 分類套用或重新安裝此自訂 skill

## pr-review-agent

- 類別：codex_skill
- 目前狀態：ready
- 登入需求：not_required
- [ ] 從同步 repo 的 skills 分類套用或重新安裝此自訂 skill

## preventive-repair

- 類別：codex_skill
- 目前狀態：ready
- 登入需求：not_required
- [ ] 從同步 repo 的 skills 分類套用或重新安裝此自訂 skill

## project-manager-agent

- 類別：codex_skill
- 目前狀態：ready
- 登入需求：not_required
- [ ] 從同步 repo 的 skills 分類套用或重新安裝此自訂 skill

## prompt-portability

- 類別：codex_skill
- 目前狀態：ready
- 登入需求：not_required
- [ ] 從同步 repo 的 skills 分類套用或重新安裝此自訂 skill

## rca-agent

- 類別：codex_skill
- 目前狀態：ready
- 登入需求：not_required
- [ ] 從同步 repo 的 skills 分類套用或重新安裝此自訂 skill

## report-writer-agent

- 類別：codex_skill
- 目前狀態：ready
- 登入需求：not_required
- [ ] 從同步 repo 的 skills 分類套用或重新安裝此自訂 skill

## research-synthesizer

- 類別：codex_skill
- 目前狀態：ready
- 登入需求：not_required
- [ ] 從同步 repo 的 skills 分類套用或重新安裝此自訂 skill

## save-to-notion

- 類別：codex_skill
- 目前狀態：ready
- 登入需求：not_required
- [ ] 從同步 repo 的 skills 分類套用或重新安裝此自訂 skill

## skill-evaluator

- 類別：codex_skill
- 目前狀態：ready
- 登入需求：not_required
- [ ] 從同步 repo 的 skills 分類套用或重新安裝此自訂 skill

## task-router

- 類別：codex_skill
- 目前狀態：ready
- 登入需求：not_required
- [ ] 從同步 repo 的 skills 分類套用或重新安裝此自訂 skill

## visual-response

- 類別：codex_skill
- 目前狀態：ready
- 登入需求：not_required
- [ ] 從同步 repo 的 skills 分類套用或重新安裝此自訂 skill

## web-research-citation

- 類別：codex_skill
- 目前狀態：ready
- 登入需求：not_required
- [ ] 從同步 repo 的 skills 分類套用或重新安裝此自訂 skill

## work-report-delivery

- 類別：codex_skill
- 目前狀態：ready
- 登入需求：not_required
- [ ] 從同步 repo 的 skills 分類套用或重新安裝此自訂 skill

## workflow-automation-agent

- 類別：codex_skill
- 目前狀態：ready
- 登入需求：not_required
- [ ] 從同步 repo 的 skills 分類套用或重新安裝此自訂 skill

## writing-style-intake

- 類別：codex_skill
- 目前狀態：ready
- 登入需求：not_required
- [ ] 從同步 repo 的 skills 分類套用或重新安裝此自訂 skill

