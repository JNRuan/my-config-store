# `writing-standards`

`writing-standards` is the standard an agent applies to all writing: replies, documentation, commits, PRs, code comments, UI text, skills, and agent definitions. It sets Orwell's rules as the base, adds rules for each genre, and ends every text with an `unslop` review.

## Required skills

The skill loads three other skills, which must be installed alongside it:

- [`technical-writing`](https://github.com/cursor/plugins/tree/main/pstack/skills/technical-writing) from [poteto's pstack](https://github.com/cursor/plugins/tree/main/pstack): Diátaxis structure, Google developer style, ASD-STE100 instruction rules, and Global English syntax for technical prose.
- [`unslop`](https://github.com/cursor/plugins/tree/main/pstack/skills/unslop) from [poteto's pstack](https://github.com/cursor/plugins/tree/main/pstack): the catalogue of AI writing patterns used in the final review.
- [`writing-for-agents`](https://github.com/mattpocock/skills/tree/main/skills/productivity/writing-for-agents) from [mattpocock/skills](https://github.com/mattpocock/skills): how to write skills, agent definitions, and `AGENTS.md` or `CLAUDE.md` files.

## Credits

- George Orwell's 1946 essay ["Politics and the English Language"](https://www.orwellfoundation.com/the-orwell-foundation/orwell/essays-and-other-works/politics-and-the-english-language/): the six rules.
- [pstack](https://github.com/cursor/plugins/tree/main/pstack) by Lauren Tan, known as poteto, MIT licensed: the `technical-writing` and `unslop` skills this skill loads.
- [mattpocock/skills](https://github.com/mattpocock/skills) by Matt Pocock, MIT licensed: the `writing-for-agents` skill this skill loads.

## Files

- `SKILL.md`: the rules and steps.
