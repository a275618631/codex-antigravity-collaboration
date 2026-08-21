# References

Checked on **2026-08-21**.

These references support the architecture discussion. They are not all project dependencies.

## Native agent runtimes

### OpenAI Codex

- Codex product: https://openai.com/codex/
- Introducing the Codex app: https://openai.com/index/introducing-the-codex-app/

Relevant capabilities documented by OpenAI include parallel agents, separate threads/projects, worktrees, Skills, and long-running agent workflows.

### Google Antigravity

- Antigravity 2.0: https://www.antigravity.google/product/antigravity-2
- Subagents: https://antigravity.google/docs/subagents
- CLI background tasks and subagents: https://antigravity.google/docs/cli/subagents/
- Custom Agents: https://antigravity.google/blog/introducing-custom-agents

Relevant capabilities include parallel subagents, custom agents, Projects, Skills, MCPs, hooks, and agent management.

## Reusable skill packaging

### Agent Skills specification

- Specification: https://github.com/agentskills/agentskills/blob/main/docs/specification.mdx

The specification defines the `SKILL.md` + YAML-frontmatter packaging pattern used across multiple agent tools.

## Agent interoperability

### Agent2Agent (A2A)

- Repository: https://github.com/a2aproject/A2A
- Project site: https://a2a-protocol.org/

A2A is an open protocol for communication and interoperability between agentic applications. It is a relevant option for future explicit inter-runtime or inter-host coordination.

## Privacy / anonymization

### Presidio

- Repository: https://github.com/data-privacy-stack/presidio
- Documentation: https://presidio.dataprivacystack.org/

Presidio provides mature primitives for detecting, redacting, masking, and anonymizing sensitive data. This project treats it as a reference building block rather than reinventing general PII detection.

### LLM Guard — design precedent only

- Repository: https://github.com/protectai/llm-guard

LLM Guard demonstrated input/output scanning and anonymize/deanonymize patterns for LLM applications. The repository is currently archived, so it should not be treated as the preferred long-term dependency.

## Adjacent methodology

### Superpowers

- Repository: https://github.com/obra/superpowers

A widely adopted skills-based development methodology. Relevant as an example of packaging reusable agent workflows and verification practices without requiring this project to copy its framework.

## Reference policy

When this repository mentions an external project, it should say one of:

- **native capability** — relied upon because the platform already provides it;
- **standard to evaluate** — relevant for future interoperability;
- **reference building block** — mature component worth reusing;
- **design precedent** — useful historical idea, not a recommended dependency.

Avoid presenting popularity or GitHub stars as evidence of architectural correctness.
