import { copyFile, mkdir } from "node:fs/promises";

await mkdir("public/static/jobs/assets", { recursive: true });
await copyFile("index.html", "public/index.html");
await copyFile(
  "jobs/static/jobs/assets/ayush-sharma.png",
  "public/static/jobs/assets/ayush-sharma.png",
);
