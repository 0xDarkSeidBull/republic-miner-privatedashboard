<script>
  import { currentPage, isLightMode, showToast } from '../stores/app.js';

  let menuOpen = false;

  function navigate(page) {
    currentPage.set(page);
    menuOpen = false;
    document.body.style.overflow = '';
    window.scrollTo(0, 0);
  }

  function toggleMenu() {
    menuOpen = !menuOpen;
    document.body.style.overflow = menuOpen ? 'hidden' : '';
  }

  function toggleTheme() {
    isLightMode.update(v => !v);
    document.body.classList.toggle('light-mode', $isLightMode);
    showToast($isLightMode ? '☀️ Light mode' : '🌙 Dark mode');
  }

  $: if (typeof document !== 'undefined') {
    document.body.classList.toggle('light-mode', $isLightMode);
  }
</script>

<nav>
  <div class="nav-logo" on:click={() => navigate('home')} style="cursor:pointer">
    <div class="nav-logo-icon">⛏</div>
    <div class="nav-logo-text">REPUBLIC<span>/STATS</span></div>
  </div>
  <div class="nav-links">
    {#each ['home','leaderboard','weekly','fastgpu','ecosystem','guides','submitjob','walletjobs'] as page}
      <button class="nav-link {$currentPage === page ? 'active' : ''}" on:click={() => navigate(page)}>
        {page === 'home' ? 'Home' 
        : page === 'leaderboard' ? 'Leaderboard' 
        : page === 'weekly' ? 'Weekly Points' 
        : page === 'fastgpu' ? '⚡ Fast GPU' 
        : page === 'ecosystem' ? 'Ecosystem' 
        : page === 'guides' ? 'Guides' 
        : page === 'walletjobs' ? 'Wallet Jobs' 
        : '⚡ Submit Job'}
      </button>
    {/each}
    <button class="nav-btn-submit" on:click={() => navigate('submit')}>+ Submit</button>
  </div>
  <button class="hamburger {menuOpen ? 'open' : ''}" on:click={toggleMenu}>
    <span></span><span></span><span></span>
  </button>
</nav>

{#if menuOpen}
<div class="mobile-menu open">
  <div class="mobile-menu-header">
    <div class="nav-logo">
      <div class="nav-logo-icon">⛏</div>
      <div class="nav-logo-text">REPUBLIC<span>/STATS</span></div>
    </div>
    <button class="mobile-close" on:click={toggleMenu}>✕</button>
  </div>
  <div class="mobile-nav-links">
    {#each [
      ['home','🏠 Home'],
      ['leaderboard','🏆 Leaderboard'],
      ['weekly','🏆 Weekly Points'],
      ['fastgpu','⚡ Fast GPU'],
      ['ecosystem','🌐 Ecosystem'],
      ['guides','📚 Guides'],
      ['submitjob','⚡ Submit Job'],
      ['walletjobs','💼 Wallet Jobs'],
      ['submit','+ Submit Project']
    ] as [page, label]}
      <button class="mobile-nav-link {$currentPage === page ? 'active' : ''}" on:click={() => navigate(page)}>
        {label}
      </button>
    {/each}
  </div>
</div>
{/if}

<!-- Theme toggle -->
<button class="theme-toggle" on:click={toggleTheme} title="Toggle theme">
  {$isLightMode ? '🌙' : '☀️'}
</button>