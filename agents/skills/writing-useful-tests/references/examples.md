# Good and bad tests

Companion to [`SKILL.md`](../SKILL.md). Each pair shows one rule in code.

## Through the interface, not a side channel

```typescript
// BAD: verifies through storage, so a storage change breaks the test
test("createUser saves to database", async () => {
  await createUser({ name: "Alice" });
  const row = await db.query("SELECT * FROM users WHERE name = ?", ["Alice"]);
  expect(row).toBeDefined();
});

// GOOD: verifies through the public API
test("createUser makes user retrievable", async () => {
  const user = await createUser({ name: "Alice" });
  const retrieved = await getUser(user.id);
  expect(retrieved.name).toBe("Alice");
});
```

## Behaviour, not implementation

```typescript
// BAD: names how the code works and spies on an internal collaborator
test("checkout calls priceCalculator.total", async () => {
  const spy = vi.spyOn(priceCalculator, "total");
  await checkout(cart, paymentMethod);
  expect(spy).toHaveBeenCalledWith(cart);
});

// GOOD: names the capability and observes the outcome
test("user can checkout with valid cart", async () => {
  const cart = createCart();
  cart.add(product);
  const result = await checkout(cart, paymentMethod);
  expect(result.status).toBe("confirmed");
});
```

## Independent expected values

```typescript
// BAD: tautological, the expected value is computed the way the code computes it
test("calculateTotal sums line items", () => {
  const items = [{ price: 10 }, { price: 5 }];
  const expected = items.reduce((sum, i) => sum + i.price, 0);
  expect(calculateTotal(items)).toBe(expected);
});

// BAD: mirror assertion, the same builder computes both sides
const expected = buildSearchQuery({ tag: "urgent" });
expect(buildSearchQuery({ tag: "urgent" })).toBe(expected);

// GOOD: a hand-derived literal
expect(calculateTotal([{ price: 10 }, { price: 5 }])).toBe(15);
expect(buildSearchQuery({ tag: "urgent" })).toBe('tag:"urgent"');
```

## Change detector versus behaviour

```typescript
// BAD: only a redesign can fail this
expect(MAX_RETRIES).toBe(5);

// GOOD: the behaviour that depends on the constant
test("a failing call makes six attempts and then gives up", async () => {
  const client = failingClient();
  await expect(fetchWithRetry(client)).rejects.toThrow();
  expect(client.attempts).toBe(6);
});
```

## What the text causes, not the text

```typescript
// BAD: pins wording a human reads, so every rewording fails it
test("rejects an invalid email", () => {
  expect(() => validateEmail("bob")).toThrow("Please enter a valid email address");
});

// GOOD: the behaviour the text reports
test("rejects an invalid email", () => {
  expect(() => validateEmail("bob")).toThrow(InvalidEmailError);
});
```

## The mock earns no assertions

```typescript
// BAD: passes when the mock is present, fails when it is absent
expect(screen.getByTestId("sidebar-mock")).toBeInTheDocument();

// GOOD: the real component's behaviour
expect(screen.getByRole("navigation")).toBeInTheDocument();
```

## Mock the level below the side effects

```typescript
// BAD: the mocked store drops the first user, so the duplicate-email check
// has nothing to find
vi.mock("./userStore");

// GOOD: mock only the external email client; the store stays real, so the
// second registerUser call sees the first user
vi.mock("./emailClient");
```

## Design boundaries for mockability

```typescript
// Hard to mock: the dependency is constructed inside
function processPayment(order) {
  const client = new StripeClient(process.env.STRIPE_KEY);
  return client.charge(order.total);
}

// Easy to mock: the dependency is injected
function processPayment(order, paymentClient) {
  return paymentClient.charge(order.total);
}

// BAD: one generic fetcher, so every mock needs conditional logic
const api = {
  fetch: (endpoint, options) => fetch(endpoint, options),
};

// GOOD: one function per external operation, each mock returns one shape
const api = {
  getUser: (id) => fetch(`/users/${id}`),
  getOrders: (userId) => fetch(`/users/${userId}/orders`),
  createOrder: (data) => fetch("/orders", { method: "POST", body: data }),
};
```
