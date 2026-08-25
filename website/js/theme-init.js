// Runs synchronously before first paint to avoid a flash of the wrong
// theme. Kept in its own tiny file (rather than inline) so the site's
// Content-Security-Policy can use a strict script-src 'self' without
// 'unsafe-inline'.
let theme = 'dark';
try {
  const saved = localStorage.getItem('opendroid-theme');
  if (saved === 'light' || saved === 'dark') theme = saved;
} catch (e) {
  // Storage may be blocked by privacy settings; keep the safe default.
}
document.documentElement.setAttribute('data-theme', theme);
