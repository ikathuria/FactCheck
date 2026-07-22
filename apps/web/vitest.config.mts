import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  // Vite resolves tsconfig `paths` (the `@/` alias) natively.
  resolve: { tsconfigPaths: true },
  test: {
    environment: "jsdom",
    globals: true,
    include: ["src/**/*.test.{ts,tsx}"],
    // The default `forks` pool can't spawn worker processes in restricted
    // sandboxes; a single worker thread avoids the IPC startup timeout.
    pool: "threads",
    fileParallelism: false,
  },
});
