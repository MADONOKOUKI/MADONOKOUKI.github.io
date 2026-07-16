/* Publication list renderer (single-page site, ren-jing.com-inspired layout).
   Data lives in data/publications.json — edit that file to add papers.
   - Papers tagged "selected" render with a teaser image (data "thumb" field).
   - Everything else renders as a compact text entry, grouped by year.
   - Link labels get icons automatically: Paper/PDF → document, Code → brackets,
     Patent → medal, Project/Page → globe, Video → camera, Demo → laptop,
     Dataset/Data → database. */

const PUB_ICONS = {
  doc: '<svg viewBox="0 0 14 14" aria-hidden="true"><path d="M3 1.5h5L11.5 5v7.5h-8.5z"/><path d="M8 1.5V5h3.5"/></svg>',
  code: '<svg viewBox="0 0 14 14" aria-hidden="true"><path d="M5 3.5 1.8 7 5 10.5M9 3.5 12.2 7 9 10.5"/></svg>',
  award: '<svg viewBox="0 0 14 14" aria-hidden="true"><circle cx="7" cy="5.5" r="3.2"/><path d="M5 8.2 4 12.5l3-1.6 3 1.6-1-4.3"/></svg>',
  lines: '<svg viewBox="0 0 14 14" aria-hidden="true"><path d="M2.5 3.5h9M2.5 7h9M2.5 10.5h6"/></svg>',
  braces: '<svg viewBox="0 0 14 14" aria-hidden="true"><path d="M5.5 2.5c-2 0-2 2-2 3s0 1.5-1.2 1.5c1.2 0 1.2.5 1.2 1.5s0 3 2 3M8.5 2.5c2 0 2 2 2 3s0 1.5 1.2 1.5c-1.2 0-1.2.5-1.2 1.5s0 3-2 3"/></svg>',
  globe: '<svg viewBox="0 0 14 14" aria-hidden="true"><circle cx="7" cy="7" r="5.5"/><path d="M1.5 7h11M7 1.5c1.8 2.5 1.8 8.5 0 11M7 1.5c-1.8 2.5-1.8 8.5 0 11"/></svg>',
  video: '<svg viewBox="0 0 14 14" aria-hidden="true"><rect x="1.5" y="3.5" width="8" height="7" rx="1.5"/><path d="M9.5 6.3 12.5 4.5v5L9.5 7.7"/></svg>',
  laptop: '<svg viewBox="0 0 14 14" aria-hidden="true"><path d="M2.5 3.5h9v6h-9z"/><path d="M1 11h12"/></svg>',
  db: '<svg viewBox="0 0 14 14" aria-hidden="true"><ellipse cx="7" cy="3.2" rx="5" ry="1.7"/><path d="M2 3.2v7.6c0 .95 2.2 1.7 5 1.7s5-.75 5-1.7V3.2"/><path d="M2 7c0 .95 2.2 1.7 5 1.7S12 7.95 12 7"/></svg>',
};

function pubIconFor(label) {
  const l = label.toLowerCase();
  if (l.includes('code')) return PUB_ICONS.code;
  if (l.includes('patent')) return PUB_ICONS.award;
  if (l.includes('project') || l.includes('page')) return PUB_ICONS.globe;
  if (l.includes('video')) return PUB_ICONS.video;
  if (l.includes('demo')) return PUB_ICONS.laptop;
  if (l.includes('data')) return PUB_ICONS.db;
  return PUB_ICONS.doc;
}

async function loadPublications() {
  const res = await fetch('data/publications.json', { cache: 'no-store' });
  if (!res.ok) throw new Error('failed to load publications.json');
  return res.json();
}

function boldSelf(authors) {
  const escaped = (authors || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
  return escaped
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

function pubEntry(p, { withImage = false } = {}) {
  const art = document.createElement('article');
  art.className = 'pub-entry';

  const content = document.createElement('div');
  content.className = 'pub-content';

  const h3 = document.createElement('h3');
  h3.className = 'pub-title';
  h3.textContent = p.title;
  content.appendChild(h3);

  const authors = document.createElement('p');
  authors.className = 'pub-authors';
  authors.innerHTML = boldSelf(p.authors);
  content.appendChild(authors);

  const venue = document.createElement('p');
  venue.className = 'pub-venue';
  venue.textContent = `${p.venue || ''}, ${p.year}`;
  content.appendChild(venue);

  if (p.award) {
    const award = document.createElement('span');
    award.className = 'pub-award';
    award.textContent = p.award;
    content.appendChild(award);
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

    content.appendChild(row);
  }

  art.appendChild(content);

  if (withImage && p.thumb) {
    art.classList.add('featured');
    const media = document.createElement('div');
    media.className = 'pub-media';
    const img = document.createElement('img');
    img.src = p.thumb;
    img.alt = '';
    img.loading = 'lazy';
    media.appendChild(img);
    art.appendChild(media);
  }

  return art;
}

/* Selected papers (teaser images) + the rest as a compact year-grouped text list. */
async function renderPublications(selectedRootId, othersRootId) {
  const selRoot = document.getElementById(selectedRootId);
  const otherRoot = document.getElementById(othersRootId);
  let data = [];
  try {
    data = await loadPublications();
  } catch (e) {
    selRoot.innerHTML = '<p>Failed to load publications. Please check data/publications.json.</p>';
    return;
  }

  const isSelected = p => p.tags && p.tags.includes('selected');

  /* — selected, newest first, with teasers — */
  const selected = data.filter(isSelected).sort((a, b) => b.year - a.year);
  const selList = document.createElement('div');
  selList.className = 'pub-list featured-list';
  for (const p of selected) selList.appendChild(pubEntry(p, { withImage: true }));
  selRoot.replaceChildren(selList);

  /* — everything else, year-grouped, text only — */
  const others = data.filter(p => !isSelected(p));
  const byYear = {};
  for (const p of others) (byYear[p.year] ??= []).push(p);
  const years = Object.keys(byYear).map(Number).sort((a, b) => b - a);

  otherRoot.innerHTML = '';
  if (years.length > 0) {
    const subhead = document.createElement('h3');
    subhead.className = 'pub-subhead';
    subhead.textContent = 'More Publications';
    otherRoot.appendChild(subhead);
  }
  for (const y of years) {
    const h4 = document.createElement('h4');
    h4.className = 'pub-year';
    h4.textContent = y;
    otherRoot.appendChild(h4);

    const list = document.createElement('div');
    list.className = 'pub-list';
    for (const p of byYear[y]) list.appendChild(pubEntry(p));
    otherRoot.appendChild(list);
  }
}
