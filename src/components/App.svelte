<script>
  import { currentPage } from '$lib/stores/app.js';
  import Splash from './Splash.svelte';
  import ChainBanner from './ChainBanner.svelte';
  import Navbar from './Navbar.svelte';
  import Toast from './Toast.svelte';
  import Footer from './Footer.svelte';
  import Home from './pages/Home.svelte';
  import Leaderboard from './pages/Leaderboard.svelte';
  import Ecosystem from './pages/Ecosystem.svelte';
  import Guides from './pages/Guides.svelte';
  import Points from './pages/Points.svelte';
  import Submit from './pages/Submit.svelte';

  let showSplash = true;
  let appVisible = false;

  function enterApp() {
    showSplash = false;
    appVisible = true;
  }
</script>

{#if showSplash}
  <Splash on:enter={enterApp} />
{/if}

{#if appVisible}
  <div id="app" style="position:relative;z-index:1">
    <ChainBanner />
    <Navbar />

    {#if $currentPage === 'home'}
      <Home />
    {:else if $currentPage === 'leaderboard'}
      <Leaderboard />
    {:else if $currentPage === 'ecosystem'}
      <Ecosystem />
    {:else if $currentPage === 'guides'}
      <Guides />
    {:else if $currentPage === 'points'}
      <Points />
    {:else if $currentPage === 'submit'}
      <Submit />
    {/if}

    <Footer />
  </div>
{/if}

<Toast />
