/* Shared publication list renderer.
   Data lives in data/publications.json — edit that file to add papers. */

async function loadPublications() {
  const res = await fetch('data/publications.json', { cache: 'no-store' });
  if (!res.ok) throw new Error('failed to load publications.json');
  return res.json();
}

function boldSelf(authors) {
  return (authors || '')
    .replace(/Koki\s+Madono/gi, '<strong>Koki Madono</strong>')
    .replace(/K\.?\s*Madono/gi, '<strong>K. Madono</strong>');
}

function showDialog(title, bodyEl) {
  const dialog = document.createElement('dialog');
  dialog.className = 'pub-dialog';
  const h3 = document.createElement('h3');
  h3.textContent = title;
  const form = document.createElement('form');
  form.method = 'dialog';
  form.innerHTML = '<button>Close</button>';
  dialog.append(h3, bodyEl, form);
  document.body.appendChild(dialog);
  dialog.showModal();
  dialog.addEventListener('close', () => dialog.remove());
}

function pubItem(p) {
  const art = document.createElement('article');
  art.className = 'pub-item';

  if (p.thumb) {
    const img = document.createElement('img');
    img.className = 'pub-thumb';
    img.src = p.thumb;
    img.alt = p.title || '';
    img.loading = 'lazy';
    art.appendChild(img);
  }

  const info = document.createElement('div');
  info.className = 'pub-info';

  const h3 = document.createElement('h3');
  h3.className = 'pub-title';
  h3.textContent = p.title;
  info.appendChild(h3);

  const authors = document.createElement('p');
  authors.className = 'pub-authors';
  authors.innerHTML = boldSelf(p.authors);
  info.appendChild(authors);

  const venue = document.createElement('p');
  venue.className = 'pub-venue';
  venue.textContent = `${p.venue || ''}, ${p.year}`;
  info.appendChild(venue);

  if (p.award) {
    const award = document.createElement('span');
    award.className = 'pub-award';
    award.textContent = p.award;
    info.appendChild(award);
  }

  if (p.links?.length || p.abstract || p.bibtex) {
    const row = document.createElement('p');
    row.className = 'pub-links';

    for (const lk of p.links || []) {
      const a = document.createElement('a');
      a.className = 'badge';
      a.href = lk.url;
      a.textContent = lk.label;
      if (/^https?:/.test(lk.url)) {
        a.target = '_blank';
        a.rel = 'noopener noreferrer';
      }
      row.appendChild(a);
    }

    if (p.abstract) {
      const btn = document.createElement('button');
      btn.className = 'badge';
      btn.textContent = 'Abstract';
      btn.addEventListener('click', () => {
        const body = document.createElement('p');
        body.textContent = p.abstract;
        showDialog('Abstract', body);
      });
      row.appendChild(btn);
    }

    if (p.bibtex) {
      const btn = document.createElement('button');
      btn.className = 'badge';
      btn.textContent = 'BibTeX';
      btn.addEventListener('click', () => {
        const body = document.createElement('pre');
        body.textContent = (p.bibtex || '').replace(/\\n/g, '\n');
        showDialog('BibTeX', body);
      });
      row.appendChild(btn);
    }

    info.appendChild(row);
  }

  art.appendChild(info);
  return art;
}

/* Flat list of selected papers (for the home page). */
async function renderSelectedPublications(rootId) {
  const root = document.getElementById(rootId);
  try {
    const data = await loadPublications();
    const selected = data
      .filter(p => p.tags && p.tags.includes('selected'))
      .sort((a, b) => b.year - a.year);
    const list = document.createElement('div');
    list.className = 'pub-list';
    for (const p of selected) list.appendChild(pubItem(p));
    root.replaceChildren(list);
  } catch (e) {
    root.innerHTML = '<p>Failed to load publications. Please check data/publications.json.</p>';
  }
}

/* Full year-grouped list with filter buttons (for publication.html). */
async function renderAllPublications(rootId, filterSelector, initialFilter = 'all') {
  const root = document.getElementById(rootId);
  let data = [];
  try {
    data = await loadPublications();
  } catch (e) {
    root.innerHTML = '<p>Failed to load publications. Please check data/publications.json.</p>';
    return;
  }

  const byYear = {};
  for (const p of data) (byYear[p.year] ??= []).push(p);
  const years = Object.keys(byYear).map(Number).sort((a, b) => b - a);

  function render(filter = 'all') {
    root.innerHTML = '';
    for (const y of years) {
      const items = byYear[y].filter(p => {
        if (filter === 'all') return true;
        if (filter === 'journal' || filter === 'conference') return p.type === filter;
        return p.tags && p.tags.includes(filter);
      });
      if (items.length === 0) continue;

      const h2 = document.createElement('h2');
      h2.className = 'pub-year';
      h2.textContent = y;
      root.appendChild(h2);

      const list = document.createElement('div');
      list.className = 'pub-list';
      for (const p of items) list.appendChild(pubItem(p));
      root.appendChild(list);
    }
  }

  const filters = document.querySelectorAll(filterSelector);
  filters.forEach(b => {
    b.addEventListener('click', () => {
      filters.forEach(x => x.classList.remove('active'));
      b.classList.add('active');
      render(b.dataset.filter);
    });
  });

  render(initialFilter);
}
