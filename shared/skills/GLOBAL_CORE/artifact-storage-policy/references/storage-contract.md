# Storage contract

只有需要正式 routing ledger、多目的地交付或稽核紀錄時才載入本 schema。

```yaml
storage_request:
  task: ""
  project_key: ""
  aliases: []
  destinations: [google_drive|github]
  artifacts: [{purpose: "", filename: ""}]
  date: "YYYY-MM-DD"
  user_authorized_write: false

routing:
  task: ""
  date: ""
  lane: fast|slow
  workflow: ""
  skills_invoked: []
  agents_invoked: []

storage:
  project_key: ""
  relationship: new|continuation|branch|related|needs_review
  platform: google_drive|github|both
  drive:
    expected_root: CODEX
    expected_project_folder: ""
    expected_parent_id: ""
    actual_parent_id: ""
    actual_path: ""
    root_leak_detected: false
    reused_existing_project_folder: false
    duplicate_project_folders_found: []
    placement_verified: false
  github:
    expected_repo: ""
    actual_repo: ""
    reused_existing_repo: false
    duplicate_or_related_repos_found: []
    placement_verified: false

artifacts:
  - purpose: ""
    expected_filename: ""
    actual_filename: ""
    local_path: ""
    url: ""
    storage_path: ""
    parent_id: ""
    repository: ""
    branch: ""
    status: created|updated|not_saved|needs_repair|failed
    verification: ""
    created_at: ""
    naming_verified: false

validations:
  routing_ledger: pass|fail|not_applicable
  content: pass|fail|not_run
  format: pass|fail|not_run
  remote_exists: pass|fail|not_run
  permission: pass|fail|not_run
  storage_location: pass|fail|not_run
  project_reuse: pass|fail|not_run
  filename_policy: pass|fail|not_run

unresolved: []
```
