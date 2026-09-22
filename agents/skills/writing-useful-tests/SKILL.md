---
name: writing-useful-tests
description: >-
  What makes a test worth keeping, at any level: unit, integration,
  behavioural, end-to-end. Use when writing, adding, or changing tests,
  deciding which tests a change needs or whether code needs one at all, or
  adding mocks, fakes, fixtures, or test helpers.
---

# Writing useful tests

A test exists to catch one specific break. Write the fewest tests that make
the change safe to ship and keep it safe as the code around it changes: one
test per break worth catching, and every test names its break. Judge tests by
the breaks they catch, never by their count or a coverage number.

Work in three passes: choose the breaks, write each test, cut.

## Choose the breaks

A **seam** is a public boundary where a caller observes behaviour without
reaching inside. Tests live at seams. Before the first test, list the seams the
change touches and, for each, the **breaks** worth catching.

These breaks earn a test:

- the main path of a public behaviour;
- a failure path with an observable effect: an error, a rejection, a fallback,
  a refusal;
- a boundary or branch: an empty input, a limit, an off-by-one, a comparison, a
  regex;
- a regression: the bug this change fixes, so it cannot return;
- a contract between modules that a change on either side would break.

This code earns no test:

- trivial code: a getter, a constructor that sets a field, a constant, a
  forwarding wrapper, a one-line helper whose caller is already tested. Test
  these only when they validate, normalise, apply a default, derive a value,
  enforce a rule, or cause a side effect. Otherwise assert the first result a
  caller can see that depends on them.
- what the compiler, type checker, or framework already guarantees. Test the
  contract your code makes at its boundary (the route you register, the query
  you emit, the payload you produce). The framework's mechanics are its
  maintainers' tests to write. When upstream behaviour surprised you,
  write one narrow characterisation test that names the assumption.
- implementation detail: a constant's value, private structure, which
  collaborator is called. A test that only a redesign can fail is a **change
  detector**: it fails on every intentional change and misses bugs. Test the
  behaviour that depends on the detail: not "MAX_RETRIES is 5" but "a failing
  call is retried five times and there is no sixth attempt".
- text a human reads: a label, a message, a heading, a document, a comment.
  Spelling and wording belong to a spellchecker, a lint rule, or a reviewer.
  A test that pins the wording is a change detector: every rewording fails it
  and no behaviour break does. Test what the text causes: the button places
  the order, the invalid input raises `InvalidEmailError`. Text a machine
  parses, such as a query, a payload, or a path, is a contract and earns a
  test.
- a second literal through a path already tested. When two inputs matter, they
  are one parametrised case, not two tests.

Pick the level by where the break lives, and give each break one level:

- **unit**: logic inside one module, reached through its public interface;
- **integration**: a contract between your modules, or with a real dependency
  such as a database, filesystem, or queue, run against the real thing;
- **end-to-end or behavioural**: a user journey through the assembled system.
  Reserve these for the few journeys whose failure would block a release.

The same break tested at three levels is two redundant tests.

## Write each test

Before the body, name the production change that would make this test fail
and the behaviour that change breaks. The test guards that behaviour: it fails
when the behaviour changes, by mistake or on purpose, and stays green when
only the implementation changes. Check:

- Cannot name a change: redesign the test around an observable behaviour.
- The change breaks no behaviour, as with a misspelled label or a reworded
  message: cut the test. Spelling and wording belong to review.
- "The source text changed": run the artefact and assert its effects.
- Only an implementation detail changes: change detector. Test the
  behaviour that depends on the detail.

Then:

- **Act and observe through the interface.** Verify through the public API,
  not a side channel. After `createUser`, retrieve the user through `getUser`
  rather than querying the table: the test then survives a storage change.
- **Name the test as a specification.** "User can check out with a valid
  cart" says what capability exists. A name that describes how the code works
  ties the test to the implementation.
- **Derive the expected value independently.** Use a literal, a hand-checked
  fixture, or a worked example from the spec. Table-driven tests with literal
  `want` values are the preferred shape. An expectation computed by the code
  under test or its helpers is **tautological**: it passes no matter what the
  code does.
- **One logical assertion per test.** The test fails for one reason, and its
  name says which.
- **Behaviour, not text.** Test a script or config by running it against
  controlled inputs and asserting outputs, side effects, or exit codes.

### Doubles

Mock only at system boundaries: external APIs, time, randomness, and sometimes
the filesystem or database (a real test database is better). Everything you
control stays real: your own classes, modules, and collaborators.

- **The mock earns no assertions.** An assertion on a mock passes when the mock
  is present and fails when it is absent. It says nothing about the component.
  If the mock is what you are checking, unmock it or delete the assertion. The
  question to ask: "Are we testing the behaviour of a mock?"
- **Mock the level below the side effects the test depends on.** Learn every
  side effect of the real method first, then mock only the slow or external
  operation and keep the rest real. When unsure, run against the real
  implementation and observe what has to happen.
- **Make doubles specific at the boundary.** Where the call is the behaviour
  (an email sent, a charge made), assert the arguments, count, and order. A
  fake that accepts anything verifies nothing. Give each branch (success,
  error, malformed) its own fixture, so the wrong branch cannot satisfy the
  expectation. Inside your own code, call counts and order are implementation
  detail: assert the outcome instead.
- **Mirror real data completely.** A mock response carries every documented
  field, not just the ones the test reads. A partial mock passes while
  integration breaks on the omitted field.
- **Test-only cleanup lives in test utilities.** A method called only from
  tests never lands on the production class.
- **When mock setup outgrows the test, go real.** When mock setup is over
  half the test, when the mock lacks methods the real component has, or when a
  change to the mock breaks tests, switch to an integration test with real
  components.
- **Design boundaries for mockability.** Inject the external dependency rather
  than constructing it inside, and give each external operation its own
  function so each mock returns one shape and needs no conditional logic.

## Cut

Before finishing, in this order:

1. **Mutation check.** Mentally mutate the production code and confirm that
   at least one test fails for each realistic mutation: a wrong constant or
   argument, a wrong branch handler, a missing state change or side effect,
   an empty or default return, missing validation for zero, empty, nil,
   unauthorised, or malformed input. A mutation that nothing catches marks the
   behaviour unprotected, or the test tautological.
2. **Reread each test and name the failure it alone catches.** Cut any where
   the answer is nothing, or another test already catches it.
3. **Delete scratch checks.** The runs you did to verify your work are not
   tests.

## Warning signs

Any of these marks a test that cannot catch a break. First ask whether the
test protects anything. If it protects nothing, cut it. If it protects a
break, fix the test so the break fails it.

- Setup and assertion share the same object, guaranteeing equality.
- The test can fail only through a crash, a panic, or a missing selector.
- The test fails on every intentional change and never on accidental breakage.
- Expected values hide behind loops, builders, or helpers.
- The test greps source text, or asserts a removed symbol stays removed.
- The expected value is text a human reads: a label, a message, a heading.
- The test would still pass if only the framework remained.
- The test exists for coverage and checks no outcome or side effect.
- An assertion checks a mock test ID, or fails if the mock is removed.
- A method is called only from test files.
- Mock setup is more than half the test, or nobody can say why the mock is
  there.

See [references/examples.md](references/examples.md) for good and bad tests examples.