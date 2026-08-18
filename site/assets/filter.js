// Client-side project grid filter — CSP-safe external script.
// Listens for 'projectsgridready' dispatched by app.js after cards render.
// Reads data-cluster / data-language from each .card element.
// Degrades gracefully: if JS is disabled all cards remain visible.
(function () {
  'use strict';

  var activeCluster = 'all';
  var activeLang    = 'all';
  var initialized   = false;

  function applyFilters() {
    var cards    = document.querySelectorAll('.card[data-cluster]');
    var clusters = document.querySelectorAll('.cluster[data-cluster-id]');

    cards.forEach(function (card) {
      var clMatch  = activeCluster === 'all' || card.dataset.cluster  === activeCluster;
      var langMatch = activeLang  === 'all' || card.dataset.language === activeLang;
      card.hidden = !(clMatch && langMatch);
    });

    // Hide entire cluster section when all its cards are hidden
    clusters.forEach(function (section) {
      var visible = section.querySelectorAll('.card:not([hidden])');
      section.hidden = visible.length === 0;
    });
  }

  function init() {
    if (initialized) return;
    var bar = document.getElementById('filter-bar');
    if (!bar) return;
    if (!document.querySelector('.card[data-cluster]')) return; // cards not rendered yet
    initialized = true;

    var clusterChips = bar.querySelectorAll('[data-filter-cluster]');
    var langChips    = bar.querySelectorAll('[data-filter-lang]');

    clusterChips.forEach(function (chip) {
      chip.addEventListener('click', function () {
        activeCluster = chip.dataset.filterCluster;
        clusterChips.forEach(function (c) {
          var on = c.dataset.filterCluster === activeCluster;
          c.setAttribute('aria-pressed', on ? 'true' : 'false');
          c.classList.toggle('active', on);
        });
        applyFilters();
      });
    });

    langChips.forEach(function (chip) {
      chip.addEventListener('click', function () {
        activeLang = chip.dataset.filterLang;
        langChips.forEach(function (c) {
          var on = c.dataset.filterLang === activeLang;
          c.setAttribute('aria-pressed', on ? 'true' : 'false');
          c.classList.toggle('active', on);
        });
        applyFilters();
      });
    });
  }

  document.addEventListener('projectsgridready', init);
}());
