/* Seasonal theme: auto-pick by month, cycle with the nav button, remember the choice.
   Shared by the top page and the blog pages. */
(() => {
  const SEASONS = ['spring', 'summer', 'autumn', 'winter'];
  const EMOJI = { spring: '🌸', summer: '🌊', autumn: '🍁', winter: '⛄' };
  const btn = document.getElementById('season-btn');
  const byMonth = m => (m >= 3 && m <= 5) ? 'spring' : (m >= 6 && m <= 8) ? 'summer' : (m >= 9 && m <= 11) ? 'autumn' : 'winter';
  let season = localStorage.getItem('season') || byMonth(new Date().getMonth() + 1);
  if (!SEASONS.includes(season)) season = 'summer';
  const apply = () => {
    document.documentElement.dataset.season = season;
    if (!btn) return;
    btn.textContent = EMOJI[season];
    btn.title = 'Season: ' + season + ' — click to change';
  };
  btn?.addEventListener('click', () => {
    season = SEASONS[(SEASONS.indexOf(season) + 1) % SEASONS.length];
    localStorage.setItem('season', season);
    apply();
  });
  apply();
})();
