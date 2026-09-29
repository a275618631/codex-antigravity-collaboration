# P0 current state — GitHub local handoff (2026-09-29)

## Confirmed

- Canonical repository: `a275618631/codex-antigravity-collaboration`; local and remote observed HEAD were `7a48104` before implementation.
- Existing canonical protocol and `shared/rules/references/cross-runtime-packets.md` remain the source of truth. This MVP adds transport metadata without replacing the Task/Result Packet.
- Existing `local_bridge` and tests were not modified. Its live two-runtime login/interop was not revalidated.
- Local Codex CLI was `0.150.1`. Its help exposed stdin prompt input, JSONL events, output schema, last-message output, ephemeral execution, and read-only/workspace-write/danger-full-access sandboxes.
- GitHub CLI was `2.93.0`; authentication status was not readable in the current sandbox.
- Antigravity IDE CLI was `1.107.0`; live bridge login was not verified.
- No Python interpreter was installed on this Windows host (`py` reported no installed Python). Python execution tests are therefore pending on a suitable host.

## Safe degradation

- Development used mock GitHub objects and static validation only. No GitHub write, PR, token access, background service, or real Codex execution occurred.
- Real ChatGPT → Issue → approval → local execution → GitHub result smoke test is **BLOCKED pending authorization, a private test inbox/repository, a process-scoped token, and Python**.
- Windows runtime and macOS runtime are **NOT VERIFIED**. The scripts are verification helpers, not evidence of runtime passage.

## References

- Codex non-interactive mode: <https://developers.openai.com/codex/noninteractive/>
- Codex CLI reference: <https://developers.openai.com/codex/cli/reference/>
- GitHub REST API rate limits: <https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api>
- GitHub REST API best practices: <https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api>
