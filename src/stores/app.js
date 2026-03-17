import { writable } from 'svelte/store';

export const currentPage = writable('home');
export const allLbData = writable([]);
export const homeRawData = writable([]);
export const ecoData = writable([]);
export const topScore = writable(0);
export const isLightMode = writable(false);
export const toastMsg = writable('');
export const activeDetailAddr = writable(null);
export const activeDetailPage = writable(null);

export const API = 'https://api.republicstats.xyz';

// ── UTILS ──
export function fmt(n) {
  if (n === null || n === undefined || n === '') return '—';
  n = Number(n);
  if (isNaN(n)) return '—';
  return n.toLocaleString();
}

export function shortAddr(a) {
  if (!a) return '—';
  return a.slice(0, 8) + '...' + a.slice(-6);
}

export function rankClass(r) {
  return r === 1 ? 'rank-1' : r === 2 ? 'rank-2' : r === 3 ? 'rank-3' : '';
}

export function uptimeBadgeHtml(u) {
  if (u === null || u === undefined) return `<span class="uptime-badge uptime-unknown">—%</span>`;
  const v = parseFloat(u);
  if (isNaN(v)) return `<span class="uptime-badge uptime-unknown">—%</span>`;
  const cls = v >= 100 ? 'uptime-100' : v >= 95 ? 'uptime-high' : 'uptime-low';
  const icon = v >= 100 ? '✓' : v >= 95 ? '~' : '!';
  return `<span class="uptime-badge ${cls}">${icon} ${v.toFixed(2)}%</span>`;
}

export function statusBadgeHtml(m) {
  if (m.jailed) return `<span class="status-badge status-jailed">Jailed</span>`;
  return (m.total || m.total_points || 0) > 0
    ? `<span class="status-badge status-active">Active</span>`
    : `<span class="status-badge status-inactive">Inactive</span>`;
}

export function getSortVal(m, key) {
  if (key === 'total') return m.total || m.total_points || 0;
  if (key === 'submit') return m.submit_job || 0;
  if (key === 'result') return m.submit_job_result || 0;
  if (key === 'uptime') return parseFloat(m.uptime || 0);
  return 0;
}

let toastTimer;
export function showToast(msg) {
  toastMsg.set(msg);
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toastMsg.set(''), 2500);
}

export async function copyText(txt) {
  await navigator.clipboard.writeText(txt);
  showToast('✓ Copied!');
}
