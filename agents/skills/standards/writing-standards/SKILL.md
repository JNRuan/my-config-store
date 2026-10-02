---
name: writing-standards
description: Standards for all writing. Use whenever you write or edit prose, including replies to the user, documents, commits, PRs, code comments, UI text, skills, and agent definitions.
---
# Writing standards

Apply these standards when you draft, when you revise, and when you reply to the user. Keep deliberate voice, character, rhythm, humour, and genre when the user wants them.

## Core Rules

From George Orwell, "Politics and the English Language":

1. Never use a metaphor, simile, or other figure of speech which you are used to seeing in print.
2. Never use a long word where a short one will do.
3. If it is possible to cut a word out, always cut it out.
4. Never use the passive where you can use the active.
5. Never use a foreign phrase, a scientific word, or a jargon word if you can think of an everyday English equivalent.
6. Break any of these rules sooner than say anything outright barbarous.

## Genre

Pick the genre before you draft. Each genre adds to Orwell's rules:

- **Technical prose**, such as documentation, READMEs, RFCs, instructions, PR descriptions, commit messages, and docstrings on a public API. Load the `technical-writing` skill and apply it. Write positive instructions that state what the reader must do.
- **Agent documents**, such as skills, agent definitions, and `AGENTS.md` or `CLAUDE.md` files. Load the `writing-for-agents` skill and apply it.
- **Replies, emails, and code comments.** Orwell's rules alone, unless directed otherwise.
- **UI text.** Follow the product's copy guidelines when they exist, then Orwell's rules.
- **Persuasive writing**, such as essays, blog posts, case studies, marketing copy, and sales pitches. Orwell's rules, with `technical-writing` applied only to passages that describe or explain technology.
- **Creative writing**, such as fiction, poetry, memoir, scripts, and lyrical prose. Keep intentional ambiguity, cadence, dialogue style, imagery, and character voice where they create a real effect. Remove only language that feels inherited, inflated, evasive, or lazy.

## Writing Guidelines

1. Before writing, identify the audience, the purpose, the promised tone, and the genre.
2. When revising, keep the author's meaning and any explicit tone or format constraints.
3. Draft or revise in concrete, direct UK English that follows Orwell's rules. Keep necessary nuance, so that short prose stays true and precise.
4. Leave marketing words to marketing copy. Words such as "powerful", "comprehensive", "seamless", "load bearing", and "synergy" belong only there.
5. Give each paragraph and list item one job that no other does. Start the text under a heading with new information, not a restatement of the heading. Cut any part that only repeats another.
6. Preserve code, commands, identifiers, product names, legal text, and direct quotes exactly. Flag any change they need.
7. Review everything you write with the `unslop` skill and fix any issues you find.
