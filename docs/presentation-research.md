# What we learned from popular skill repositories

Research snapshot: **October 25, 2026**. This study concerns repository
presentation, not copying another project's implementation or branding.

## What the public metric measures

The [skills.sh all-time directory](https://www.skills.sh/) showed the following
widely installed skills during this review:

| Skill | Reported installs, rounded | Source |
| --- | ---: | --- |
| find-skills | 4.0 million | [Registry page](https://www.skills.sh/vercel-labs/skills/find-skills) |
| grill-me | 1.4 million | [Registry page](https://www.skills.sh/mattpocock/skills/grill-me) |
| agent-browser | 1.2 million | [Registry page](https://www.skills.sh/vercel-labs/agent-browser/agent-browser) |
| frontend-design | 1.0 million | [Registry page](https://www.skills.sh/anthropics/skills/frontend-design) |

The directory also lists other skills between these entries; this is a selected
reference set, not a claim that these are the top four in order.

These are **aggregate CLI installs**, not unique people, GitHub stars or all
downloads everywhere. The [registry methodology](https://www.skills.sh/docs)
describes telemetry-based ranking. The public
[Claude Code](https://www.skills.sh/agent/claude-code) and
[Codex](https://www.skills.sh/agent/codex) pages explain installation but do not
provide separate per-agent install counts. We therefore do not label the
numbers above as Claude-only or Codex-only downloads.

## Presentation observations and our choices

| Observed pattern | Where reviewed | Our application |
| --- | --- | --- |
| Clear identity and immediate installation | [skills CLI](https://github.com/vercel-labs/skills) | Named project, short promise and copyable install near the top |
| Task-led descriptions | [Vercel Agent Skills](https://github.com/vercel-labs/agent-skills) | Show user goals before transport internals |
| Practical quick start and visible requirements | [agent-browser](https://github.com/vercel-labs/agent-browser) | Runnable examples plus Python/Node and desktop requirements |
| Distinct presentation and direct language | [Matt Pocock's skills](https://github.com/mattpocock/skills) | Original hero art, concise positioning and concrete workflows |
| Scope and usage guidance | [Anthropic skills](https://github.com/anthropics/skills) | Separate intended use, verified behavior and pending acceptance |

Our interpretation is that these choices reduce the effort needed to understand,
install and evaluate a project. This is a design hypothesis, not evidence that
a README feature caused installation growth. Existing audiences, distribution,
utility and promotion also affect adoption.

We wrote an original README, included English and Brazilian Portuguese entry
points, kept the working skill ID stable, and exposed contribution paths. We
did not copy another project's text, artwork, claimed audits or popularity
badges. Future presentation changes should be evaluated against real feedback.
