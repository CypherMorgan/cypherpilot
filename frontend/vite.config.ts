import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

// Default base is "/" for local dev.
// For GitHub Pages at https://cyphermorgan.github.io/qpilot/, set VITE_BASE_PATH=/qpilot/
const base = process.env.VITE_BASE_PATH || "/";

export default defineConfig({
  base,
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "src"),
    },
  },
  server: {
    port: 5173,
    host: true,
  },
});
