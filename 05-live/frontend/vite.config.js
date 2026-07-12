import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5510,
    proxy: {
      "/ws": { target: "ws://localhost:8500", ws: true },
      "/api": { target: "http://localhost:8500" },
    },
  },
});
