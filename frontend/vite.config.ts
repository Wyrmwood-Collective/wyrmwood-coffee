import { fileURLToPath, URL } from "node:url";

import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import vueDevTools from "vite-plugin-vue-devtools";

const repoRoot = fileURLToPath(new URL("..", import.meta.url));

// https://vite.dev/config/
export default defineConfig({
  base: "/app/",
  plugins: [vue(), vueDevTools()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
      // WC-69 sample purchase histories — frontend filters; no GET /purchases.
      "@sample-data": fileURLToPath(new URL("../data/sample_data.json", import.meta.url)),
    },
  },
  server: {
    fs: {
      allow: [repoRoot],
    },
    proxy: {
      "/auth": "http://127.0.0.1:8000",
      "/employees": "http://127.0.0.1:8000",
      "/vendors": "http://127.0.0.1:8000",
      "/ingredients": "http://127.0.0.1:8000",
      "/customers": "http://127.0.0.1:8000",
      "/drinks": "http://127.0.0.1:8000",
      "/baked-goods": "http://127.0.0.1:8000",
      "/promotions": "http://127.0.0.1:8000",
      "/reports": "http://127.0.0.1:8000",
    },
  },
});
