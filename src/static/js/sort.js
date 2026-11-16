/**
 * Past Mystery: sort control for the story lists (All Stories and the 3 group pages).
 *
 * The first part is logic only, thus Node can test it (tests/sort.test.js).
 * The second part runs only in a browser. Without this file, the lists keep
 * their order from the HTML: added time, newest first.
 */
(function (root, factory) {
  var api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.StorySort = api;
  if (typeof document !== 'undefined') api.start(document, root);
}(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  var STORAGE_KEY = 'pm.sort.v1';
  var DEFAULT = { type: 'added', dir: 'desc' };
  var TYPES = {
    added: { name: 'Added time', desc: 'Newest first', asc: 'Oldest first' },
    year: { name: 'Story time', desc: 'Latest first', asc: 'Earliest first' },
    views: { name: 'Number of views', desc: 'Most views first', asc: 'Fewest views first' }
  };
  var MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August',
    'September', 'October', 'November', 'December'];

  function isNumber(v) { return typeof v === 'number' && isFinite(v); }

  function value(story, type) {
    if (type === 'added') {
      var t = Date.parse(story.added);
      return isNaN(t) ? null : t;
    }
    var v = story[type];
    return isNumber(v) ? v : null;
  }

  /** Returns a new list. Equal values keep the input order. No value = last, in both directions. */
  function sortStories(stories, type, dir) {
    if (!TYPES[type]) { type = DEFAULT.type; dir = DEFAULT.dir; }
    var sign = dir === 'asc' ? 1 : -1;
    return stories
      .map(function (story, index) { return { story: story, index: index, v: value(story, type) }; })
      .sort(function (a, b) {
        if (a.v === null || b.v === null) {
          if (a.v === b.v) return a.index - b.index;
          return a.v === null ? 1 : -1;
        }
        return a.v === b.v ? a.index - b.index : sign * (a.v - b.v);
      })
      .map(function (item) { return item.story; });
  }

  function hasViews(stories) {
    return stories.some(function (s) { return isNumber(s.views); });
  }

  function metaText(story, type) {
    if (type === 'year') return story.when || '';
    if (type === 'views') {
      if (!isNumber(story.views)) return '';
      return story.views.toLocaleString('en-US') + (story.views === 1 ? ' view' : ' views');
    }
    var m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(story.added || '');
    return m ? 'Added ' + MONTHS[Number(m[2]) - 1] + ' ' + Number(m[3]) + ', ' + m[1] : '';
  }

  function readChoice(text) {
    try {
      var c = JSON.parse(text);
      if (c && TYPES[c.type] && (c.dir === 'asc' || c.dir === 'desc')) return { type: c.type, dir: c.dir };
    } catch (e) { /* use the default */ }
    return { type: DEFAULT.type, dir: DEFAULT.dir };
  }

  // ---- browser part ----

  function start(doc, win) {
    function run() {
      var lists = doc.querySelectorAll('.archive-grid, .categories-section');
      if (!lists.length || !win.fetch) return;
      win.fetch('/static/data/stories.json')
        .then(function (r) { return r.json(); })
        .then(function (stories) { build(doc, win, lists, stories); })
        .catch(function () { /* the lists keep the order from the HTML */ });
    }
    if (doc.readyState === 'loading') doc.addEventListener('DOMContentLoaded', run);
    else run();
  }

  function build(doc, win, lists, stories) {
    var saved = null;
    try { saved = win.localStorage.getItem(STORAGE_KEY); } catch (e) { /* no storage */ }
    var choice = readChoice(saved);
    var views = hasViews(stories);
    if (choice.type === 'views' && !views) choice = { type: DEFAULT.type, dir: DEFAULT.dir };

    var bar = doc.createElement('div');
    bar.className = 'sort-bar';
    var typeSelect = select(doc, 'Sort by', 'sort-type');
    var dirSelect = select(doc, 'Order', 'sort-dir');
    Object.keys(TYPES).forEach(function (key) {
      var option = new win.Option(TYPES[key].name + (key === 'views' && !views ? ' (no numbers yet)' : ''), key);
      option.disabled = key === 'views' && !views;
      typeSelect.control.add(option);
    });
    bar.appendChild(typeSelect.label);
    bar.appendChild(dirSelect.label);
    // Put the control under the page title (group page) or above the first list (All Stories).
    var first = lists[0];
    var heading = first.querySelector('.section-title');
    var before = first.previousElementSibling;
    if (heading) heading.insertAdjacentElement('afterend', bar);
    else first.parentNode.insertBefore(bar, before && /archive-cat-title/.test(before.className) ? before : first);

    function fillDirections() {
      var t = TYPES[choice.type];
      dirSelect.control.innerHTML = '';
      dirSelect.control.add(new win.Option(t.desc + ' (descending)', 'desc'));
      dirSelect.control.add(new win.Option(t.asc + ' (ascending)', 'asc'));
      dirSelect.control.value = choice.dir;
    }

    function apply() {
      var rank = {};
      var bySlug = {};
      sortStories(stories, choice.type, choice.dir).forEach(function (s, i) { rank[s.slug] = i; bySlug[s.slug] = s; });
      Array.prototype.forEach.call(lists, function (list) {
        var cards = Array.prototype.slice.call(list.querySelectorAll('a.archive-card, a.category-bar'));
        cards
          .map(function (card) { return { card: card, slug: (card.getAttribute('href') || '').split('/').pop() }; })
          .sort(function (a, b) { return (rank[a.slug] === undefined ? 1e9 : rank[a.slug]) - (rank[b.slug] === undefined ? 1e9 : rank[b.slug]); })
          .forEach(function (item) {
            list.appendChild(item.card);
            var story = bySlug[item.slug];
            var meta = item.card.querySelector('.sort-meta');
            var text = story ? metaText(story, choice.type) : '';
            if (!meta && text) {
              meta = doc.createElement('p');
              meta.className = 'sort-meta';
              var title = item.card.querySelector('.card-title, .category-bar-title');
              if (title) title.insertAdjacentElement('afterend', meta);
            }
            if (meta) meta.textContent = text;
          });
      });
      try { win.localStorage.setItem(STORAGE_KEY, JSON.stringify(choice)); } catch (e) { /* no storage */ }
    }

    typeSelect.control.value = choice.type;
    fillDirections();
    typeSelect.control.addEventListener('change', function () {
      choice = { type: typeSelect.control.value, dir: 'desc' };
      fillDirections();
      apply();
    });
    dirSelect.control.addEventListener('change', function () {
      choice.dir = dirSelect.control.value;
      apply();
    });
    apply();
  }

  function select(doc, text, id) {
    var label = doc.createElement('label');
    label.className = 'sort-field';
    label.setAttribute('for', id);
    var span = doc.createElement('span');
    span.textContent = text;
    var control = doc.createElement('select');
    control.id = id;
    label.appendChild(span);
    label.appendChild(control);
    return { label: label, control: control };
  }

  return {
    DEFAULT: DEFAULT, TYPES: TYPES, sortStories: sortStories, hasViews: hasViews,
    metaText: metaText, readChoice: readChoice, start: start
  };
}));
