/* Publication list renderer (single-page site, ren-jing.com-inspired layout).
   Data lives in data/publications.json — edit that file to add papers. */

const PUB_ICONS = {
  doc: '<svg viewBox="0 0 14 14" aria-hidden="true"><path d="M3 1.5h5L11.5 5v7.5h-8.5z"/><path d="M8 1.5V5h3.5"/></svg>',
  code: '<svg viewBox="0 0 14 14" aria-hidden="true"><path d="M5 3.5 1.8 7 5 10.5M9 3.5 12.2 7 9 10.5"/></svg>',
  award: '<svg viewBox="0 0 14 14" aria-hidden="true"><circle cx="7" cy="5.5" r="3.2"/><path d="M5 8.2 4 12.5l3-1.6 3 1.6-1-4.3"/></svg>',
  lines: '<svg viewBox="0 0 14 14" aria-hidden="true"><path d="M2.5 3.5h9M2.5 7h9M2.5 10.5h6"/></svg>',
  braces: '<svg viewBox="0 0 14 14" aria-hidden="true"><path d="M5.5 2.5c-2 0-2 2-2 3s0 1.5-1.2 1.5c1.2 0 1.2.5 1.2 1.5s0 3 2 3M8.5 2.5c2 0 2 2 2 3s0 1.5 1.2 1.5c-1.2 0-1.2.5-1.2 1.5s0 3-2 3"/></svg>',
};

function pubIconFor(label) {
  const l = label.toLowerCase();
  if (l.includes('code')) return PUB_ICONS.code;
  if (l.includes('patent')) return PUB_ICONS.award;
  return PUB_ICONS.doc;
}

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

function badge(label, icon) {
  const span = document.createElement('span');
  span.innerHTML = icon;
  span.appendChild(document.createTextNode(label));
  return span;
}

function pubEntry(p) {
  const art = document.createElement('article');
  art.className = 'pub-entry';

  const h3 = document.createElement('h3');
  h3.className = 'pub-title';
  h3.textContent = p.title;
  art.appendChild(h3);

  const authors = document.createElement('p');
  authors.className = 'pub-authors';
  authors.innerHTML = boldSelf(p.authors);
  art.appendChild(authors);

  const venue = document.createElement('p');
  venue.className = 'pub-venue';
  venue.textContent = `${p.venue || ''}, ${p.year}`;
  art.appendChild(venue);

  if (p.award) {
    const award = document.createElement('span');
    award.className = 'pub-award';
    award.textContent = p.award;
    art.appendChild(award);
  }

  if (p.links?.length || p.abstract || p.bibtex) {
    const row = document.createElement('p');
    row.className = 'pub-links';

    for (const lk of p.links || []) {
      const a = document.createElement('a');
      a.className = 'badge';
      a.href = lk.url;
      a.innerHTML = pubIconFor(lk.label);
      a.appendChild(document.createTextNode(lk.label));
      if (/^https?:/.test(lk.url)) {
        a.target = '_blank';
        a.rel = 'noopener noreferrer';
      }
      row.appendChild(a);
    }

    if (p.abstract) {
      const btn = document.createElement('button');
      btn.className = 'badge';
      btn.innerHTML = PUB_ICONS.lines;
      btn.appendChild(document.createTextNode('Abstract'));
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
      btn.innerHTML = PUB_ICONS.braces;
      btn.appendChild(document.createTextNode('BibTeX'));
      btn.addEventListener('click', () => {
        const body = document.createElement('pre');
        body.textContent = (p.bibtex || '').replace(/\\n/g, '\n');
        showDialog('BibTeX', body);
      });
      row.appendChild(btn);
    }

    art.appendChild(row);
  }

  return art;
}

/* Year-grouped list with filter buttons. */
async function renderPublications(rootId, filterSelector, initialFilter = 'all') {
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

      const h3 = document.createElement('h3');
      h3.className = 'pub-year';
      h3.textContent = y;
      root.appendChild(h3);

      const list = document.createElement('div');
      list.className = 'pub-list';
      for (const p of items) list.appendChild(pubEntry(p));
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
