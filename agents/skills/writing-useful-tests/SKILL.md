---
name: writing-useful-tests
description: >-
  What makes a test worth keeping, at any level: unit, integration,
  behavioural, end-to-end. Use when writing, changing, or reviewing tests,
  planning which tests a feature, change, or bug fix needs before or after
  the code exists, deciding whether code needs a test at all, fixing a flaky
  test, or adding mocks, fakes, fixtures, or test helpers.
---

# Writing useful tests

A test exists to catch one **break**: a change to production code that breaks
a behaviour someone relies on. Write the fewest tests that make the change safe
to ship and keep it safe as the code around it changes. Each test catches one
break, and its name says which. Judge tests by the breaks they catch, never by
their count or a coverage number.

Work in four passes: choose the breaks, write each test, prove each test goes
red, and cut what protects nothing. To plan tests, run pass 1: its list of
breaks, each with its level, is the plan. To review tests someone else wrote,
run passes 2 to 4 on them.

## 1. Choose the breaks

A **public interface** is what a caller uses to reach a behaviour, such as a
function it calls, an endpoint, a CLI command, a message it sends, or a page it
clicks through. Tests act and observe only through public interfaces. Before the
first test, list the public interfaces the change touches and, for each one,
the breaks worth catching.

These breaks earn a test:

- the main path of a public behaviour;
- a failure path with an observable effect, such as an error, a rejection, a
  fallback, or a refusal;
- an edge case or branch that is both reachable and critical. Reachable means
  a real caller can send the input through the public interface, past the
  validation that already runs. Critical means a wrong result would do harm,
  such as losing or corrupting data, charging the wrong amount, granting
  access wrongly, or breaking a path users take. For example, an empty cart at
  checkout, a quantity one past the stock limit, or a repeated payment
  request. An input that types, a parser, or earlier validation already
  rejects earns no test.
- a regression: the bug this change fixes, so it cannot return;
- a contract between modules that a change on either side would break;
- an access rule, tested both ways: a caller the rule permits can act, and a
  caller it refuses cannot. For example, an owner can delete their post and
  another user cannot.
- an invariant or state transition: a rule that must hold across calls, not
  just within one. For example, a balance never goes negative, an order ships
  once, and a repeated request changes nothing the second time.

These earn no test:

- trivial code, such as a getter, a constructor that sets a field, a constant,
  a forwarding wrapper, or a one-line helper whose caller is already tested.
  Test these only when they validate, normalise, apply a default, derive a
  value, enforce a rule, or cause a side effect. Otherwise assert the first
  result a caller can see that depends on them.
- what the compiler, type checker, framework, or a library already
  guarantees. Test the contract your code makes at its boundary, for example
  the route you register, the query you emit, or the payload you produce. The
  framework's or library's own mechanics are for its maintainers to test.
  When upstream behaviour surprises you, write one narrow characterisation
  test that names the assumption.
- implementation detail, such as a constant's value, private structure, or
  which collaborator is called. A test that only a redesign can fail is a
  **change detector**. It fails on every intentional change and misses real
  breaks. Instead, test the behaviour that depends on the detail: not
  "MAX_RETRIES is 5" but "a failing call makes six attempts and then gives
  up". If no behaviour depends on the detail, write no test.
- text a human reads, such as a label, a message, a heading, a document, a
  comment, or a log message. A test that pins the wording is a change
  detector. Every rewording fails it and no behaviour break does. Test what the
  text causes, for example the button places the order, or the invalid input
  raises `InvalidEmailError`. Text a machine parses, such as a query, a
  payload, a path, or a structured log field, is a contract and earns a test.
  So is an accessible name, which assistive technology reads, and wording the
  product requires exactly, such as legal copy or a required disclosure.
- a second literal through a path already tested. When two inputs matter, they
  are one parametrised case, not two tests.
- a behaviour an existing test already covers. When the change alters it,
  update that test rather than adding a second one.
- generated code: code a tool writes from a schema or spec. Test the
  behaviour that uses it, or the generator's input when you own the
  generator. ORM models, protobuf stubs, and client SDKs are examples.
- appearance: how an interface looks rather than what it does. Use a visual
  check or a visual-regression tool. An assertion on a class name or style is
  a change detector. Colour, spacing, and layout are examples.

Pick the level by where the break lives, and test each break at one level:

- **unit**: logic inside one module, reached through its public interface;
- **integration**: a contract between your modules, or with a real dependency
  such as a database, filesystem, or queue, run against the real thing;
- **end-to-end or behavioural**: a user journey through the assembled system.
  Reserve these for the few journeys whose failure would block a release.

When a break fits more than one level, use the lowest level that runs
everything the break depends on. If a unit test can reach the logic only by
mocking your own code, test it at integration instead.

An integration test that cannot reach its real dependency has not run. When
the dependency is unavailable, report the gap. Do not replace the dependency
with a mock and count the test as passing.

An end-to-end test checks that the journey completes and that its outcome is
correct. Test the branches and edge cases inside the journey at a lower
level. For example, the checkout journey places one order, and a unit test
covers each rule for rejecting a card.

The same break tested at three levels is two redundant tests.

## 2. Write each test

Before the body, name the break: the production change that would fail this
test, and the behaviour that change breaks. The test fails when that behaviour
changes, by mistake or on purpose, and stays green when only the
implementation changes.

- If you cannot name a change, redesign the test around an observable
  behaviour.
- If the change breaks no behaviour, as with a reworded message, cut the test.
- If the only change you can name is an edit to a script or config file, run
  the file against controlled inputs and assert its outputs, side effects, or
  exit code.
- If only an implementation detail changes, the test is a change detector.
  Replace it: find the behaviour that depends on the detail and test that
  behaviour instead. If no behaviour depends on the detail, write no test.

Write the body to these rules. [references/examples.md](references/examples.md)
shows each rule, and each mock rule below, as a bad and a good test side by
side. Read it before writing the first test in a session.

- **Match the repo.** Use the test framework, file layout, and assertion
  style the repo already uses.
- **Act and observe through the interface.** After `createUser`, retrieve the
  user through `getUser`, not by querying the table, so the test survives a
  storage change.
- **Name the test as a specification.** "User can check out with a valid
  cart" says what capability exists. A name that describes how the code works
  ties the test to the implementation.
- **Derive the expected value independently.** Use a literal, a hand-checked
  fixture, or a worked example from the spec. Prefer table-driven tests with
  literal expected values. An expected value computed by the code under test
  or its helpers is **tautological**: it passes whatever the code does.
- **One logical assertion per test.** The test fails for one reason, and its
  name says which.
- **Same result every run.** Fix the clock, seed randomness, and give each
  test its own data. Each test runs alone and in any order. Wait for the
  condition the test needs, never for a fixed time.
- **Locate elements the way a user does.** In UI tests, find an element by
  role and accessible name, then by label, then by test ID. A CSS class or
  DOM position breaks on every restyle.

### Mocks

Mock only at system boundaries, such as external APIs, time, randomness, and
sometimes the filesystem or database. Prefer a real test database. Everything
you control stays real, including your own classes, modules, and
collaborators. These rules use
"mock" for every double: mock, fake, or stub.

- **The mock earns no assertions.** An assertion on a mock passes when the mock
  is present and fails when it is absent. It says nothing about the component.
  If the mock is what you are checking, unmock it or delete the assertion.
- **Mock the level below the side effects the test depends on.** Learn every
  side effect of the real method first, then mock only the slow or external
  operation and keep the rest real. When unsure, run against the real
  implementation and observe what has to happen.
- **Make mocks specific at the boundary.** Where the call is the behaviour, as
  with an email sent or a charge made, assert the arguments, count, and order.
  A mock that accepts anything verifies nothing. Give each branch its own
  fixture, for example success, error, and malformed, so the wrong branch
  cannot satisfy the expectation. Inside your own code, call counts and order
  are implementation detail, so assert the outcome instead.
- **Mirror real data completely.** A mock response carries every documented
  field, not only the fields the test reads. A partial mock passes while
  integration breaks on the omitted field.
- **Keep test-only code in test utilities.** A method that only tests call
  belongs in a test utility, not on the production class.
- **When mock setup outgrows the test, go real.** When mock setup is over
  half the test, when the mock lacks methods the real component has, or when a
  change to the mock breaks tests, switch to an integration test with real
  components.
- **Design boundaries for mocking.** Inject the external dependency rather
  than constructing it inside. Give each external operation its own function,
  so each mock returns one shape and needs no conditional logic.

## 3. Prove each test goes red

List the mutations the change could realistically introduce on a critical
path, for example a wrong constant or argument, a wrong branch handler, a
missing state change or side effect, an empty or default return, a deleted
guard or validation check, and any other realistic mistake the change could
contain. At least one test must go red for each mutation.

When no test catches a mutation, find a reachable input that now gives a
different outcome. If that outcome is critical, the input is a missing edge
case: add a test for it. If no reachable input changes the outcome, or the
change it causes is harmless, the mutation needs no test. When the only test
that should catch it stays green, that test is tautological: fix it.

Reason through each mutation. When reasoning cannot settle whether a test
catches one, make the mutation, run the test, and revert the mutation before
the next one. A regression test must go red against the unfixed code before
it goes green against the fix.

## 4. Cut what protects nothing

1. Reread each test and name the break it alone catches. Cut the test when it
   catches none, or when another test already catches it.
2. Check each test against the warning signs below.
3. Delete scratch checks. The runs you did to verify your work are not tests.

## Warning signs

Each sign marks a test that cannot catch its break. If the test protects
nothing, cut it. If it protects a break, fix it so that break turns it red.

- Setup and assertion share the same object, guaranteeing equality.
- The test can fail only through a crash, a panic, or a missing selector.
- A try/catch, conditional, or early return lets the test pass without
  reaching its assertion.
- A snapshot of large or volatile output that nobody reviews line by line.
- The test fails on every intentional change and never on an accidental break.
- Expected values hide behind loops, builders, or helpers.
- The test greps source text, or asserts a removed symbol stays removed.
- The expected value is text a human reads: a label, a message, a heading.
- The test would still pass if only the framework remained.
- The test exists for coverage and checks no outcome or side effect.
- An assertion checks a mock test ID, or fails if the mock is removed.
- A method is called only from test files.
- Mock setup is more than half the test, or nobody can say why the mock is
  there.
