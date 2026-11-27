import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// BASE_PATH vaut "/<nom-du-dépôt>/" pour GitHub Pages, "/" en local.
// (Ce fichier n'est pas vérifié par `tsc` : vitest 2 embarque sa propre version de Vite.)
export default defineConfig({
  base: process.env.BASE_PATH ?? "/",
  plugins: [react()],
  // @ts-expect-error clé lue par vitest
  test: { environment: "jsdom", globals: true, setupFiles: ["./src/setupTests.ts"] },
});
