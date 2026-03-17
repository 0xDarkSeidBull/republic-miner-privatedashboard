<script>
  import { onMount } from 'svelte';
  import { API } from '../../stores/app.js';

  let projects = [];
  let filter = 'All';

  async function loadEcosystem() {
    try {
      const r = await fetch(API + '/api/ecosystem', { signal: AbortSignal.timeout(8000) });
      const d = await r.json();
      projects = d.data || d || [];
    } catch {
      projects = [
        { name: 'Republic Stats', description: 'GPU Miner Tracker, Leaderboard & Ecosystem Dashboard', category: 'Tool', icon: '📊', url: 'https://republicstats.xyz' },
        { name: 'Republic AI', description: 'Official Republic AI testnet portal', category: 'Infrastructure', icon: '🏛️', url: 'https://republic.ai' },
      ];
    }
  }

  $: filtered = filter === 'All' ? projects : projects.filter(p => p.category === filter);

  onMount(loadEcosystem);
</script>

<div class="eco-hero">
  <h2>🌐 ECOSYSTEM</h2>
  <p>Projects, tools, and infrastructure building on Republic AI Testnet</p>
</div>

<div class="filter-bar">
  {#each [['All','All'],['AI','🤖 AI'],['Tool','🔧 Tool'],['Infrastructure','🏛️ Infra'],['Explorer','🔍 Explorer'],['DeFi','💎 DeFi'],['Other','⚡ Other']] as [val, label]}
    <button class="filter-btn {filter === val ? 'active' : ''}" on:click={() => filter = val}>{label}</button>
  {/each}
</div>

<div class="eco-grid">
  {#if filtered.length === 0}
    <div class="empty-state">No projects in this category yet.</div>
  {:else}
    {#each filtered as p}
      <div class="eco-card" on:click={() => p.url && window.open(p.url, '_blank')}>
        <div class="eco-card-header">
          <div class="eco-card-icon">{p.icon || '🔷'}</div>
          <span class="cat-badge cat-{(p.category||'Other').replace(/\s+/g,'')}">{p.category || 'Other'}</span>
        </div>
        <div class="eco-card-name">{p.name}</div>
        <div class="eco-card-desc">{p.description || ''}</div>
        {#if p.url}<span class="eco-card-link">→ Visit site</span>{/if}
      </div>
    {/each}
  {/if}
</div>
