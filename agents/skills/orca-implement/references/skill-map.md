# Skill map

The skill each role invokes. `SKILL.md` names these by placeholder; substitute the mapped skill name at dispatch or invocation time, so dispatch text sent to a worker carries only the literal name. To swap an implementation, change its row here; models and efforts stay in `references/routing.md`.

| Role / intent        | Placeholder               | Skill                   |
| -------------------- | ------------------------- | ----------------------- |
| Code review lens     | `{code-review-skill}`     | `code-review-local`     |
| Security review lens | `{security-review-skill}` | `security-review-local` |
| Adversarial QA       | `{adversarial-qa-skill}`  | `adversarial-review`    |
| Browser verification | `{browser-skill}`         | `agent-browser`         |
| Plan gate            | `{plan-gate-skill}`       | `crit`                  |
| PR creation          | `{pr-skill}`              | `pr-create`             |

A mapped skill must be available where it runs: worker-invoked skills to Orca worker terminals, coordinator-invoked skills to the coordinator's runtime.
