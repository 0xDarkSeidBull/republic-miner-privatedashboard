<script>
  import { currentPage, isLightMode, toastMsg } from '../stores/app.js';

  let menuOpen = false;

  const pageUrls = {
    'home': '/', 'leaderboard': '/leaderboard', 'weekly': '/weekly',
    'fastgpu': '/fastgpu', 'hyperscale': '/hyperscale', 'userdashboard': '/userdashboard',
    'ecosystem': '/ecosystem', 'guides': '/guides', 'submitjob': '/submitjob',
    'walletjobs': '/walletjobs', 'submit': '/submit'
  };

  function navigate(page) {
    currentPage.set(page);
    menuOpen = false;
    document.body.style.overflow = '';
    window.scrollTo(0, 0);
    window.history.pushState({}, '', pageUrls[page] || '/');
  }

  function toggleMenu() {
    menuOpen = !menuOpen;
    document.body.style.overflow = menuOpen ? 'hidden' : '';
  }

  const navItems = [
    { page: 'home', label: 'Home' },
    { page: 'leaderboard', label: 'Leaderboard' },
    { page: 'weekly', label: 'Weekly Points' },
    { page: 'fastgpu', label: '⚡ Fast GPU' },
    { page: 'hyperscale', label: '🤖 Hyperscale' },
    { page: 'userdashboard', label: 'Dashboard' },
    { page: 'ecosystem', label: 'Ecosystem' },
    { page: 'guides', label: 'Guides' },
    { page: 'submitjob', label: 'Submit Job' },
    { page: 'walletjobs', label: 'Wallet Jobs' },
  ];
</script>

<nav class="navbar">
  <div class="nav-inner">
    <!-- Logo -->
    <div class="nav-logo" on:click={() => navigate('home')}>
      <div class="logo-icon">
        <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
          <polygon points="14,2 26,8 26,20 14,26 2,20 2,8" fill="none" stroke="var(--accent)" stroke-width="2"/>
          <polygon points="14,7 21,11 21,17 14,21 7,17 7,11" fill="var(--accent)" opacity="0.3"/>
          <circle cx="14" cy="14" r="3" fill="var(--accent)"/>
        </svg>
      </div>
      <span class="logo-text">REPUBLIC<span class="logo-slash">/</span><span class="logo-stats">STATS</span></span>
    </div>

    <!-- Desktop Nav -->
    <div class="nav-links">
      {#each navItems as item}
        <button
          class="nav-link {$currentPage === item.page ? 'active' : ''}"
          on:click={() => navigate(item.page)}
        >
          {item.label}
          {#if $currentPage === item.page}
            <span class="nav-indicator"></span>
          {/if}
        </button>
      {/each}
    </div>

    <!-- Right side -->
    <div class="nav-right">
      <button class="btn-submit" on:click={() => navigate('submit')}>
        <span>+</span> Submit
      </button>
      <button class="hamburger {menuOpen ? 'open' : ''}" on:click={toggleMenu}>
        <span></span><span></span><span></span>
      </button>
    </div>
  </div>
</nav>

<!-- Mobile Menu -->
{#if menuOpen}
  <div class="mobile-overlay" on:click={toggleMenu}></div>
  <div class="mobile-menu open">
    <div class="mobile-header">
      <div class="nav-logo" on:click={() => navigate('home')}>
        <div class="logo-icon">
          <svg width="24" height="24" viewBox="0 0 28 28" fill="none">
            <polygon points="14,2 26,8 26,20 14,26 2,20 2,8" fill="none" stroke="var(--accent)" stroke-width="2"/>
            <circle cx="14" cy="14" r="3" fill="var(--accent)"/>
          </svg>
        </div>
        <span class="logo-text">REPUBLIC<span class="logo-slash">/</span><span class="logo-stats">STATS</span></span>
      </div>
      <button class="mobile-close" on:click={toggleMenu}>✕</button>
    </div>
    <div class="mobile-links">
      {#each [...navItems, { page: 'submit', label: '+ Submit Project' }] as item}
        <button
          class="mobile-link {$currentPage === item.page ? 'active' : ''}"
          on:click={() => navigate(item.page)}
        >
          {item.label}
        </button>
      {/each}
    </div>
  </div>
{/if}

<style>
  .navbar {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 100;
    background: rgba(5, 5, 8, 0.85);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-bottom: 1px solid rgba(255, 60, 0, 0.15);
    height: 56px;
  }

  .nav-inner {
    max-width: 1400px;
    margin: 0 auto;
    padding: 0 24px;
    height: 100%;
    display: flex;
    align-items: center;
    gap: 32px;
  }

  /* Logo */
  .nav-logo {
    display: flex;
    align-items: center;
    gap: 10px;
    cursor: pointer;
    flex-shrink: 0;
    text-decoration: none;
  }

  .logo-icon {
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .logo-text {
    font-family: var(--font-display);
    font-size: 20px;
    letter-spacing: 2px;
    color: var(--text);
    white-space: nowrap;
  }

  .logo-slash {
    color: var(--accent);
  }

  .logo-stats {
    color: var(--accent);
  }

  /* Nav Links */
  .nav-links {
    display: flex;
    align-items: center;
    gap: 2px;
    flex: 1;
    overflow: hidden;
  }

  .nav-link {
    position: relative;
    background: none;
    border: none;
    color: var(--muted);
    font-family: var(--font-body);
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
    padding: 6px 10px;
    cursor: pointer;
    transition: color 0.2s;
    white-space: nowrap;
  }

  .nav-link:hover {
    color: var(--text);
  }

  .nav-link.active {
    color: var(--accent);
  }

  .nav-indicator {
    position: absolute;
    bottom: -1px;
    left: 50%;
    transform: translateX(-50%);
    width: 20px;
    height: 2px;
    background: var(--accent);
    border-radius: 2px;
  }

  /* Right */
  .nav-right {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-shrink: 0;
  }

  .btn-submit {
    background: var(--accent);
    color: #000;
    border: none;
    padding: 7px 16px;
    font-family: var(--font-display);
    font-size: 14px;
    letter-spacing: 1px;
    border-radius: 6px;
    cursor: pointer;
    transition: opacity 0.2s, transform 0.2s;
    display: flex;
    align-items: center;
    gap: 4px;
  }

  .btn-submit:hover {
    opacity: 0.9;
    transform: translateY(-1px);
  }

  /* Hamburger */
  .hamburger {
    display: none;
    flex-direction: column;
    gap: 5px;
    background: none;
    border: none;
    cursor: pointer;
    padding: 4px;
  }

  .hamburger span {
    display: block;
    width: 22px;
    height: 2px;
    background: var(--text);
    border-radius: 2px;
    transition: all 0.3s;
  }

  .hamburger.open span:nth-child(1) { transform: rotate(45deg) translate(5px, 5px); }
  .hamburger.open span:nth-child(2) { opacity: 0; }
  .hamburger.open span:nth-child(3) { transform: rotate(-45deg) translate(5px, -5px); }

  /* Mobile */
  .mobile-overlay {
    display: none;
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.6);
    z-index: 98;
    backdrop-filter: blur(4px);
  }

  .mobile-menu {
    display: none;
    position: fixed;
    top: 0;
    right: 0;
    bottom: 0;
    width: 280px;
    background: #08090f;
    border-left: 1px solid var(--border);
    z-index: 99;
    padding: 20px;
    flex-direction: column;
    gap: 8px;
  }

  .mobile-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 24px;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--border);
  }

  .mobile-close {
    background: none;
    border: 1px solid var(--border);
    color: var(--muted);
    width: 32px;
    height: 32px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 14px;
  }

  .mobile-links {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .mobile-link {
    background: none;
    border: none;
    color: var(--muted);
    font-family: var(--font-body);
    font-size: 14px;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
    padding: 12px 16px;
    text-align: left;
    cursor: pointer;
    border-radius: 8px;
    transition: all 0.2s;
  }

  .mobile-link:hover { background: rgba(255,60,0,0.08); color: var(--text); }
  .mobile-link.active { background: rgba(255,60,0,0.12); color: var(--accent); }

  @media (max-width: 1024px) {
    .nav-links { display: none; }
    .hamburger { display: flex; }
    .mobile-overlay.open,
    .mobile-menu.open { display: flex; }
  }

  @media (max-width: 768px) {
    .nav-inner { padding: 0 16px; gap: 16px; }
    .btn-submit { display: none; }
  }
</style>