let theme = 'dark';
try {
const saved = localStorage.getItem('opendroid-theme');
if (saved === 'light' || saved === 'dark') theme = saved;
} catch (e) {
}
document.documentElement.setAttribute('data-theme', theme);
