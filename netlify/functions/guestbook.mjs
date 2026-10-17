import { getStore } from "@netlify/blobs";
import { createGuestbookHandler } from "./guestbook-core.mjs";

const store = getStore({ name: "corporate-guestbook", consistency: "strong" });
export default createGuestbookHandler(store);
