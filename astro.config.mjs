import { defineConfig } from 'astro/config';
import svelte from '@astrojs/svelte';

export default defineConfig({
  integrations: [svelte()],
  output: 'server', // ✅ ADD THIS - API endpoints ke liye zaroori hai
});