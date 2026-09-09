import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "tests/browser",
  fullyParallel: false,
  workers: 1,
  use: { baseURL: "http://127.0.0.1:8000", trace: "retain-on-failure" },
  webServer: {
    command: ".venv/bin/python scripts/dev.py --production --test",
    url: "http://127.0.0.1:8000/api/ready",
    reuseExistingServer: false,
    timeout: 30000,
  },
  reporter: [["list"], ["html", { open: "never" }]],
});
