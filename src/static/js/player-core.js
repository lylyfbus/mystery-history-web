/**
 * Past Mystery audio player: logic only.
 *
 * This file does not touch the page, the <audio> element, or the speech engine.
 * Thus Node can test it (tests/player.test.js). The browser part is player-ui.js.
 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.PlayerCore = factory();
}(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  var STORAGE_KEY = 'pm.player.v1';
  var SESSION_KEY = 'pm.player.v1.session';
  var MAX_NAME = 60;
  var FADE_MS = 10000;

  var DEFAULT_LISTS = [
    { id: 'all', name: 'All Stories' },
    { id: 'ancient-mysteries', name: 'Ancient Mysteries' },
    { id: 'interesting-history', name: 'Interesting History' },
    { id: 'unknown-phenomena', name: 'Unknown Phenomena' }
  ];

  // --- storage that never throws -------------------------------------------

  function readJson(storage, key) {
    try {
      if (!storage) return null;
      var raw = storage.getItem(key);
      return raw ? JSON.parse(raw) : null;
    } catch (e) {
      return null;
    }
  }

  function writeJson(storage, key, value) {
    try {
      if (storage) storage.setItem(key, JSON.stringify(value));
    } catch (e) { /* private mode or full storage: keep the data in memory only */ }
  }

  // --- playlists -------------------------------------------------------------

  function isDefaultId(id) {
    return DEFAULT_LISTS.some(function (l) { return l.id === id; });
  }

  function cleanName(name) {
    var text = String(name == null ? '' : name).replace(/\s+/g, ' ').trim().slice(0, MAX_NAME);
    if (!text) throw new Error('name required');
    return text;
  }

  function createLibrary(stories, storage) {
    var known = {};
    stories.forEach(function (s) { known[s.slug] = true; });

    function loadUserLists() {
      var saved = readJson(storage, STORAGE_KEY);
      if (!saved || typeof saved !== 'object' || !Array.isArray(saved.lists)) return [];
      var seen = {};
      return saved.lists.filter(function (l) {
        if (!l || typeof l.id !== 'string' || typeof l.name !== 'string') return false;
        if (isDefaultId(l.id) || seen[l.id] || !l.name.trim()) return false;
        seen[l.id] = true;
        return true;
      }).map(function (l) {
        var inList = {};
        var slugs = (Array.isArray(l.slugs) ? l.slugs : []).filter(function (slug) {
          if (typeof slug !== 'string' || !known[slug] || inList[slug]) return false;
          inList[slug] = true;
          return true;
        });
        return { id: l.id, name: l.name.trim().slice(0, MAX_NAME), slugs: slugs };
      });
    }

    var userLists = loadUserLists();

    function save() {
      writeJson(storage, STORAGE_KEY, { version: 1, lists: userLists });
    }

    function find(id) {
      if (isDefaultId(id)) throw new Error('default list');
      for (var i = 0; i < userLists.length; i += 1) if (userLists[i].id === id) return userLists[i];
      throw new Error('unknown list');
    }

    function newId() {
      var id;
      do {
        id = 'u' + Date.now().toString(36) + Math.floor(Math.random() * 1e6).toString(36);
      } while (userLists.some(function (l) { return l.id === id; }));
      return id;
    }

    return {
      lists: function () {
        var defaults = DEFAULT_LISTS.map(function (d) {
          var inGroup = stories.filter(function (s) { return d.id === 'all' || s.group === d.id; });
          return { id: d.id, name: d.name, isDefault: true, slugs: inGroup.map(function (s) { return s.slug; }) };
        });
        return defaults.concat(userLists.map(function (l) {
          return { id: l.id, name: l.name, isDefault: false, slugs: l.slugs.slice() };
        }));
      },
      createList: function (name) {
        var list = { id: newId(), name: cleanName(name), slugs: [] };
        userLists.push(list);
        save();
        return list.id;
      },
      renameList: function (id, name) {
        var list = find(id);
        list.name = cleanName(name);
        save();
      },
      deleteList: function (id) {
        var list = find(id);
        userLists.splice(userLists.indexOf(list), 1);
        save();
      },
      addStory: function (id, slug) {
        var list = find(id);
        if (!known[slug]) throw new Error('unknown story');
        if (list.slugs.indexOf(slug) >= 0) return false;
        list.slugs.push(slug);
        save();
        return true;
      },
      removeStory: function (id, slug) {
        var list = find(id);
        var at = list.slugs.indexOf(slug);
        if (at >= 0) {
          list.slugs.splice(at, 1);
          save();
        }
      }
    };
  }

  // --- queue: what plays next ----------------------------------------------------

  function shuffle(items, rng) {
    var a = items.slice();
    for (var i = a.length - 1; i > 0; i -= 1) {
      var j = Math.floor(rng() * (i + 1));
      var t = a[i]; a[i] = a[j]; a[j] = t;
    }
    return a;
  }

  function createQueue(slugs, options) {
    options = options || {};
    var rng = options.rng || Math.random;
    var original = slugs.slice();
    var order = [];
    var index = 0;
    var queue = {
      mode: 'order',
      current: function () { return order.length ? order[index] : null; },
      next: function () {
        if (index >= order.length - 1) return null;
        index += 1;
        return order[index];
      },
      prev: function () {
        if (!order.length) return null;
        if (index > 0) index -= 1;
        return order[index];
      },
      hasNext: function () { return index < order.length - 1; },
      position: function () { return { index: index, total: order.length }; },
      setMode: function (mode) { arrange(mode, queue.current()); }
    };

    // Random: the current story is first, and each other story comes one time after it.
    function arrange(mode, currentSlug) {
      queue.mode = mode === 'random' ? 'random' : 'order';
      var at = original.indexOf(currentSlug);
      if (queue.mode === 'random') {
        var rest = original.filter(function (s, i) { return i !== at; });
        order = (at >= 0 ? [original[at]] : []).concat(shuffle(rest, rng));
        index = 0;
      } else {
        order = original.slice();
        index = at >= 0 ? at : 0;
      }
    }

    arrange(options.mode, options.startSlug);
    return queue;
  }

  // --- sleep timer -------------------------------------------------------------

  function createSleepTimer(now) {
    now = now || Date.now;
    var endAt = null;
    var atStoryEnd = false;
    var timer = {
      mode: 'off',
      start: function (minutes) {
        var m = Number(minutes);
        if (minutes === null || minutes === '' || !isFinite(m) || m <= 0) throw new Error('minutes must be more than 0');
        endAt = now() + m * 60000;
        atStoryEnd = false;
        timer.mode = 'time';
      },
      startEndOfStory: function () {
        endAt = null;
        atStoryEnd = true;
        timer.mode = 'end';
      },
      cancel: function () {
        endAt = null;
        atStoryEnd = false;
        timer.mode = 'off';
      },
      remainingMs: function () {
        return endAt === null ? null : Math.max(0, endAt - now());
      },
      volumeFactor: function () {
        var left = timer.remainingMs();
        return left === null || left >= FADE_MS ? 1 : left / FADE_MS;
      },
      shouldStop: function () {
        return endAt !== null && now() >= endAt;
      },
      // Call this when a story ends. True means: stop now, do not play the next story.
      storyEnded: function () {
        if (!atStoryEnd) return false;
        timer.cancel();
        return true;
      }
    };
    return timer;
  }

  // --- text for the device voice ---------------------------------------------------

  // Browsers stop long speech after some seconds. Thus we speak in short parts.
  function splitForSpeech(paragraphs, maxChars) {
    maxChars = maxChars || 220;
    var parts = [];
    (paragraphs || []).forEach(function (paragraph) {
      var text = String(paragraph || '').replace(/\s+/g, ' ').trim();
      if (!text) return;
      var sentences = text.match(/[^.!?]+(?:[.!?]+["'”’)]*|$)/g) || [text];
      var buffer = '';
      sentences.forEach(function (sentence) {
        var s = sentence.trim();
        if (!s) return;
        // "Dr." and "Mr." do not end a sentence: join them to the next piece.
        var joined = buffer ? buffer + ' ' + s : s;
        if (buffer && joined.length > maxChars && !/\b(?:Mr|Mrs|Ms|Dr|St|Sr|Jr|No|vs|[A-Z])\.$/.test(buffer)) {
          parts.push(buffer);
          buffer = s;
        } else {
          buffer = joined;
        }
      });
      if (buffer) parts.push(buffer);
    });
    return parts;
  }

  // Blocks are the titles and paragraphs of a story, in page order: [{title: true|false, text}].
  // A section title is spoken as its own part, so the voice pauses before and after it.
  function partsForSpeech(blocks, maxChars) {
    var parts = [];
    (blocks || []).forEach(function (block) {
      var text = String((block && block.text) || '').replace(/\s+/g, ' ').trim();
      if (!text) return;
      if (block.title) parts.push(/[.!?]["'”’)]*$/.test(text) ? text : text + '.');
      else parts = parts.concat(splitForSpeech([text], maxChars));
    });
    return parts;
  }

  function pickSource(story, env) {
    env = env || {};
    if (story && story.audio && !env.mp3Failed) return 'mp3';
    return env.hasSpeech ? 'speech' : 'none';
  }

  // --- what was playing (to offer "Continue" after a page change) -------------------

  function saveSession(storage, session) {
    writeJson(storage, SESSION_KEY, session);
  }

  function loadSession(storage) {
    var s = readJson(storage, SESSION_KEY);
    if (!s || typeof s !== 'object' || Array.isArray(s) || typeof s.slug !== 'string' || !s.slug) return null;
    var out = {
      listId: typeof s.listId === 'string' ? s.listId : 'all',
      slug: s.slug,
      position: typeof s.position === 'number' && isFinite(s.position) && s.position > 0 ? s.position : 0,
      mode: s.mode === 'random' ? 'random' : 'order'
    };
    if (typeof s.part === 'number' && isFinite(s.part) && s.part > 0) out.part = Math.floor(s.part);
    return out;
  }

  function clearSession(storage) {
    try {
      if (storage && storage.removeItem) storage.removeItem(SESSION_KEY);
      else if (storage) storage.setItem(SESSION_KEY, '');
    } catch (e) { /* nothing to do */ }
  }

  function formatTime(seconds) {
    var s = isFinite(seconds) && seconds > 0 ? Math.floor(seconds) : 0;
    var h = Math.floor(s / 3600);
    var m = Math.floor((s % 3600) / 60);
    var sec = s % 60;
    var two = function (n) { return (n < 10 ? '0' : '') + n; };
    return h ? h + ':' + two(m) + ':' + two(sec) : m + ':' + two(sec);
  }

  return {
    STORAGE_KEY: STORAGE_KEY,
    SESSION_KEY: SESSION_KEY,
    DEFAULT_LISTS: DEFAULT_LISTS,
    createLibrary: createLibrary,
    createQueue: createQueue,
    createSleepTimer: createSleepTimer,
    splitForSpeech: splitForSpeech,
    partsForSpeech: partsForSpeech,
    pickSource: pickSource,
    saveSession: saveSession,
    loadSession: loadSession,
    clearSession: clearSession,
    formatTime: formatTime
  };
}));
