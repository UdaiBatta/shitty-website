const sampleEntries = [
  ["PRINTER VICTIM 1998", "The printer ate page one. I rate this onboarding five potatoes.", 1],
  ["OFFICE POTATO #2", "Signed the sandwich policy. I require one crouton per meeting.", 5],
  ["SANDWICH LIAISON", "Applied for quality assurance. The bread seemed qualified.", 12],
  ["FORM ESCAPEE", "I escaped the application with my dignity mostly intact.", 30],
  ["FICTIONAL CEO FAN CLUB", "The team gets the credit. The printer gets a stern look.", 72],
];

const json = (body, status = 200) => new Response(JSON.stringify(body), {
  status,
  headers: { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store" },
});

export function createGuestbookHandler(store, now = () => new Date()) {
  return async (request) => {
    if (request.method === "GET") {
      const { blobs } = await store.list({ prefix: "entries/" });
      const savedEntries = await Promise.all(blobs.map(({ key }) => store.get(key, { type: "json" })));
      const samples = sampleEntries.map(([name, message, hoursAgo]) => ({
        name,
        message,
        is_sample: true,
        created_at: new Date(now().getTime() - hoursAgo * 60 * 60 * 1000).toISOString(),
      }));
      const entries = [...savedEntries.filter(Boolean), ...samples]
        .sort((a, b) => Date.parse(b.created_at) - Date.parse(a.created_at))
        .slice(0, 30);
      return json({ entries });
    }

    if (request.method !== "POST") return json({ error: "Method not allowed." }, 405);
    if (Number(request.headers.get("content-length") || 0) > 1024) {
      return json({ error: "Guestbook entry is too large." }, 400);
    }

    let payload;
    try {
      const body = await request.text();
      if (new TextEncoder().encode(body).byteLength > 1024) return json({ error: "Guestbook entry is too large." }, 400);
      payload = JSON.parse(body);
    } catch {
      return json({ error: "The guestbook entry could not be read." }, 400);
    }
    if (!payload || typeof payload !== "object" || Array.isArray(payload) ||
        Object.keys(payload).length !== 2 || !Object.hasOwn(payload, "name") || !Object.hasOwn(payload, "message")) {
      return json({ error: "Provide only a name and message." }, 400);
    }
    if (typeof payload.name !== "string" || typeof payload.message !== "string") {
      return json({ error: "Name and message must be text." }, 400);
    }

    const name = payload.name.trim().replace(/\s+/g, " ");
    const message = payload.message.trim();
    if (!name || name.length > 50) return json({ error: "Enter a name or nickname of 1 to 50 characters." }, 400);
    if (!message || message.length > 250) return json({ error: "Enter a message of 1 to 250 characters." }, 400);

    const entry = { name, message, is_sample: false, created_at: now().toISOString() };
    await store.set(`entries/${crypto.randomUUID()}`, JSON.stringify(entry));
    return json({ entry }, 201);
  };
}
