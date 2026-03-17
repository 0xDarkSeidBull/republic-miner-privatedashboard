<script>
  import { createEventDispatcher } from 'svelte';
  const dispatch = createEventDispatcher();

  function enter() {
    dispatch('enter');
  }
</script>

<div id="splash" on:click={enter}>
  <div class="splash-grid"></div>
  <div class="splash-glow"></div>
  <div class="splash-scan"></div>
  <div class="splash-bracket tl"></div>
  <div class="splash-bracket tr"></div>
  <div class="splash-bracket bl"></div>
  <div class="splash-bracket br"></div>
  <div class="splash-content">
    <div class="splash-eyebrow">Republic AI Testnet</div>
    <div class="splash-title">GPU MINING</div>
    <div class="splash-sub">STATS</div>
    <div class="splash-terminal">
      <div class="term-line l1">$ republic-miner status --node live</div>
      <div class="term-line l2">✓ GPU: RTX 4090 · 24GB VRAM · CUDA 12.3</div>
      <div class="term-line l3">⛏ Jobs Submitted: 112,845 · Results: 74,528</div>
      <div class="term-line l4">🏆 Top Miner: 47,525 pts · Chain: LIVE #703,895</div>
      <div class="term-line l5">► All systems operational. Rewards: ACTIVE<span class="term-cursor"></span></div>
    </div>
    <div class="splash-cta">— CLICK ANYWHERE TO CHECK YOUR GPU MINING STATS —</div>
  </div>
</div>

<style>
#splash {
  position: fixed; inset: 0; z-index: 9999;
  background: var(--bg);
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  overflow: hidden; cursor: pointer;
}
.splash-grid {
  position: absolute; inset: 0;
  background-image:
    linear-gradient(rgba(255,60,0,.07) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,60,0,.07) 1px, transparent 1px);
  background-size: 60px 60px;
  animation: grid-pan 20s linear infinite;
}
@keyframes grid-pan { from { background-position: 0 0; } to { background-position: 60px 60px; } }
.splash-glow {
  position: absolute; width: 800px; height: 800px;
  background: radial-gradient(circle, rgba(255,60,0,.12) 0%, rgba(255,106,0,.06) 35%, transparent 70%);
  border-radius: 50%; animation: glow-pulse 3s ease-in-out infinite;
}
@keyframes glow-pulse { 0%,100% { transform: scale(1); opacity: .8; } 50% { transform: scale(1.1); opacity: 1; } }
.splash-bracket { position: absolute; width: 60px; height: 60px; border-color: var(--accent); border-style: solid; opacity: .6; }
.splash-bracket.tl { top: 40px; left: 40px; border-width: 3px 0 0 3px; }
.splash-bracket.tr { top: 40px; right: 40px; border-width: 3px 3px 0 0; }
.splash-bracket.bl { bottom: 40px; left: 40px; border-width: 0 0 3px 3px; }
.splash-bracket.br { bottom: 40px; right: 40px; border-width: 0 3px 3px 0; }
.splash-scan {
  position: absolute; left: 0; right: 0; height: 2px;
  background: linear-gradient(90deg, transparent, var(--accent), transparent);
  animation: scan 4s linear infinite; top: 0;
}
@keyframes scan { from { top: 0; } to { top: 100%; } }
.splash-content { position: relative; z-index: 2; text-align: center; padding: 0 20px; }
.splash-eyebrow {
  font-family: var(--font-mono); font-size: 12px;
  color: var(--accent); letter-spacing: .3em;
  text-transform: uppercase; margin-bottom: 24px;
  display: flex; align-items: center; justify-content: center; gap: 12px;
}
.splash-eyebrow::before, .splash-eyebrow::after { content: ''; flex: 1; max-width: 80px; height: 1px; background: linear-gradient(90deg, transparent, var(--accent)); }
.splash-eyebrow::after { background: linear-gradient(90deg, var(--accent), transparent); }
.splash-title {
  font-family: var(--font-display);
  font-size: clamp(64px, 10vw, 140px);
  line-height: .92; letter-spacing: .02em; margin-bottom: 8px;
  background: linear-gradient(135deg, #fff 0%, #ff6a00 40%, #ff3c00 70%, #ff0055 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
  filter: drop-shadow(0 0 40px rgba(255,60,0,.4));
}
.splash-sub {
  font-family: var(--font-display);
  font-size: clamp(32px, 5vw, 64px);
  line-height: 1; letter-spacing: .08em;
  color: var(--blue);
  filter: drop-shadow(0 0 20px rgba(0,204,255,.5));
  margin-bottom: 40px;
}
.splash-terminal {
  background: rgba(8,9,15,.9); border: 1px solid rgba(255,60,0,.3);
  padding: 20px 28px; max-width: 560px; margin: 0 auto 40px;
  position: relative; text-align: left;
}
.splash-terminal::before {
  content: 'REPUBLIC-AI MINER v2.4.1';
  position: absolute; top: -10px; left: 20px;
  font-family: var(--font-mono); font-size: 10px;
  color: var(--accent); background: var(--bg);
  padding: 0 8px; letter-spacing: .15em;
}
.term-line { font-family: var(--font-mono); font-size: 13px; line-height: 2; overflow: hidden; white-space: nowrap; }
.term-line.l1 { color: var(--muted); animation: type 0s .1s forwards; width: 0; }
.term-line.l2 { color: var(--green); animation: type 0s .6s forwards; width: 0; }
.term-line.l3 { color: var(--blue); animation: type 0s 1.1s forwards; width: 0; }
.term-line.l4 { color: var(--accent3); animation: type 0s 1.6s forwards; width: 0; }
.term-line.l5 { color: var(--text); animation: type 0s 2.1s forwards; width: 0; }
@keyframes type { to { width: 100%; } }
.term-cursor { display: inline-block; width: 8px; height: 14px; background: var(--accent); animation: blink .8s step-end infinite; vertical-align: middle; margin-left: 2px; }
@keyframes blink { 0%,100% { opacity: 1; } 50% { opacity: 0; } }
.splash-cta {
  font-family: var(--font-display); font-size: 18px; letter-spacing: .2em;
  color: rgba(255,255,255,.4);
  animation: fade-cta 1.5s ease-in-out infinite alternate;
}
@keyframes fade-cta { from { opacity: .3; transform: translateY(2px); } to { opacity: .8; transform: translateY(-2px); } }
</style>
