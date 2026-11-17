# `writing-useful-comments`

`writing-useful-comments` tells a coding agent what makes a code comment or doc comment worth keeping. It loads when the agent writes, changes, or reviews comments, including the ones it adds while writing code.

It covers the comment itself: when one is warranted, how to word it, and what to do with comments already in the file. It leaves lint and type suppressions to the project's own rules.

## Credits

Most rules began as the comment section of one project's agent instructions. These sources added or sharpened the rest:

- [`comment-stinky`](https://github.com/saschb2b/skills/tree/HEAD/skills/engineering/comment-stinky) by saschb2b: write for a reader who has only the file open, put a rule that must hold into a type, assertion, or test, and refer to code by name.
- The [`claude-api`](https://github.com/anthropics/skills/blob/HEAD/skills/claude-api/shared/model-migration.md) skill by Anthropic: a comment addresses the next reader, not the reviewer of the change.
- [`comment-sicko`](https://github.com/cursor/plugins/blob/main/pstack/agents/comment-sicko.md) from [poteto's pstack](https://github.com/cursor/plugins/tree/main/pstack): the kinds of comment that stay.
- [`code-comments`](https://github.com/caidanw/skills/tree/HEAD/skills/code-comments) by caidanw and [`write-durable-code-comments`](https://github.com/giacus/agent-skills/tree/HEAD/skills/write-durable-code-comments) by giacus: change the code before commenting, and say what breaks.
- [`art-of-comment`](https://github.com/rakaadi/agent-kit/tree/HEAD/skills/art-of-comment) by rakaadi and Anthropic's [`comment-analyzer`](https://github.com/anthropics/claude-plugins-official/blob/HEAD/plugins/pr-review-toolkit/agents/comment-analyzer.md): check each claim against the code, and never invent a reason.
- [Go Doc Comments](https://go.dev/doc/comment) and Google's [code review guide](https://google.github.io/eng-practices/review/reviewer/looking-for.html): a doc comment tells callers what they need and leaves the implementation out.

## Files

- `SKILL.md`: the rules and two before-and-after examples.
