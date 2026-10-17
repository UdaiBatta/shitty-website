import test from "node:test";
import assert from "node:assert/strict";
import { createGuestbookHandler } from "../netlify/functions/guestbook-core.mjs";

function memoryStore() {
  const entries = new Map();
  return {
    entries,
    async list({ prefix }) {
      return { blobs: [...entries.keys()].filter((key) => key.startsWith(prefix)).map((key) => ({ key })) };
    },
    async get(key) {
      return entries.has(key) ? JSON.parse(entries.get(key)) : null;
    },
    async set(key, value) {
      entries.set(key, value);
    },
  };
}

test("lists timestamped sample notes and accepts a named public entry", async () => {
  const store = memoryStore();
  const fixedNow = () => new Date("2026-10-17T12:00:00.000Z");
  const handler = createGuestbookHandler(store, fixedNow);

  const before = await handler(new Request("https://example.test/api/guestbook/"));
  const initial = await before.json();
  assert.equal(initial.entries.length, 5);
  assert.equal(initial.entries[0].is_sample, true);
  assert.ok(initial.entries[0].created_at);

  const response = await handler(new Request("https://example.test/api/guestbook/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name: "  Test   Visitor ", message: " Hello, company! " }),
  }));
  assert.equal(response.status, 201);
  assert.deepEqual((await response.json()).entry, {
    name: "Test Visitor",
    message: "Hello, company!",
    is_sample: false,
    created_at: "2026-10-17T12:00:00.000Z",
  });

  const after = await handler(new Request("https://example.test/api/guestbook/"));
  const saved = await after.json();
  assert.equal(saved.entries[0].name, "Test Visitor");
  assert.equal(saved.entries.length, 6);
});

test("rejects invalid or oversized entries", async () => {
  const handler = createGuestbookHandler(memoryStore());
  const response = await handler(new Request("https://example.test/api/guestbook/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name: "Visitor", message: "x".repeat(251) }),
  }));
  assert.equal(response.status, 400);
  assert.equal((await response.json()).error, "Enter a message of 1 to 250 characters.");
});
