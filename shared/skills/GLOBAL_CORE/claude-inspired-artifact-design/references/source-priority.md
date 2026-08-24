# 來源優先序與對照

## 使用方式

需要更新提示工程規則、確認 Anthropic 是否公開某項建議，或使用者要求「官方提示詞」時，先查閱下列官方文件。官方文件可能隨模型與產品版本更新；不要把本檔案的摘要視為永久規格。

1. 使用者當前要求與專案規則。
2. Anthropic 官方公開提示工程文件。
3. 使用者提供的本地 PDF，作為本專案的 Claude-inspired 視覺與 Artifact 參考。
4. 一般設計與工程判斷。

## Anthropic 官方來源

- Prompting best practices：<https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices>
- Prompt engineering overview：<https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/overview>
- Anthropic Prompt Library 入口：<https://docs.anthropic.com/en/prompt-library>
- Anthropic Prompt Generator 說明：<https://www.anthropic.com/news/prompt-generator>

目前可直接採用的官方方向包括：清楚直接地寫出任務與輸出；補充背景與動機；使用相關、多樣、結構化的範例；用一致的 XML 標籤區分指令、背景、輸入與範例；依需要設定角色；讓提示格式接近希望得到的輸出格式；在複雜任務完成前依驗收條件自我檢查。這些是提示工程建議，不等於官方視覺品牌規範。

## 使用者提供的本地參考

- 使用者提供的「Claude-inspired Artifact 產出規範」PDF（本移植包不攜帶本機檔案路徑）
- 使用者提供的「介面設計優化指引」PDF（本移植包不攜帶本機檔案路徑）

兩份 PDF 的共同方向是：內容優先；安靜而有層次的視覺語言；結論先行；避免過度卡片化、漸層、陰影、裝飾與無意義動畫；使用共用 token、內容 schema、可重用元件與依媒介選擇的範本；保留現有架構並以 lint、typecheck、test、build、響應式、可及性與視覺檢查驗證。這些內容應標示為使用者／本專案參考，不應寫成 Anthropic 官方承諾。

## 衝突處理

- 官方提示工程建議與本地 PDF 衝突時，官方提示工程建議優先；例如官方要求明確、正向、可驗收的輸出，不能被「只要有 Claude 感即可」取代。
- 本地 PDF 涉及暖色 token、版面留白、元件命名、Artifact schema 或回報格式時，可作為本專案預設，但仍要服從品牌、無障礙、技術限制與使用者當前要求。
- 查不到官方依據時，不補寫成「Anthropic 官方規範」；改寫為「本專案 Claude-inspired 偏好」或「本次設計建議」。
