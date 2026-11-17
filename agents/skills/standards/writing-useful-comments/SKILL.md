---
name: writing-useful-comments
description: >-
  What makes a code comment worth keeping. Use when writing, changing, or
  reviewing code comments, docstrings, or doc comments, including the ones
  you add while writing code.
---

# Writing useful comments

A comment serves the **next reader**: someone with only this file open, who never saw the diff, the
ticket, or the conversation. Write for them, not for the reviewer of your change. Default to
writing no comment and carefully consider whether a comment is necessary or useful before writing
it.

## When to comment

First try to make the code say it: rename, extract, tighten a type, or add an assertion or a test.
A rule that must hold belongs where breaking it fails the build. Make these changes in code your
task already touches. Elsewhere, propose them.

A comment stays only when it gives the next reader one of these:

- a reason the code does not show;
- a constraint, an invariant, or an important trade-off;
- a contract the signature does not make evident, such as a side effect or a failure mode;
- behaviour forced by a dependency, platform, or protocol you cannot change;
- a link to the issue or RFC that explains a constraint that still holds.

Everything else belongs somewhere else:

- **What the code does.** Names, types, and match arms say it. A comment that restates a
  condition, a match, or a signature adds nothing.
- **The task, the fix, the callers, and what the code used to do.** The commit and the PR
  description hold these. In the file they stop being true as the code changes.

If deleting the comment would confuse nobody, delete it.

## How to write it

- **State the constraint, not the story.** Write the failure the code guards against, in the
  present tense, as something still true, and say what breaks: _"an agent can serve HTTP 200 with
  every worker dead, so liveness cannot be read off the status code"_. The incident behind it
  goes in the commit message. Test each sentence: would it help someone changing this code next
  year, or does it only say what happened once?
- **Short sentences, one idea each.** Use as many as the reader needs. A long comment of short
  sentences is fine. A short comment of one long sentence is not. Leave out colons and dashes that
  chain clauses, and asides in brackets.
- **Name who acts.** "the user", "the admin", "the saga", "Stripe". A session, a request, or a
  link is not someone and cannot want, hold, or grant. Write what happens: "the user opens the
  link", not "the link grants access".
- **Ask a question for a predicate or a lookup.** "Can this user unsubscribe someone from emails?"
  says exactly what `true` or `Some` means.
- **Explain a concept once.** Define a term where its type lives and point other comments at that
  name: "A capability, like `SubscriptionCapability`." Refer to code by name, never by position
  such as "the block below".
- **Put the comment on the thing it justifies**, one or two lines above the rule, function, or
  unit it explains. A file-header essay that covers several definitions goes unread and out of
  date.
- **A doc comment states the contract.** Say what the caller gets, what they must provide, the
  side effects, and how it fails. Leave the implementation out. Where the language or the repo
  expects one on every public item, write one, and make it say something the signature does not.
- **A security denial states what an attacker could otherwise do.** "Otherwise any signed-in user
  could create a billing link for another customer's email address."
- **Claim only what you checked.** Trace each claim through the code or the data flow before you
  write it. When you do not know the reason, ask, or write no comment.

## Existing comments

- When your change makes a comment false, fix or delete it in the same change.
- When asked to fix one comment, fix that one. Leave the others in the file as they are, including
  those in a style you would not use.

## Examples

The story of a fix becomes the constraint that still holds.

Before:

```ts
// Added a retry because uploads were failing in prod last week (INC-204).
```

After:

```ts
// The storage API returns 503 while a bucket rebalances. A retry one second later succeeds.
```

A definition repeated at its point of use becomes a question and a pointer.

Before:

```fsharp
/// The account whose subscription this session may act on, read from the validated links it holds.
///
/// A capability is a right carried by a token rather than by an identity: holding the account's
/// link is what grants it, and whose session this is plays no part. So the answer is read from the
/// validated links alone, never from `context.User`, and a signed-in admin without the link gets
/// `None` like anyone else.
```

After:

```fsharp
/// Which account's subscription can this user act on? Read from their valid links only, so the
/// answer lapses when the link does. See `SubscriptionCapability` for what a capability is.
```
