# Design Principles

## 1. Native capabilities first

If the platform already supports parallel agents, worktrees, skills, permissions, or subagents, use those capabilities before creating another abstraction layer.

A new component must solve a problem that cannot be handled reliably by the existing runtimes.

## 2. Complexity must be earned

The architecture intentionally progresses in this order:

```text
native runtime
    ↓
shared workspace
    ↓
explicit coordination
    ↓
thin broker
```

Do not skip to a distributed system because it looks architecturally complete.

Add a component only when there is a demonstrated requirement such as:

- real-time state;
- durable retries;
- task leases;
- heartbeat/liveness;
- cross-host scheduling;
- failure recovery that a shared workspace cannot provide.

## 3. Capability-aware routing

Different runtimes should not perform the same task by default.

Routing should consider:

- tool availability;
- repository access;
- browser/Google integration;
- reasoning requirement;
- privacy classification;
- expected cost/latency;
- need for an independent reviewer.

The goal is not “use more models.” The goal is “use the smallest sufficient capability.”

## 4. Bounded delegation

Internal subagents are a runtime concern.

External delegation is an architecture concern.

A receiving runtime may fan out internally, but cross-runtime delegation should have an explicit hop limit and return path.

This makes cost, failure, and responsibility easier to reason about.

## 5. Shared methods, thin adapters

Portable knowledge should live in reusable skills or shared instructions.

Platform-specific differences belong in small adapters.

Avoid:

- copying the same skill into multiple incompatible trees;
- embedding current model names into shared policy;
- making one platform's private config the de facto open standard.

## 6. Read-many, controlled write ownership

Parallel analysis is cheap; conflicting writes are expensive.

The architecture therefore encourages:

- many readers;
- independent reviewers;
- isolated parallel branches/worktrees;
- one active write owner per conflicting write-set;
- an explicit merge/finalization authority.

This is **not a distributed-lock implementation**. In the current Git-based pattern, write ownership is a coordination policy. Branch/worktree isolation separates concurrent work, Git provides optimistic concurrency, and PR/review/merge is the integration gate. A broker-backed lease would only be considered if future multi-host coordination demonstrates a real need for stronger distributed ownership semantics.

## 7. Privacy is a routing input

Privacy classification should affect where a task may execute.

A local model can help identify organization-specific sensitive concepts, but an LLM should not be the only mechanism deciding whether data may leave the machine.

Deterministic policy, secret detection, data classification, and local-only rules remain necessary.

## 8. Verification beats autonomy claims

“Low-friction” is preferable to “fully autonomous.”

A useful system should reduce unnecessary approvals while preserving clear gates around:

- destructive operations;
- external publication;
- credentials/secrets;
- irreversible changes;
- production data;
- security-sensitive actions.

## 9. Roadmap is not implementation

Every public claim should be labeled:

- **Implemented**
- **Partial**
- **Planned**
- **Exploratory**

Architecture diagrams may show future directions, but status tables must make the boundary explicit.

## 10. Avoid product-like claims without product-like evidence

Do not describe the project as:

- an enterprise platform;
- a secure gateway;
- a zero-trust solution;
- a fully autonomous operating system;
- production-ready;
- seamless;

unless those claims have corresponding implementation, threat modeling, tests, and operational evidence.

The project is strongest when it remains a **practical reference architecture and case study**.
