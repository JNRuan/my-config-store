# `writing-useful-tests`

`writing-useful-tests` tells a coding agent what makes a test worth keeping, at any level: unit, integration, behavioural, end-to-end. It loads whenever the agent writes or changes tests, decides which tests a change needs, or adds mocks, fakes, fixtures, or test helpers.

It is not a TDD skill. It covers the test itself: which breaks earn a test, how to write each one so it catches that break, when to use a double, and how to cut what protects nothing.

## Credits

The rules come from two sources, both MIT licensed:

- [`tdd`](https://github.com/mattpocock/skills/tree/main/skills/engineering/tdd) by Matt Pocock, from [mattpocock/skills](https://github.com/mattpocock/skills): seams as the place tests live, the anti-patterns, the good and bad test examples, and the mocking guidance in its `tests.md` and `mocking.md` references.
- [`writing-good-tests.md`](https://github.com/obra/superpowers/blob/main/skills/test-driven-development/writing-good-tests.md) by Jesse Vincent, from [obra/superpowers](https://github.com/obra/superpowers): name the break, independent expected values, change detectors, the rules for doubles, the mutation check, and the warning signs.

The skill leaves out the TDD loop on purpose: red, green, refactor, vertical slices, and agreeing seams with the user.

## Files

- `SKILL.md`: the rules.
- `references/examples.md`: good and bad tests side by side.
