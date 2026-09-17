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
// BAD: names how the code works and mocks an internal collaborator
test("checkout calls paymentService.process", async () => {
  const mockPayment = jest.mock(paymentService);
  await checkout(cart, payment);
  expect(mockPayment.process).toHaveBeenCalledWith(cart.total);
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

// GOOD: the behaviour that depends on the decision
test("a failing call is retried five times and then gives up", async () => {
  const client = failingClient();
  await expect(fetchWithRetry(client)).rejects.toThrow();
  expect(client.attempts).toBe(6);
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
// BAD: the mock swallows the config write that duplicate detection reads
vi.mock("ToolCatalog", () => ({
  discoverAndCacheTools: vi.fn().mockResolvedValue(undefined),
}));

// GOOD: mock only the slow server startup; the config write stays real
vi.mock("MCPServerManager");
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
