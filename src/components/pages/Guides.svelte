<script>
  import { showToast } from '../../stores/app.js';

  let activeGuide = 'gpu';

  function copyCode(btn) {
    const pre = btn.nextElementSibling;
    navigator.clipboard.writeText(pre.textContent).then(() => {
      btn.textContent = '✓ copied';
      setTimeout(() => btn.textContent = 'copy', 1500);
    });
  }
</script>

<div class="guides-wrap">
  <div class="page-title">GUIDES</div>
  <div class="page-sub">Official and community guides for running Republic AI nodes and miners</div>

  <div class="guide-section-label">🔗 Official Resources</div>
  <div class="guide-links">
    <a href="https://republic.ai" target="_blank" class="guide-link-btn official">🏛️ Republic AI</a>
    <a href="https://docs.republic.ai" target="_blank" class="guide-link-btn official">📖 Docs</a>
    <a href="https://discord.gg/republicai" target="_blank" class="guide-link-btn discord">💬 Discord</a>
    <a href="https://github.com/0xDarkSeidBull/republic-miner-scripts" target="_blank" class="guide-link-btn community">🐙 GitHub</a>
  </div>

  <div class="guide-tabs">
    {#each [['gpu','⛏️ GPU Miner'],['cpu','🖥️ CPU Validator'],['snapshot','📸 Snapshot'],['cmds','⚡ Commands']] as [id, label]}
      <button class="guide-tab {activeGuide === id ? 'active' : ''}" on:click={() => activeGuide = id}>{label}</button>
    {/each}
  </div>

  {#if activeGuide === 'gpu'}
  <div>
    <div class="guide-note">ℹ️ GPU miner setup for Republic AI Testnet. Always check Discord for the latest updates.</div>
    <div class="guide-step">
      <h3>1. System Requirements</h3>
      <div class="code-block"><button class="code-copy" on:click={e => copyCode(e.target)}>copy</button><pre>OS: Ubuntu 22.04 / 24.04 LTS
GPU: NVIDIA 8GB+ VRAM (RTX 3080/4090/A100)
RAM: 16GB min, 32GB recommended
Disk: 100GB+ SSD | CPU: 8 cores min</pre></div>
    </div>
    <div class="guide-step">
      <h3>2. Install Dependencies</h3>
      <div class="code-block"><button class="code-copy" on:click={e => copyCode(e.target)}>copy</button><pre>sudo apt update && sudo apt upgrade -y
sudo apt install -y curl wget git build-essential jq lz4 unzip</pre></div>
    </div>
    <div class="guide-step">
      <h3>3. Install NVIDIA CUDA</h3>
      <div class="code-block"><button class="code-copy" on:click={e => copyCode(e.target)}>copy</button><pre>wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt-get update && sudo apt-get install -y cuda-toolkit-12-3
nvidia-smi</pre></div>
    </div>
    <div class="guide-step">
      <h3>4. Install GPU Miner</h3>
      <div class="code-block"><button class="code-copy" on:click={e => copyCode(e.target)}>copy</button><pre>curl -sSL https://raw.githubusercontent.com/RepublicAI/gpu-miner/main/install.sh | bash</pre></div>
      <div class="guide-warn">⚠️ Always verify install scripts from official sources. Check Discord for latest version.</div>
    </div>
    <div class="guide-step">
      <h3>5. Configure & Start</h3>
      <div class="code-block"><button class="code-copy" on:click={e => copyCode(e.target)}>copy</button><pre>export WALLET_ADDRESS="rai1your_address_here"
export MONIKER="YourMinerName"
sudo systemctl enable republic-miner
sudo systemctl start republic-miner
journalctl -u republic-miner -f -o cat</pre></div>
    </div>
  </div>
  {/if}

  {#if activeGuide === 'cpu'}
  <div>
    <div class="guide-note">ℹ️ CPU Validator guide for Republic AI Testnet.</div>
    <div class="guide-step">
      <h3>1. Install & Init Node</h3>
      <div class="code-block"><button class="code-copy" on:click={e => copyCode(e.target)}>copy</button><pre>curl -sSL https://raw.githubusercontent.com/RepublicAI/node/main/install.sh | bash
republicd init YOUR_MONIKER --chain-id republic-testnet-1</pre></div>
    </div>
    <div class="guide-step">
      <h3>2. Start & Check Sync</h3>
      <div class="code-block"><button class="code-copy" on:click={e => copyCode(e.target)}>copy</button><pre>sudo systemctl enable republicd && sudo systemctl start republicd
republicd status 2>&1 | jq .SyncInfo</pre></div>
    </div>
  </div>
  {/if}

  {#if activeGuide === 'snapshot'}
  <div>
    <div class="guide-warn">⚠️ Always backup priv_validator_key.json before applying a snapshot!</div>
    <div class="guide-step">
      <h3>Stop & Backup</h3>
      <div class="code-block"><button class="code-copy" on:click={e => copyCode(e.target)}>copy</button><pre>cp $HOME/.republic/config/priv_validator_key.json $HOME/priv_validator_key.json.bak
sudo systemctl stop republicd</pre></div>
    </div>
    <div class="guide-step">
      <h3>Apply Snapshot</h3>
      <div class="code-block"><button class="code-copy" on:click={e => copyCode(e.target)}>copy</button><pre>republicd tendermint unsafe-reset-all --home $HOME/.republic --keep-addr-book
wget -O $HOME/republic_snapshot.tar.lz4 https://snapshot.republicstats.xyz/latest.tar.lz4
lz4 -d $HOME/republic_snapshot.tar.lz4 | tar -xf - -C $HOME/.republic/
sudo systemctl start republicd</pre></div>
    </div>
  </div>
  {/if}

  {#if activeGuide === 'cmds'}
  <div>
    <div class="guide-step">
      <h3>Node Status</h3>
      <div class="code-block"><button class="code-copy" on:click={e => copyCode(e.target)}>copy</button><pre>republicd status 2>&1 | jq .SyncInfo
republicd status 2>&1 | jq .SyncInfo.catching_up</pre></div>
    </div>
    <div class="guide-step">
      <h3>API Queries</h3>
      <div class="code-block"><button class="code-copy" on:click={e => copyCode(e.target)}>copy</button><pre>curl https://api.republicstats.xyz/api/miner/YOUR_ADDRESS | jq
curl https://api.republicstats.xyz/api/leaderboard?limit=50 | jq
curl https://api.republicstats.xyz/api/stats | jq</pre></div>
    </div>
  </div>
  {/if}
</div>
