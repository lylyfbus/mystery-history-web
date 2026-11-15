/**
 * Past Mystery audio player: the browser part.
 *
 * - A bar at the bottom of the page (made on the first play).
 * - "Listen" and "+ Add to playlist" buttons on story pages.
 * - The playlist page (/listen).
 *
 * Sound source for a story: the MP3 file if stories.json has one, else the
 * voice of the device (speechSynthesis). All logic that does not need the
 * browser is in player-core.js and has tests.
 */
(function () {
  'use strict';

  var Core = window.PlayerCore;
  if (!Core) return;

  var storage = null;
  try { storage = window.localStorage; } catch (e) { storage = null; }

  var synth = window.speechSynthesis || null;
  var hasSpeech = !!(synth && window.SpeechSynthesisUtterance);
  var GROUP_NAMES = {};
  Core.DEFAULT_LISTS.forEach(function (l) { GROUP_NAMES[l.id] = l.name; });

  var S = {
    stories: null, bySlug: {}, library: null,
    queue: null, listId: 'all', mode: 'order',
    story: null, source: 'none', playing: false,
    parts: [], part: 0, token: 0,
    failed: {}, skipped: 0,
    timer: Core.createSleepTimer(),
    audio: null, bar: null, el: {}, lastSave: 0, tick: null
  };

  // --- small helpers -------------------------------------------------------------

  function h(tag, attrs, children) {
    var node = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (key) {
      var value = attrs[key];
      if (value === null || value === undefined || value === false) return;
      if (key === 'text') node.textContent = value;
      else if (key === 'on') Object.keys(value).forEach(function (ev) { node.addEventListener(ev, value[ev]); });
      else node.setAttribute(key, value === true ? '' : value);
    });
    (children || []).forEach(function (child) { if (child) node.appendChild(child); });
    return node;
  }

  function button(label, className, onClick, text) {
    return h('button', { type: 'button', class: className, 'aria-label': label, title: label, text: text || label, on: { click: onClick } });
  }

  var storiesPromise = null;
  function loadStories() {
    if (!storiesPromise) {
      storiesPromise = fetch('/static/data/stories.json').then(function (r) {
        if (!r.ok) throw new Error('stories.json ' + r.status);
        return r.json();
      }).then(function (stories) {
        S.stories = stories;
        stories.forEach(function (s) { S.bySlug[s.slug] = s; });
        S.library = Core.createLibrary(stories, storage);
        return stories;
      });
      storiesPromise.catch(function () { storiesPromise = null; });
    }
    return storiesPromise;
  }

  function listById(id) {
    var lists = S.library.lists();
    for (var i = 0; i < lists.length; i += 1) if (lists[i].id === id) return lists[i];
    return lists[0];
  }

  function say(message) {
    if (S.el.msg) S.el.msg.textContent = message || '';
  }

  // --- the bar -------------------------------------------------------------------

  function ensureBar() {
    if (S.bar) return;
    var el = S.el;
    el.art = h('img', { class: 'pm-art', alt: '', width: '48', height: '48' });
    el.title = h('a', { class: 'pm-title' });
    el.sub = h('span', { class: 'pm-sub' });
    el.prev = button('Previous story', 'pm-btn pm-prev', function () { step(-1); }, '⏮');
    el.play = button('Play', 'pm-btn pm-play', toggle, '▶');
    el.next = button('Next story', 'pm-btn pm-next', function () { step(1); }, '⏭');
    el.seek = h('input', { type: 'range', class: 'pm-seek', min: '0', max: '0', step: '1', value: '0', 'aria-label': 'Position in the story',
      on: { input: onSeek } });
    el.time = h('span', { class: 'pm-time', text: '' });
    el.mode = button('Random order', 'pm-chip pm-mode', function () { setMode(S.mode === 'random' ? 'order' : 'random'); }, 'Random');
    el.timer = h('select', { class: 'pm-timer', 'aria-label': 'Sleep timer', on: { change: function () { setTimer(el.timer.value); } } }, [
      h('option', { value: '', text: 'Sleep timer: off' }),
      h('option', { value: '15', text: 'Stop in 15 min' }),
      h('option', { value: '30', text: 'Stop in 30 min' }),
      h('option', { value: '45', text: 'Stop in 45 min' }),
      h('option', { value: '60', text: 'Stop in 60 min' }),
      h('option', { value: 'end', text: 'Stop at end of story' })
    ]);
    el.left = h('span', { class: 'pm-left', text: '' });
    el.lists = h('a', { class: 'pm-chip pm-lists-link', href: '/listen', text: 'Playlists' });
    el.close = button('Close the player', 'pm-btn pm-close', closePlayer, '✕');
    el.msg = h('div', { class: 'pm-msg', 'aria-live': 'polite' });

    S.bar = h('div', { id: 'pm-player', role: 'region', 'aria-label': 'Audio player' }, [
      h('div', { class: 'pm-row' }, [
        el.art,
        h('div', { class: 'pm-info' }, [el.title, el.sub]),
        h('div', { class: 'pm-controls' }, [el.prev, el.play, el.next]),
        h('div', { class: 'pm-extra' }, [el.mode, el.timer, el.left, el.lists, el.close])
      ]),
      h('div', { class: 'pm-row pm-row-seek' }, [el.seek, el.time]),
      el.msg
    ]);
    document.body.appendChild(S.bar);
    document.body.classList.add('pm-has-player');

    S.audio = new Audio();
    S.audio.preload = 'metadata';
    S.audio.addEventListener('ended', onStoryEnd);
    S.audio.addEventListener('play', function () { setPlaying(true); });
    S.audio.addEventListener('pause', function () { if (S.source === 'mp3') setPlaying(false); });
    S.audio.addEventListener('error', onAudioError);

    S.tick = window.setInterval(onTick, 500);
    window.addEventListener('pagehide', saveNow);
    setupMediaSession();
  }

  function closePlayer() {
    stopSound();
    Core.clearSession(storage);
    window.clearInterval(S.tick);
    window.removeEventListener('pagehide', saveNow);
    if (S.bar) S.bar.remove();
    document.body.classList.remove('pm-has-player');
    S.bar = null; S.el = {}; S.story = null; S.queue = null; S.audio = null; S.playing = false;
    S.timer.cancel();
    refreshPage();
  }

  function setPlaying(on) {
    S.playing = on;
    if (S.el.play) {
      S.el.play.textContent = on ? '⏸' : '▶';
      S.el.play.setAttribute('aria-label', on ? 'Pause' : 'Play');
      S.el.play.title = on ? 'Pause' : 'Play';
    }
    if (navigator.mediaSession) navigator.mediaSession.playbackState = on ? 'playing' : 'paused';
    refreshPage();
  }

  function renderBar() {
    var el = S.el;
    var story = S.story;
    if (!S.bar || !story) return;
    el.art.src = story.image;
    el.title.textContent = story.title;
    el.title.href = '/posts/' + story.slug;
    var pos = S.queue.position();
    var sourceName = S.source === 'mp3' ? 'Recorded voice' : S.source === 'speech' ? 'Device voice' : 'No audio';
    el.sub.textContent = listById(S.listId).name + ' · ' + (pos.index + 1) + ' of ' + pos.total + ' · ' + sourceName;
    el.mode.setAttribute('aria-pressed', S.mode === 'random' ? 'true' : 'false');
    el.prev.disabled = pos.index === 0;
    el.next.disabled = !S.queue.hasNext();
    if (navigator.mediaSession && window.MediaMetadata) {
      navigator.mediaSession.metadata = new window.MediaMetadata({
        title: story.title, artist: 'Past Mystery', album: listById(S.listId).name,
        artwork: [{ src: story.image, sizes: '1024x1024', type: 'image/webp' }]
      });
    }
  }

  function setupMediaSession() {
    if (!navigator.mediaSession) return;
    var set = function (name, fn) { try { navigator.mediaSession.setActionHandler(name, fn); } catch (e) { /* not supported */ } };
    set('play', function () { if (!S.playing) toggle(); });
    set('pause', function () { if (S.playing) toggle(); });
    set('nexttrack', function () { step(1); });
    set('previoustrack', function () { step(-1); });
  }

  // --- play ----------------------------------------------------------------------

  function stopSound() {
    S.token += 1;
    if (S.audio) { S.audio.pause(); }
    if (hasSpeech) synth.cancel();
  }

  /** Start a list at a story. options: {mode, position, part, autoplay} */
  function play(listId, slug, options) {
    options = options || {};
    return loadStories().then(function () {
      ensureBar();
      var list = listById(listId);
      if (slug && list.slugs.indexOf(slug) < 0) list = listById('all');
      if (!list.slugs.length) { say('This playlist is empty.'); return; }
      if (options.mode) S.mode = options.mode;
      S.listId = list.id;
      S.queue = Core.createQueue(list.slugs, { mode: S.mode, startSlug: slug || null });
      S.skipped = 0;
      loadStory(S.queue.current(), options);
    }).catch(function () {
      ensureBar();
      say('The story list did not load. Check your connection and try again.');
    });
  }

  function loadStory(slug, options) {
    options = options || {};
    var autoplay = options.autoplay !== false;
    stopSound();
    var token = S.token;
    S.story = S.bySlug[slug];
    S.source = Core.pickSource(S.story, { hasSpeech: hasSpeech, mp3Failed: !!S.failed[slug] });
    S.parts = []; S.part = 0;
    setPlaying(false);
    renderBar();
    S.el.seek.value = '0'; S.el.seek.max = '0'; S.el.time.textContent = '';
    say(options.message || '');

    if (S.source === 'mp3') {
      S.audio.src = S.story.audio;
      S.audio.volume = 1;
      var start = options.position || 0;
      if (start > 0) {
        S.audio.addEventListener('loadedmetadata', function once() {
          S.audio.removeEventListener('loadedmetadata', once);
          if (token === S.token && start < S.audio.duration - 2) S.audio.currentTime = start;
        });
      }
      if (autoplay) startAudio();
    } else if (S.source === 'speech') {
      if (!options.message) say('Loading the story…');
      fetch('/posts/' + slug).then(function (r) {
        if (!r.ok) throw new Error('post ' + r.status);
        return r.text();
      }).then(function (page) {
        if (token !== S.token) return;
        var doc = new DOMParser().parseFromString(page, 'text/html');
        var paragraphs = [];
        doc.querySelectorAll('article.post-content > p').forEach(function (p) { paragraphs.push(p.textContent); });
        S.parts = [S.story.title + '.'].concat(Core.splitForSpeech(paragraphs));
        S.part = Math.min(options.part || 0, S.parts.length - 1);
        S.el.seek.max = String(S.parts.length - 1);
        say(options.message || '');
        saveNow();
        if (autoplay) { setPlaying(true); speakPart(); }
      }).catch(function () {
        if (token !== S.token) return;
        skip('This story did not load.');
      });
    } else {
      skip('Audio is not ready for this story on this device.');
    }
    saveNow();
  }

  function startAudio() {
    var promise = S.audio.play();
    if (promise && promise.catch) {
      promise.catch(function (err) {
        // The browser can refuse to start sound without a tap. Then the reader presses Play.
        if (err && err.name === 'NotAllowedError') say('Press play to start.');
      });
    }
  }

  function onAudioError() {
    if (S.source !== 'mp3' || !S.story || !S.audio.getAttribute('src')) return;
    var slug = S.story.slug;
    var wasPlaying = S.playing || !S.audio.paused;
    S.failed[slug] = true;
    if (hasSpeech) {
      loadStory(slug, { autoplay: wasPlaying, message: 'The recorded voice did not load. Using the device voice.' });
    } else {
      skip('The audio for this story did not load.');
    }
  }

  /** Go to the next story because this one cannot play. Stops if no story in the queue can play. */
  function skip(message) {
    S.skipped += 1;
    setPlaying(false);
    if (S.queue && S.queue.hasNext() && S.skipped <= S.queue.position().total) {
      loadStory(S.queue.next(), { message: message + ' Going to the next story.' });
    } else {
      say(message);
    }
  }

  function pickVoice() {
    var voices = synth.getVoices().filter(function (v) { return /^en[-_]/i.test(v.lang) || v.lang === 'en'; });
    var local = voices.filter(function (v) { return v.localService; });
    var pool = local.length ? local : voices;
    return pool.filter(function (v) { return /en[-_]US/i.test(v.lang) && v.default; })[0]
      || pool.filter(function (v) { return /en[-_]US/i.test(v.lang); })[0] || pool[0] || null;
  }

  function speakPart() {
    var token = S.token;
    if (S.part >= S.parts.length) { onStoryEnd(); return; }
    var utterance = new window.SpeechSynthesisUtterance(S.parts[S.part]);
    var voice = pickVoice();
    if (voice) utterance.voice = voice;
    utterance.lang = voice ? voice.lang : 'en-US';
    utterance.rate = 0.95;
    utterance.onend = function () {
      if (token !== S.token || !S.playing) return;
      S.skipped = 0;
      S.part += 1;
      speakPart();
    };
    utterance.onerror = function (ev) {
      if (token !== S.token || ev.error === 'interrupted' || ev.error === 'canceled') return;
      skip('The device voice stopped with an error.');
    };
    S.utterance = utterance; // keep a reference: some browsers drop the events without it
    synth.speak(utterance);
  }

  function toggle() {
    if (!S.story) return;
    if (S.source === 'mp3') {
      if (S.audio.paused) startAudio(); else S.audio.pause();
    } else if (S.source === 'speech') {
      if (S.playing) {
        S.token += 1;
        synth.cancel();
        setPlaying(false);
      } else if (S.parts.length) {
        S.token += 1;
        if (S.part >= S.parts.length) S.part = 0;
        setPlaying(true);
        speakPart();
      }
    }
    say('');
    saveNow();
  }

  function step(direction) {
    if (!S.queue) return;
    var slug = direction > 0 ? S.queue.next() : S.queue.prev();
    S.skipped = 0;
    if (slug) loadStory(slug);
  }

  function onStoryEnd() {
    S.skipped = 0;
    if (S.timer.storyEnded()) {
      finishTimer('Sleep timer: stopped at the end of the story.');
      return;
    }
    var next = S.queue.next();
    if (next) {
      loadStory(next);
    } else {
      stopSound();
      setPlaying(false);
      S.part = 0;
      say('End of the playlist.');
      Core.clearSession(storage);
    }
  }

  function onSeek() {
    var value = Number(S.el.seek.value);
    if (S.source === 'mp3') {
      S.audio.currentTime = value;
    } else if (S.source === 'speech' && S.parts.length) {
      S.part = value;
      if (S.playing) { S.token += 1; synth.cancel(); speakPart(); }
    }
    showTime();
  }

  function setMode(mode) {
    S.mode = mode === 'random' ? 'random' : 'order';
    if (S.queue) S.queue.setMode(S.mode);
    renderBar();
    saveNow();
  }

  // --- sleep timer -----------------------------------------------------------------

  function setTimer(value) {
    if (value === 'end') S.timer.startEndOfStory();
    else if (value) S.timer.start(Number(value));
    else S.timer.cancel();
    if (S.audio) S.audio.volume = 1;
    if (S.el.timer) S.el.timer.value = value ? String(value) : '';
    showTimer();
  }

  function finishTimer(message) {
    stopSound();
    setPlaying(false);
    S.timer.cancel();
    if (S.audio) S.audio.volume = 1;
    if (S.el.timer) S.el.timer.value = '';
    showTimer();
    say(message);
    saveNow();
  }

  function showTimer() {
    if (!S.el.left) return;
    var left = S.timer.remainingMs();
    S.el.left.textContent = left === null ? '' : Core.formatTime(Math.ceil(left / 1000));
  }

  // --- every half second ---------------------------------------------------------

  function showTime() {
    if (!S.story) return;
    if (S.source === 'mp3') {
      var d = S.audio.duration || S.story.duration || 0;
      if (isFinite(d) && d > 0 && document.activeElement !== S.el.seek) {
        S.el.seek.max = String(Math.floor(d));
        S.el.seek.value = String(Math.floor(S.audio.currentTime));
      }
      S.el.time.textContent = Core.formatTime(S.audio.currentTime) + ' / ' + Core.formatTime(d);
    } else if (S.source === 'speech' && S.parts.length) {
      if (document.activeElement !== S.el.seek) S.el.seek.value = String(S.part);
      S.el.time.textContent = 'Part ' + Math.min(S.part + 1, S.parts.length) + ' of ' + S.parts.length;
    }
  }

  function onTick() {
    showTime();
    showTimer();
    if (S.timer.mode === 'time') {
      if (S.audio && S.source === 'mp3') S.audio.volume = S.timer.volumeFactor();
      if (S.timer.shouldStop()) finishTimer('Sleep timer: stopped. Good night.');
    }
    if (S.playing && Date.now() - S.lastSave > 5000) saveNow();
  }

  function saveNow() {
    if (!S.story) return;
    S.lastSave = Date.now();
    Core.saveSession(storage, {
      listId: S.listId, slug: S.story.slug, mode: S.mode,
      position: S.source === 'mp3' && S.audio ? S.audio.currentTime : 0,
      part: S.source === 'speech' ? S.part : 0
    });
  }

  function restoreSession() {
    var session = Core.loadSession(storage);
    if (!session) return;
    loadStories().then(function () {
      if (!S.bySlug[session.slug]) { Core.clearSession(storage); return; }
      S.mode = session.mode;
      play(session.listId, session.slug, { position: session.position, part: session.part, autoplay: false,
        message: 'Press play to continue.' });
    }).catch(function () { /* no list: no bar */ });
  }

  // --- "add to playlist" menu ------------------------------------------------------

  var openMenu = null;
  function closeMenu() {
    if (openMenu) { openMenu.menu.remove(); openMenu.anchor.setAttribute('aria-expanded', 'false'); openMenu = null; }
  }
  document.addEventListener('click', function (ev) {
    if (openMenu && !openMenu.menu.contains(ev.target) && ev.target !== openMenu.anchor) closeMenu();
  });
  document.addEventListener('keydown', function (ev) {
    if (ev.key === 'Escape' && openMenu) { var a = openMenu.anchor; closeMenu(); a.focus(); }
  });

  function askName(question, current) {
    var name = window.prompt(question, current || '');
    return name === null ? null : name.trim();
  }

  function newPlaylist(thenAddSlug) {
    var name = askName('Name of the new playlist:');
    if (!name) return null;
    var id = S.library.createList(name);
    if (thenAddSlug) S.library.addStory(id, thenAddSlug);
    refreshPage();
    return id;
  }

  function showAddMenu(anchor, slug) {
    if (openMenu && openMenu.anchor === anchor) { closeMenu(); return; }
    closeMenu();
    loadStories().then(function () {
      var menu = h('div', { class: 'pm-menu', role: 'menu', 'aria-label': 'Add to playlist' });
      var mine = S.library.lists().filter(function (l) { return !l.isDefault; });
      if (!mine.length) menu.appendChild(h('p', { class: 'pm-menu-note', text: 'You have no playlists yet.' }));
      mine.forEach(function (list) {
        var has = list.slugs.indexOf(slug) >= 0;
        menu.appendChild(h('button', { type: 'button', role: 'menuitemcheckbox', 'aria-checked': has ? 'true' : 'false',
          text: (has ? '✓ ' : '+ ') + list.name,
          on: { click: function () {
            if (has) S.library.removeStory(list.id, slug); else S.library.addStory(list.id, slug);
            closeMenu();
            flash(anchor, has ? 'Removed' : 'Added');
            refreshPage();
          } } }));
      });
      menu.appendChild(h('button', { type: 'button', role: 'menuitem', class: 'pm-menu-new', text: 'New playlist…',
        on: { click: function () { closeMenu(); if (newPlaylist(slug)) flash(anchor, 'Added'); } } }));
      anchor.insertAdjacentElement('afterend', menu);
      anchor.setAttribute('aria-expanded', 'true');
      openMenu = { menu: menu, anchor: anchor };
      menu.querySelector('button').focus();
    }).catch(function () { flash(anchor, 'Not available'); });
  }

  function flash(buttonEl, text) {
    var old = buttonEl.getAttribute('data-label') || buttonEl.textContent;
    buttonEl.setAttribute('data-label', old);
    buttonEl.textContent = text;
    window.setTimeout(function () { buttonEl.textContent = old; }, 1400);
  }

  // --- story page: Listen / Add buttons --------------------------------------------

  function bindStoryRows(rootEl) {
    (rootEl || document).querySelectorAll('.listen-row').forEach(function (row) {
      if (row.getAttribute('data-bound')) return;
      row.setAttribute('data-bound', '1');
      var slug = row.getAttribute('data-slug');
      var listen = row.querySelector('.listen-btn');
      var add = row.querySelector('.listen-add');
      if (listen) listen.addEventListener('click', function () {
        if (S.story && S.story.slug === slug) toggle();
        else play(row.getAttribute('data-list') || 'all', slug);
      });
      if (add) {
        add.setAttribute('aria-haspopup', 'true');
        add.setAttribute('aria-expanded', 'false');
        add.addEventListener('click', function () { showAddMenu(add, slug); });
      }
    });
  }

  function refreshStoryRows() {
    document.querySelectorAll('.listen-row').forEach(function (row) {
      var listen = row.querySelector('.listen-btn');
      if (!listen) return;
      var active = S.story && S.story.slug === row.getAttribute('data-slug');
      var on = active && S.playing;
      listen.textContent = on ? '⏸ Pause' : (row.classList.contains('pm-story') ? '▶ Play' : '▶ Listen');
      row.classList.toggle('pm-active', !!active);
    });
  }

  // --- playlist page (/listen) -------------------------------------------------------

  var page = { lists: null, stories: null, selected: 'all' };

  function renderListenPage() {
    if (!page.lists) return;
    var lists = S.library.lists();
    if (!lists.some(function (l) { return l.id === page.selected; })) page.selected = 'all';
    try { if (storage) storage.setItem('pm.listen.list', page.selected); } catch (e) { /* ignore */ }

    page.lists.textContent = '';
    lists.forEach(function (list) {
      var item = h('li', { class: 'pm-list' + (list.id === page.selected ? ' pm-selected' : '') }, [
        h('button', { type: 'button', class: 'pm-list-name', 'aria-current': list.id === page.selected ? 'true' : null,
          on: { click: function () { page.selected = list.id; renderListenPage(); } } },
        [h('span', { text: list.name }), h('span', { class: 'pm-count', text: String(list.slugs.length) })])
      ]);
      if (!list.isDefault) {
        item.appendChild(button('Rename playlist ' + list.name, 'pm-small', function () {
          var name = askName('New name for the playlist:', list.name);
          if (name) { S.library.renameList(list.id, name); refreshPage(); }
        }, 'Rename'));
        item.appendChild(button('Delete playlist ' + list.name, 'pm-small pm-danger', function () {
          if (window.confirm('Delete the playlist "' + list.name + '"? The stories stay on the site.')) {
            S.library.deleteList(list.id);
            refreshPage();
          }
        }, 'Delete'));
      }
      page.lists.appendChild(item);
    });
    page.lists.appendChild(h('li', { class: 'pm-list' }, [button('New playlist', 'pm-new', function () {
      var id = newPlaylist(null);
      if (id) { page.selected = id; renderListenPage(); }
    }, '+ New playlist')]));

    var list = listById(page.selected);
    page.stories.textContent = '';
    page.stories.appendChild(h('div', { class: 'pm-stories-head' }, [
      h('h2', { class: 'pm-stories-title', text: list.name }),
      h('p', { class: 'pm-stories-note', text: list.slugs.length + (list.slugs.length === 1 ? ' story' : ' stories') }),
      h('div', { class: 'pm-stories-actions' }, [
        h('button', { type: 'button', class: 'pm-primary', disabled: !list.slugs.length, text: '▶ Play all',
          on: { click: function () { play(list.id, null, { mode: 'order' }); } } }),
        h('button', { type: 'button', class: 'pm-secondary', disabled: !list.slugs.length, text: 'Play random',
          on: { click: function () { play(list.id, null, { mode: 'random' }); } } })
      ])
    ]));
    if (!list.slugs.length) {
      page.stories.appendChild(h('p', { class: 'pm-empty',
        text: 'This playlist is empty. Select "All Stories", then press + on a story to add it here.' }));
    }
    var rows = h('ol', { class: 'pm-story-list' });
    list.slugs.forEach(function (slug) {
      var story = S.bySlug[slug];
      var row = h('li', { class: 'listen-row pm-story', 'data-slug': slug, 'data-list': list.id }, [
        h('img', { src: story.image, alt: '', loading: 'lazy', width: '72', height: '72' }),
        h('div', { class: 'pm-story-text' }, [
          h('a', { href: '/posts/' + slug, text: story.title }),
          h('span', { class: 'pm-story-meta', text: GROUP_NAMES[story.group] + ' · '
            + (story.audio ? 'Recorded voice, ' + Core.formatTime(story.duration) : 'Device voice') })
        ]),
        h('div', { class: 'pm-story-actions' }, [
          h('button', { type: 'button', class: 'listen-btn', 'aria-label': 'Play ' + story.title, text: '▶ Play' }),
          h('button', { type: 'button', class: 'listen-add', 'aria-label': 'Add ' + story.title + ' to a playlist', text: '+' }),
          list.isDefault ? null : button('Remove ' + story.title + ' from this playlist', 'pm-small pm-danger', function () {
            S.library.removeStory(list.id, slug);
            refreshPage();
          }, 'Remove')
        ])
      ]);
      rows.appendChild(row);
    });
    page.stories.appendChild(rows);
    bindStoryRows(page.stories);
    refreshStoryRows();
  }

  function refreshPage() {
    if (page.lists && S.library) renderListenPage();
    else refreshStoryRows();
  }

  // --- start ----------------------------------------------------------------------

  function start() {
    bindStoryRows(document);
    page.lists = document.getElementById('pm-lists');
    page.stories = document.getElementById('pm-stories');
    if (page.lists && page.stories) {
      try { page.selected = (storage && storage.getItem('pm.listen.list')) || 'all'; } catch (e) { page.selected = 'all'; }
      loadStories().then(renderListenPage).catch(function () {
        page.stories.textContent = 'The story list did not load. Check your connection and load the page again.';
      });
    } else {
      page.lists = null;
    }
    restoreSession();
  }

  window.PastPlayer = {
    play: play, toggle: toggle,
    next: function () { step(1); }, prev: function () { step(-1); },
    setMode: setMode, setTimer: setTimer, close: closePlayer,
    state: function () {
      return { slug: S.story && S.story.slug, listId: S.listId, mode: S.mode, source: S.source, playing: S.playing,
        part: S.part, parts: S.parts.length, timer: S.timer.mode };
    }
  };

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();
}());
