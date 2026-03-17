<script>
  import { onMount, onDestroy } from 'svelte';
  import { API } from '../stores/app.js';

  let status = 'checking';
  let text = 'Checking chain status...';
  let interval;

  async function checkChain() {
    try {
      const r = await fetch(API + '/api/chain_status', { signal: AbortSignal.timeout(7000) });
      const d = await r.json();
      const isLive = d.is_live === true || d.status === 'live' || d.status === 'active'
        || d.halted === false || d.is_halted === false || d.live === true;
      const lb = d.latest_block || d.height || d.latest_block_height || d.block_height || '—';
      const sb = d.last_scanned || d.last_scanned_height || lb;
      const fn = n => (n && n !== '—') ? Number(n).toLocaleString() : '—';
      if (isLive) {
        status = 'live';
        text = `✓ Chain LIVE · Latest: ${fn(lb)} · Scanned: ${fn(sb)}`;
      } else {
        status = 'halted';
        text = `⚠ Chain HALTED · ${d.message || 'Check Discord'}`;
      }
    } catch {
      status = 'checking';
      text = 'Checking chain status...';
    }
  }

  onMount(() => {
    checkChain();
    interval = setInterval(checkChain, 30000);
  });

  onDestroy(() => clearInterval(interval));
</script>

<div id="chainBanner" class={status === 'halted' ? 'halted' : status === 'checking' ? 'checking' : ''}>
  <span class="chain-dot {status === 'live' ? 'live' : status === 'halted' ? 'halted' : 'checking'}"></span>
  <span>{text}</span>
</div>
