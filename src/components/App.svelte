<script>
  import { onMount } from 'svelte';
  import { currentPage } from '../stores/app.js';
  import Splash from './Splash.svelte';
  import ChainBanner from './ChainBanner.svelte';
  import Sidebar from './Sidebar.svelte';
  import Toast from './Toast.svelte';
  import Footer from './Footer.svelte';
  import Home from './pages/Home.svelte';
  import Leaderboard from './pages/Leaderboard.svelte';
  import Ecosystem from './pages/Ecosystem.svelte';
  import Guides from './pages/Guides.svelte';
  import Points from './pages/Points.svelte';
  import Submit from './pages/Submit.svelte';
  import Weekly from './pages/Weekly.svelte';
  import SubmitJob from './pages/SubmitJob.svelte';
  import WalletJobs from './pages/WalletJobs.svelte';
  import FastGeo from './pages/FastGeo.svelte';
  import UserDashboard from './pages/UserDashboard.svelte';
  import Hyperscale from './pages/Hyperscale.svelte';
  import Validators from './pages/Validators.svelte';

  export let initialPage = 'home';
  let showSplash = true;
  let appVisible = false;

  onMount(() => {
    currentPage.set(initialPage);
    if (initialPage !== 'home') {
      showSplash = false;
      appVisible = true;
    }
  });

  function enterApp() {
    showSplash = false;
    appVisible = true;
  }
</script>

{#if showSplash}
  <Splash on:enter={enterApp} />
{/if}

{#if appVisible}
  <div id="app" style="display:flex;min-height:100vh;position:relative;z-index:1">
    <Sidebar />
    <div class="main-content">
      <ChainBanner />
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
      {:else if $currentPage === 'submitjob'}
        <SubmitJob />
      {:else if $currentPage === 'weekly'}
        <Weekly />
      {:else if $currentPage === 'hyperscale'}
        <Hyperscale />
      {:else if $currentPage === 'userdashboard'}
        <UserDashboard />
      {:else if $currentPage === 'fastgpu'}
        <FastGeo />
      {:else if $currentPage === 'walletjobs'}
        <WalletJobs />
      {:else if $currentPage === 'validators'}
        <Validators />
      {/if}
      <Footer />
    </div>
  </div>
{/if}

<Toast />

<style>
  .main-content {
    margin-left: 220px;
    flex: 1;
    min-width: 0;
    transition: margin-left 0.25s;
  }

  @media (max-width: 768px) {
    .main-content {
      margin-left: 0;
    }
  }
</style>