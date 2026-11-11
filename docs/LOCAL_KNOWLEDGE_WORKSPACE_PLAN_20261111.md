# Local knowledge workspace: Trilium adoption and minimal integration

Created: 2026-11-11 (Asia/Taipei). Project: `codex-antigravity-collaboration`.
Status: planning and work-package definition; desktop deployment and user acceptance NOT RUN.
Owner: Codex lead. Delivery dates: not scheduled; use dependency order below.
Planning base: `cf9b9e4aac7788d55adef52e3a286ec28aa8a9ab` on `poc/ollama-systemone-router`.
Documentation branch: `codex/plan-trilium-kb-20261111`.

## Decision and user requirements

Adopt an existing local application UI first. Trilium Notes is the primary candidate.
The user explicitly prefers minimum development: reuse native document management,
search, editing, graph views, layouts, and backup instead of building those again.
The prior custom React/React Flow application proposal is superseded by this plan.
Use existing extension points only for a measured unmet requirement. Do not fork
Trilium core or commission a new frontend, search engine, database service, gateway,
broker, MCP server, or agent runtime as a routine implementation step.

The target is daily knowledge work: find a document, understand its relationships,
read its evidence, and add personal notes through an existing visual UI on Windows.
Core browsing, search, note editing, relationship navigation, and saved views must
work locally without cloud login or internet access after assets are prepared.
Cloud storage is an optional source/sync surface, not a runtime dependency.

## Evidence and candidate selection

- Research verified official latest stable release `v0.107.0` (published 2026-11-08);
  pin an official Windows asset and its published integrity information at execution.
- Trilium documents native full-text search, note trees, labels/relations, relation
  maps, note maps, tabs/split views, export/import, scripting, and ETAPI.
- Current online docs can follow newer code. Verify required features against the
  pinned release and the installed app's in-app help; do not treat nightly as stable.
- Exact `v0.107.0` source documentation confirms native Ollama/LM Studio providers,
  note-context/tools and a built-in HTTP MCP server (no stdio transport). Local
  operation and existing-client compatibility still require runtime acceptance.
  Do not equate note-context chat/tools with whole-vault semantic/vector RAG.
- AnythingLLM Desktop is a reserve candidate for document Q&A only if a demonstrated
  native Trilium gap remains. Do not deploy both applications by default.
- No Trilium installation, offline UI test, import fidelity test, or ETAPI execution
  has been performed in this planning task. Product capability is research evidence,
  not local acceptance evidence.

## Architecture and authority

```text
Approved local project files / explicitly exported Drive documents
    -> native import first; bounded one-way projection only if required
    -> Trilium Desktop local knowledge tree, search, maps, notes and collections
    -> supported native HTTP MCP / ETAPI or scoped export for existing agents

Existing System One artifacts -> native notes/tables/attachments in Trilium
Existing Ollama              -> optional native Trilium local-model connection
Existing GitHub tasks       -> original issue links; execution uses existing workflow
```

`PROJECT.yaml` remains authoritative: GitHub owns code/tests/config; the registered
Drive Current owns planning/progress/manuals. Trilium provides a usable local view;
it does not replace those authorities. New personal notes are authored in Trilium,
separately from managed source projections. Their native database and backups are
expected application data, not a new service we implement.

This is a sibling extension, not an expansion of the System One experiment's
restricted runtime/write-set. Preserve the frozen Policy Engine and existing
production routing. Native note edits do not authorize repository edits or agent
dispatch. The existing bridge need not be repaired to view documents or evidence.

## Native-first capability contract

| User operation | First implementation | Conditional small change |
| --- | --- | --- |
| Organize/read/search | Native tree, editor, labels, saved search, split view | Configuration/help only |
| Navigate project/document/decision/evidence | Native links, relations, relation/note map | Small explicit relation mapping only if needed |
| Add commentary | Native personal notes linked to managed source notes | None |
| Read local project documents | Native Markdown/HTML/file import and source receipts | One bounded importer if repeat-import/metadata acceptance fails |
| View System One and baseline evidence | Native tables/code notes/attachments, original evidence links | One deterministic JSON/JSONL-to-importable-report converter if needed |
| Let agents read knowledge | Native HTTP MCP if client controls fit; scoped export otherwise | Existing runtime configuration/client calls, no new server |
| Local AI help | Existing native provider and selected-note context, if verified | Reserve existing document-Q&A application; separate decision before adding it |

Flexibility comes from native workspaces/layouts, note attributes, templates,
collections, saved searches, and documented extensions. No speculative plugin
framework. Each custom change needs a reproducible native-UI failure and a linked
issue, with one named writer and focused acceptance. If core patches, a separate
frontend, bidirectional sync, or another required service becomes necessary, stop
and return that architectural choice to the lead/user.

## Work packages and dependency order

Live task state and detailed task packets belong to the linked GitHub issues.
This document describes the accepted sequence, not a second task-status queue.

| ID | Owner role at execution | Dependency | Deliverable / acceptance |
| --- | --- | --- | --- |
| KB-01 | Local setup worker; lead validates | None | Pin stable Windows desktop, isolated data profile, native UI/offline/import/search/map/backup trial and screenshots; zero custom code |
| KB-02 | Data integration worker | KB-01 | Small source projection with provenance, relationships, personal-note isolation, and repeat-import/update/conflict behavior |
| KB-03 | Evidence presentation worker | KB-01; shares mapped root with KB-02 | Existing synthetic cases/results usable in native UI, paired results and downgrade case links, original artifacts retained |
| KB-04 | Existing-agent integration worker plus independent reviewer | KB-02 and KB-03 | Native export/API/local-model fit check, bounded agent reading, final user-task and offline/restore acceptance, short operating guide |

KB-02 and KB-03 preparation may run in parallel in separate output files. Only one
writer may import/change the shared Trilium database at a time. KB-04 review must
be performed by someone other than the implementation writer. The lead owns
architecture and acceptance; role allocation does not mean a worker is running.

Planning epic: [16](https://github.com/a275618631/codex-antigravity-collaboration/issues/16).
- KB-01: [#17](https://github.com/a275618631/codex-antigravity-collaboration/issues/17)
- KB-02: [#18](https://github.com/a275618631/codex-antigravity-collaboration/issues/18)
- KB-03: [#19](https://github.com/a275618631/codex-antigravity-collaboration/issues/19)
- KB-04: [#20](https://github.com/a275618631/codex-antigravity-collaboration/issues/20)

Human plan: [Trilium adoption and minimal integration](https://docs.google.com/document/d/1o9aCwceCUr5n-1GLmNgqSm0Od31W86dxGwQVpf4YXdI/edit?usp=drivesdk).
Formal progress: [registered Drive Current](https://drive.google.com/file/d/1pnrxGpRQnaXTVQh4QRkEmQl0E_R2JJZC/view).
Drive location: existing project folder / `xx_擴充規劃`
(`1efB5T5KXZMNdMI9Rm_wYjomt95f_3gBV`); the local execution does not depend on Drive.

## Source projection and update rules (KB-02)

Start with an allowlisted sample of 10-20 project documents and the existing
synthetic experiment artifacts; never recursively index the user's drive or all
repositories. `PROJECT_TREE.md` / `SYSTEM_RELATIONSHIPS.yaml` are not present in
the audited checkout and must not be assumed available. Use explicit existing
file links and user-authored relationships instead of generating a new authority.

For each managed projection record project ID, source kind, source path/URL,
repository and ref scope where applicable, source revision/hash, capture time,
and source authority. A live Drive URL alone is not an offline copy; mark freshness
and let the user explicitly refresh exported documents when connectivity returns.

Native import is a conversion/copy, not a live Git-folder mount. Check Markdown
tables, code, relative links, attachments, Unicode and filenames for conversion
loss. Preserve originals; do not promise byte-identical round trips through a rich
text editor. Managed source notes should use supported read-only settings; personal
notes and comments live separately and are never overwritten by a source refresh.

If a thin importer is justified, use supported ETAPI and native note attributes
for stable identity; its derived mapping is not a new system of record. A second
identical run must create zero duplicates. An update must preserve note identity,
incoming links and personal notes. Detect local edits using the last imported
body hash; skip/report conflicts. Renames and ambiguous identity need explicit
resolution. Source deletions mark stale/obsolete; do not automatically delete notes.
After timeout or partial failure, record bounded progress and resume idempotently;
do not claim whole-run transaction rollback without API evidence.

## Existing PoC evidence contract (KB-03)

Use only existing `experiments/systemone_router` cases, predictions, metrics,
and audit evidence. Join predictions to cases by `case_id`. Display method,
actual route, gold route, minimum-safe-route membership, status/fallback,
confidence when available, latency, model/config and response digest when present.
Missing evidence stays unknown; do not fabricate a per-run model digest.

Show `synthetic_non_adoption` prominently. Preserve dataset readiness separately
from the blocked adoption gate. The captured ten-case System One canary has
accuracy 0.50 and false downgrades 3/5; the fixture-tailored keyword baseline has
accuracy 1.00 and 0/5. Those are synthetic observations, not adoption evidence or
a generalizable superiority claim. Do not rerun model calls to create UI data.

## Local access and existing-agent integration (KB-04)

Trilium `v0.107.0` includes a native HTTP MCP server, disabled by default. Prefer
supported direct HTTP MCP configuration in the existing Codex/Antigravity client
when deterministic client/tool controls fit; use native subtree exports otherwise.
Do not build a new MCP server or assume the old bridge is required. MCP uses the
same whole-instance read/write ETAPI token and external calls bypass Trilium UI
approval. A separate token is not a read-only or subtree-scoped token. Start any
MCP trial in a disposable/dedicated approved-content profile, verify actual client
tool restrictions, and treat those controls separately from note-context settings.
Never read existing credential stores or include tokens in issues/reports/logs.
Bind optional listeners to loopback and keep the existing deterministic tool policy.

For optional local AI, verify native provider compatibility and note-context
behavior on the pinned version. Reuse an existing suitable generative model if
available; the System One decision model is not the knowledge-answering baseline.
Record any additional model/embedding/download requirement rather than installing
it silently. Local model usage alone does not prove the application makes no
outbound calls; verify startup and offline user tasks with remote features off.
Do not add an agent-run button, task receiver, autonomous tool access or background
watcher merely to integrate note reading.

## Acceptance and delivery evidence

1. Start the existing desktop UI from a normal Windows shortcut with a dedicated
   local data profile; record app version, storage location and startup behavior.
2. With internet disconnected, browse/read/search known Traditional Chinese and
   English sample content, follow local note links and open an existing attachment.
3. From one project note, navigate to a decision, its source, and a relevant
   experiment result using native UI maps/links; report missing relations honestly.
4. Add a personal note, refresh the source projection twice, and verify no duplicate
   managed notes, no lost links, and no overwritten personal work.
5. Compare baseline/System One cases and open all three captured false-downgrade
   cases from the native presentation. Preserve the synthetic/adoption boundary.
6. Back up using the supported native workflow, restore to a separate local profile,
   and repeat browse/search/link checks. Exported Markdown alone is not assumed to
   preserve every attribute, attachment, map, or revision; verify the native backup.
7. If optional agent/local-AI paths are enabled, show actual bounded reads and source
   references; otherwise report NOT RUN/DEFERRED without blocking core UI adoption.

Keep test evidence separate: researched capability, locally observed UI behavior,
offline verification, restore verification, and optional AI/API verification.
Screenshots must come from the actual local trial and be sanitized. A planning
document or an upstream screenshot is not local deployment proof.

## Sources checked for planning

- Stable release: https://github.com/TriliumNext/Trilium/releases/tag/v0.107.0
- Native features: https://github.com/TriliumNext/Trilium#-features
- Native maps: https://docs.triliumnotes.org/user-guide/note-types/relation-map
- ETAPI: https://docs.triliumnotes.org/user-guide/advanced-usage/etapi
- Pinned native AI: https://github.com/TriliumNext/Trilium/blob/v0.107.0/docs/User%20Guide/User%20Guide/AI.md
- Pinned MCP: https://github.com/TriliumNext/Trilium/blob/v0.107.0/docs/User%20Guide/User%20Guide/AI/MCP.md
- Pinned privacy/token boundary: https://github.com/TriliumNext/Trilium/blob/v0.107.0/docs/User%20Guide/User%20Guide/AI/Privacy.md
- Reserve desktop: https://docs.anythingllm.com/installation-desktop/overview
- Project authority: repository `PROJECT.yaml` and registered Drive Current.

## Planning delivery boundary

This work produces an agent plan, linked planning issues, and a human-readable
Drive plan. The install checkpoint below records the separately requested local
Trilium install; it does not constitute completion of native UI, offline, import,
backup/restore, or Agent acceptance. No existing knowledge base was migrated and
no unattended receiver was dispatched. Existing PoC code and raw results are
unchanged. Planning branch `codex/plan-trilium-kb-20261111` was pushed; no PR or
merge has been created.

## Local install checkpoint (2026-11-11)

- Installed the official TriliumNext Notes v0.107.0 Windows x64 package per-user
  through WinGet (`TriliumNext.Notes`); WinGet verified installer SHA-256
  `218b444138b52b212f914daa1f032221ecb30f83b579f43c19bc2de55e231129`.
- Executable: `C:\Users\Y6T2\AppData\Local\trilium\Trilium.exe`.
- Data directory: `C:\Users\Y6T2\AppData\Roaming\trilium-data`; a new database was
  created on first launch. No pre-existing Trilium install/data directory was
  found before installation.
- First launch reached the native `Getting Started - Trilium Notes` window. The
  process is running; screenshot capture was not available in this execution.
- This confirms installation and startup only. KB-01 still must verify actual
  browse/search tasks, offline behavior, safe import, backup/restore, and the
  Traditional Chinese user guide. Upgrade/rollback acceptance was added to
  GitHub issue #17 and remains NOT RUN.
- No model, MCP, ETAPI, sync, external account, or production routing was enabled.
