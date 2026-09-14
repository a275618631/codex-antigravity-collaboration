---
name: claude-inspired-artifact-design
description: 僅當使用者明確要求 Claude 風格、Claude-inspired Artifact，或接近 Claude 式的文件、簡報、UI、Dashboard、HTML、Markdown、React 等產出時使用；一般文字與設計任務不觸發。
---

# Claude 風格產出

只有明確的 Claude／Claude-inspired 要求才套用本 Skill。它提供內容優先、安靜有層次、精準自然且誠實表達限制的設計方向，不複製 Claude 或 Anthropic 的介面、商標、未公開提示詞，也不宣稱成果是官方設計。

## 執行邊界

- 先遵循使用者要求、專案與平台限制，再查證 Anthropic 官方公開提示工程文件；需要最新或精確的官方建議時，讀取 [source-priority.md](references/source-priority.md)。
- 產出 Artifact、文件、簡報或 UI 時，才讀取 [visual-artifact-guidance.md](references/visual-artifact-guidance.md) 的條件式視覺與工程細節。
- 先檢查既有架構、設計系統、內容 schema 與元件庫；只做完成任務所需的最小修改，保留既有功能與可維護性。
- 回覆先給結論，再補充依據、限制與下一步；明確區分事實、推論與待驗證事項。

## 提示與驗收

需要設計提示時，明確指定角色、任務、讀者、格式、內容邊界與驗收條件；複雜輸入可用一致的 XML 標籤分隔。完成前檢查內容正確性、可讀性、功能與專案既有 lint／typecheck／test／build 要求，僅回報實際執行或尚待驗證的項目。

## 禁止事項

- 不把 Claude 風格簡化為換色、圓角、漸層、卡片或固定版面。
- 不為風格一致而重寫無關架構、替換框架或建立不可重用的抽象層。
- 沒有官方依據時，將視覺偏好標示為本專案參考，不捏造來源或官方背書。
