import { defineConfig } from 'astro/config';
import svelte from '@astrojs/svelte';
import vercel from '@astrojs/vercel';  // ← Node ki jagah Vercel

export default defineConfig({
  integrations: [svelte()],
  output: 'server',
  adapter: vercel()  // ← Node ki jagah Vercel
});