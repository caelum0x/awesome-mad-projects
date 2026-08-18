// Data-driven project grid. Single source of truth: projects.json (also served
// by the Pages Function at /api/projects). Falls back to an inline JSON island
// so the page renders even when opened directly from disk (file://).
(function () {
  'use strict';

  var LANG_CLASS = {
    Python: 'lang-python',
    Rust:   'lang-rust',
    Go:     'lang-go',
    TypeScript: 'lang-ts',
  };

  function el(tag, attrs, children) {
    var node = document.createElement(tag);
    if (attrs) {
      Object.keys(attrs).forEach(function (k) {
        if (k === 'class') node.className = attrs[k];
        else if (k === 'text') node.textContent = attrs[k];
        else node.setAttribute(k, attrs[k]);
      });
    }
    (children || []).forEach(function (c) { node.appendChild(c); });
    return node;
  }

  // Build a project card with cover image and visible GitHub link
  function cardFor(p) {
    var nodes = [];

    // Cover image (top of card)
    var coverImg = el('img', {
      class: 'card-cover',
      src: 'assets/covers/' + p.slug + '.png',
      alt: p.name + ' cover — ' + p.tagline.substring(0, 60),
      loading: 'lazy',
      width: '700',
      height: '450',
    });
    // Fallback: if the cover image fails to load, hide it gracefully
    coverImg.addEventListener('error', function () {
      this.style.display = 'none';
    });
    nodes.push(coverImg);

    // Card body
    var badge = el('span', {
      class: 'badge ' + (LANG_CLASS[p.language] || ''),
      text: p.language,
    });

    var head = el('div', { class: 'card-head' }, [
      el('h3', { class: 'card-name', text: p.name }),
      badge,
    ]);

    var tagline = el('p', { class: 'card-tagline', text: p.tagline });

    // GitHub link — always visible on the card face
    var ghLink = el('a', {
      class: 'card-github',
      href: p.github_url,
      rel:  'noopener',
      target: '_blank',
      'aria-label': 'View source for ' + p.name + ' on GitHub (opens in new tab)',
    });
    ghLink.innerHTML =
      '<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">' +
        '<path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 ' +
        '11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555' +
        '-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-' +
        '.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 ' +
        '3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 ' +
        '0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315' +
        ' 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 ' +
        '3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 ' +
        '3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 ' +
        '1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0 0 24 ' +
        '12c0-6.63-5.37-12-12-12z"/>' +
      '</svg>' +
      'GitHub ↗';

    var body = el('div', { class: 'card-body' }, [head, tagline, ghLink]);
    nodes.push(body);

    var card = el('article', { class: 'card reveal' }, nodes);

    // Also make the entire card a link (wrapping anchor)
    // We achieve this by using pointer events on the card and propagating from ghLink
    card.setAttribute('data-href', p.github_url);
    card.addEventListener('click', function (e) {
      // Only open if user clicked the card itself, not a child link
      if (e.target === ghLink || ghLink.contains(e.target)) return;
      window.open(p.github_url, '_blank', 'noopener');
    });
    card.style.cursor = 'pointer';

    return card;
  }

  function render(data) {
    var mount = document.getElementById('clusters');
    if (!mount) return;
    mount.innerHTML = '';
    var total = 0;

    data.clusters.forEach(function (cluster) {
      var section = el('section', {
        class: 'cluster reveal',
        'aria-labelledby': 'cl-' + cluster.id,
      });
      section.appendChild(
        el('h3', { class: 'cluster-title', id: 'cl-' + cluster.id, text: cluster.title })
      );
      if (cluster.blurb) {
        section.appendChild(el('p', { class: 'cluster-blurb', text: cluster.blurb }));
      }
      var grid = el('div', { class: 'grid' });
      cluster.projects.forEach(function (p) {
        grid.appendChild(cardFor(p));
        total += 1;
      });
      section.appendChild(grid);
      mount.appendChild(section);
    });

    var counter = document.getElementById('project-count');
    if (counter) counter.textContent = String(total);

    // Trigger scroll-reveal for newly added cards
    if (window.__revealObserver) {
      document.querySelectorAll('.reveal:not(.visible)').forEach(function (el) {
        window.__revealObserver.observe(el);
      });
    }
  }

  function inlineData() {
    var island = document.getElementById('projects-data');
    if (!island) return null;
    try { return JSON.parse(island.textContent); } catch (e) { return null; }
  }

  function boot() {
    fetch('projects.json', { cache: 'no-store' })
      .then(function (r) { if (!r.ok) throw new Error('bad status'); return r.json(); })
      .then(render)
      .catch(function () {
        var data = inlineData();
        if (data) render(data);
      });
  }

  // ── Scroll-reveal via IntersectionObserver ───────────────────────────
  function initReveal() {
    if (!('IntersectionObserver' in window)) {
      // Fallback: show everything immediately
      document.querySelectorAll('.reveal').forEach(function (el) {
        el.classList.add('visible');
      });
      return;
    }

    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.08, rootMargin: '0px 0px -40px 0px' });

    window.__revealObserver = observer;

    document.querySelectorAll('.reveal').forEach(function (el) {
      observer.observe(el);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () { initReveal(); boot(); });
  } else {
    initReveal();
    boot();
  }
}());
