<script>
  import { currentPage } from '../stores/app.js';

  let collapsed = false;

  const pageUrls = {
    'home': '/', 'leaderboard': '/leaderboard', 'weekly': '/weekly',
    'fastgpu': '/fastgpu', 'hyperscale': '/hyperscale', 'userdashboard': '/userdashboard',
    'ecosystem': '/ecosystem', 'guides': '/guides', 'submitjob': '/submitjob',
    'walletjobs': '/walletjobs', 'submit': '/submit'
  };

  function navigate(page) {
    currentPage.set(page);
    window.scrollTo(0, 0);
    window.history.pushState({}, '', pageUrls[page] || '/');
  }

  const explorerLinks = [
    { page: 'home', label: 'Home', icon: '🏠' },
    { page: 'leaderboard', label: 'Leaderboard', icon: '🏆' },
    { page: 'weekly', label: 'Weekly Points', icon: '📊' },
    { page: 'submitjob', label: 'Submit Job', icon: '⚡' },
    { page: 'walletjobs', label: 'Wallet Jobs', icon: '💼' },
    { page: 'userdashboard', label: 'Dashboard', icon: '👤' },
    { page: 'validators', label: 'Validators', icon: '⚡' },
  ];

  const toolLinks = [
    { page: 'fastgpu', label: 'Fast GPU', icon: '🖥️' },
    { page: 'hyperscale', label: 'Hyperscale Jobs', icon: '🤖' },
    { page: 'ecosystem', label: 'Ecosystem', icon: '🌐' },
    { page: 'guides', label: 'Guides', icon: '📚' },
  ];

  const externalLinks = [
    { href: 'https://republicai.io', label: 'Website', icon: '🔗' },
    { href: 'https://discord.gg/republicai', label: 'Discord', icon: '💬' },
    { href: 'https://twitter.com/republicai', label: 'Twitter', icon: '🐦' },
  ];
</script>

<aside class="sidebar {collapsed ? 'collapsed' : ''}">
  <!-- Logo -->
  <div class="sidebar-logo" on:click={() => navigate('home')}>
    <div class="logo-icon">
      <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
        <polygon points="16,2 30,9 30,23 16,30 2,23 2,9" fill="none" stroke="#ff3c00" stroke-width="1.5"/>
        <polygon points="16,8 24,12 24,20 16,24 8,20 8,12" fill="#ff3c00" opacity="0.2"/>
        <circle cx="16" cy="16" r="4" fill="#ff3c00"/>
      </svg>
    </div>
    {#if !collapsed}
      <div class="logo-text">
        <span class="logo-main">REPUBLIC</span>
        <span class="logo-sub">/STATS</span>
      </div>
    {/if}
  </div>

  <!-- Section: Explorer -->
  <div class="sidebar-section">
    {#if !collapsed}
      <div class="section-label">Explorer</div>
    {/if}
    {#each explorerLinks as item}
      <button
        class="sidebar-link {$currentPage === item.page ? 'active' : ''}"
        on:click={() => navigate(item.page)}
        title={item.label}
      >
        <span class="link-icon">{item.icon}</span>
        {#if !collapsed}
          <span class="link-label">{item.label}</span>
        {/if}
        {#if $currentPage === item.page}
          <span class="active-bar"></span>
        {/if}
      </button>
    {/each}
  </div>

  <!-- Section: Tools -->
  <div class="sidebar-section">
    {#if !collapsed}
      <div class="section-label">Tools</div>
    {/if}
    {#each toolLinks as item}
      <button
        class="sidebar-link {$currentPage === item.page ? 'active' : ''}"
        on:click={() => navigate(item.page)}
        title={item.label}
      >
        <span class="link-icon">{item.icon}</span>
        {#if !collapsed}
          <span class="link-label">{item.label}</span>
        {/if}
        {#if $currentPage === item.page}
          <span class="active-bar"></span>
        {/if}
      </button>
    {/each}
  </div>

  <!-- Section: Republic AI -->
  <div class="sidebar-section">
    {#if !collapsed}
      <div class="section-label">Republic AI</div>
    {/if}
    {#each externalLinks as item}
      <a
        href={item.href}
        target="_blank"
        rel="noopener"
        class="sidebar-link external"
        title={item.label}
      >
        <span class="link-icon">{item.icon}</span>
        {#if !collapsed}
          <span class="link-label">{item.label}</span>
        {/if}
      </a>
    {/each}
  </div>

  <!-- Submit button -->
  <div class="sidebar-footer">
    <button class="btn-submit" on:click={() => navigate('submit')}>
      {#if collapsed}
        <span>+</span>
      {:else}
        <span>+ Submit Project</span>
      {/if}
    </button>
    <button class="collapse-btn" on:click={() => collapsed = !collapsed} title="Toggle sidebar">
      {collapsed ? '→' : '←'}
    </button>
  </div>

  <!-- Version -->
  {#if !collapsed}
    <div class="sidebar-version">
      Built by 0xDarkSeidBull · RepublicStats
    </div>
  {/if}
</aside>

<style>
  .sidebar {
    position: fixed;
    top: 0;
    left: 0;
    bottom: 0;
    width: 220px;
    background: #060810;
    border-right: 1px solid rgba(255,60,0,0.1);
    display: flex;
    flex-direction: column;
    gap: 0;
    z-index: 100;
    overflow-y: auto;
    overflow-x: hidden;
    transition: width 0.25s ease;
    scrollbar-width: none;
  }
  .sidebar::-webkit-scrollbar { display: none; }
  .sidebar.collapsed { width: 60px; }

  /* Logo */
  .sidebar-logo {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 20px 16px;
    cursor: pointer;
    border-bottom: 1px solid rgba(255,60,0,0.08);
    margin-bottom: 8px;
    flex-shrink: 0;
  }
  .logo-icon { flex-shrink: 0; }
  .logo-text { display: flex; flex-direction: column; line-height: 1; }
  .logo-main {
    font-family: var(--font-display);
    font-size: 16px;
    letter-spacing: 2px;
    color: var(--text);
  }
  .logo-sub {
    font-family: var(--font-display);
    font-size: 14px;
    letter-spacing: 2px;
    color: var(--accent);
  }

  /* Sections */
  .sidebar-section {
    padding: 4px 8px;
    margin-bottom: 8px;
  }
  .section-label {
    font-family: var(--font-mono);
    font-size: 10px;
    color: var(--muted);
    letter-spacing: 1.5px;
    text-transform: uppercase;
    padding: 8px 8px 6px;
  }

  /* Links */
  .sidebar-link {
    position: relative;
    display: flex;
    align-items: center;
    gap: 10px;
    width: 100%;
    padding: 9px 10px;
    background: none;
    border: none;
    border-radius: 8px;
    color: #6b7280;
    font-family: var(--font-body);
    font-size: 13px;
    font-weight: 500;
    letter-spacing: 0.3px;
    cursor: pointer;
    text-align: left;
    text-decoration: none;
    transition: all 0.15s;
  }
  .sidebar-link:hover {
    background: rgba(255,60,0,0.06);
    color: var(--text);
  }
  .sidebar-link.active {
    background: rgba(255,60,0,0.1);
    color: var(--accent);
  }
  .link-icon { font-size: 15px; flex-shrink: 0; width: 20px; text-align: center; }
  .link-label { flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .active-bar {
    position: absolute;
    right: 0;
    top: 50%;
    transform: translateY(-50%);
    width: 3px;
    height: 20px;
    background: var(--accent);
    border-radius: 3px 0 0 3px;
  }

  /* Footer */
  .sidebar-footer {
    margin-top: auto;
    padding: 12px 8px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    border-top: 1px solid rgba(255,60,0,0.08);
  }
  .btn-submit {
    background: var(--accent);
    color: #000;
    border: none;
    padding: 9px 12px;
    font-family: var(--font-display);
    font-size: 13px;
    letter-spacing: 1px;
    border-radius: 8px;
    cursor: pointer;
    transition: opacity 0.2s;
    width: 100%;
    text-align: center;
  }
  .btn-submit:hover { opacity: 0.85; }
  .collapse-btn {
    background: rgba(255,255,255,0.05);
    border: 1px solid var(--border);
    color: var(--muted);
    padding: 6px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 12px;
    transition: all 0.2s;
    width: 100%;
  }
  .collapse-btn:hover { color: var(--text); background: rgba(255,255,255,0.08); }

  .sidebar-version {
    padding: 12px 16px;
    font-size: 10px;
    color: var(--muted);
    opacity: 0.5;
    font-family: var(--font-mono);
  }

  /* Mobile */
  @media (max-width: 768px) {
    .sidebar { display: none; }
  }
</style>