// Tests for the audio player logic (src/static/js/player-core.js).
// Run: ./run_tests.sh   (or: node --test tests/)
const test = require('node:test');
const assert = require('node:assert/strict');
const Core = require('../src/static/js/player-core.js');

const STORIES = [
  { slug: 'a1', title: 'A one', group: 'ancient-mysteries', audio: null },
  { slug: 'a2', title: 'A two', group: 'ancient-mysteries', audio: '/static/audio/a2.mp3' },
  { slug: 'h1', title: 'H one', group: 'interesting-history', audio: null },
  { slug: 'u1', title: 'U one', group: 'unknown-phenomena', audio: null },
  { slug: 'u2', title: 'U two', group: 'unknown-phenomena', audio: null },
];

function memoryStorage(initial) {
  const data = Object.assign({}, initial);
  return {
    data,
    getItem: (k) => (k in data ? data[k] : null),
    setItem: (k, v) => { data[k] = String(v); },
  };
}

function seededRng(seed) {
  let s = seed;
  return () => { s = (s * 1103515245 + 12345) % 2147483648; return s / 2147483648; };
}

test('there are 4 default lists: all stories and one for each group', () => {
  const lists = Core.createLibrary(STORIES, memoryStorage()).lists();
  assert.deepEqual(lists.map((l) => l.id), ['all', 'ancient-mysteries', 'interesting-history', 'unknown-phenomena']);
  assert.deepEqual(lists.map((l) => l.name), ['All Stories', 'Ancient Mysteries', 'Interesting History', 'Unknown Phenomena']);
  assert.ok(lists.every((l) => l.isDefault));
  assert.deepEqual(lists[0].slugs, ['a1', 'a2', 'h1', 'u1', 'u2']);
  assert.deepEqual(lists[1].slugs, ['a1', 'a2']);
  assert.deepEqual(lists[2].slugs, ['h1']);
  assert.deepEqual(lists[3].slugs, ['u1', 'u2']);
});

test('create, rename and delete a playlist; data stays after a reload', () => {
  const storage = memoryStorage();
  const lib = Core.createLibrary(STORIES, storage);
  const id = lib.createList('  Sleep list  ');
  assert.equal(lib.lists().length, 5);
  assert.equal(lib.lists()[4].name, 'Sleep list');
  assert.equal(lib.lists()[4].isDefault, false);
  lib.renameList(id, 'Night');
  lib.addStory(id, 'u1');
  const again = Core.createLibrary(STORIES, storage); // same storage = page reload
  assert.deepEqual(again.lists()[4], { id, name: 'Night', isDefault: false, slugs: ['u1'] });
  again.deleteList(id);
  assert.equal(Core.createLibrary(STORIES, storage).lists().length, 4);
});

test('a playlist name is necessary and is cut at 60 characters', () => {
  const lib = Core.createLibrary(STORIES, memoryStorage());
  assert.throws(() => lib.createList('   '), /name required/);
  const id = lib.createList('x'.repeat(100));
  assert.throws(() => lib.renameList(id, ''), /name required/);
  assert.equal(lib.lists()[4].name.length, 60);
});

test('two playlists get different ids', () => {
  const lib = Core.createLibrary(STORIES, memoryStorage());
  assert.notEqual(lib.createList('One'), lib.createList('One'));
});

test('a default list cannot be changed or deleted', () => {
  const lib = Core.createLibrary(STORIES, memoryStorage());
  for (const id of ['all', 'ancient-mysteries']) {
    assert.throws(() => lib.renameList(id, 'x'), /default list/);
    assert.throws(() => lib.deleteList(id), /default list/);
    assert.throws(() => lib.addStory(id, 'a1'), /default list/);
    assert.throws(() => lib.removeStory(id, 'a1'), /default list/);
  }
});

test('add and remove stories; the same story is in a list one time only', () => {
  const lib = Core.createLibrary(STORIES, memoryStorage());
  const id = lib.createList('Mine');
  assert.equal(lib.addStory(id, 'a1'), true);
  assert.equal(lib.addStory(id, 'a1'), false);
  assert.equal(lib.addStory(id, 'h1'), true);
  assert.deepEqual(lib.lists()[4].slugs, ['a1', 'h1']);
  lib.removeStory(id, 'a1');
  assert.deepEqual(lib.lists()[4].slugs, ['h1']);
  assert.throws(() => lib.addStory(id, 'not-a-story'), /unknown story/);
  assert.throws(() => lib.addStory('no-such-list', 'a1'), /unknown list/);
});

test('order mode plays the list in order and stops at the end', () => {
  const q = Core.createQueue(['a', 'b', 'c'], { mode: 'order' });
  assert.equal(q.current(), 'a');
  assert.equal(q.next(), 'b');
  assert.equal(q.next(), 'c');
  assert.equal(q.next(), null);
  assert.equal(q.current(), 'c');
  assert.equal(q.prev(), 'b');
  assert.equal(q.prev(), 'a');
  assert.equal(q.prev(), 'a');
});

test('order mode can start in the middle of the list', () => {
  const q = Core.createQueue(['a', 'b', 'c'], { mode: 'order', startSlug: 'b' });
  assert.equal(q.current(), 'b');
  assert.equal(q.next(), 'c');
  assert.equal(q.next(), null);
});

test('an empty queue does not break', () => {
  const q = Core.createQueue([], { mode: 'random' });
  assert.equal(q.current(), null);
  assert.equal(q.next(), null);
  assert.equal(q.prev(), null);
});

test('random mode plays each story one time, then stops', () => {
  const slugs = ['s0', 's1', 's2', 's3', 's4', 's5', 's6', 's7', 's8', 's9'];
  const q = Core.createQueue(slugs, { mode: 'random', startSlug: 's4', rng: seededRng(7) });
  const played = [q.current()];
  for (let i = 0; i < 9; i += 1) played.push(q.next());
  assert.equal(played[0], 's4');
  assert.deepEqual([...played].sort(), slugs);
  assert.notDeepEqual(played, slugs);
  assert.equal(q.next(), null);
});

test('change of mode keeps the current story', () => {
  const q = Core.createQueue(['a', 'b', 'c', 'd'], { mode: 'order', startSlug: 'c', rng: seededRng(3) });
  q.setMode('random');
  assert.equal(q.mode, 'random');
  assert.equal(q.current(), 'c');
  const rest = [q.next(), q.next(), q.next()];
  assert.deepEqual([...rest].sort(), ['a', 'b', 'd']);
  q.setMode('order');
  assert.equal(q.current(), rest[2]);
});

test('sleep timer stops at the set time and lowers the volume in the last 10 seconds', () => {
  let now = 1000000;
  const timer = Core.createSleepTimer(() => now);
  assert.equal(timer.remainingMs(), null);
  assert.equal(timer.shouldStop(), false);
  timer.start(30);
  assert.equal(timer.mode, 'time');
  assert.equal(timer.remainingMs(), 30 * 60000);
  assert.equal(timer.volumeFactor(), 1);
  now += 29 * 60000 + 55000;
  assert.equal(timer.shouldStop(), false);
  assert.ok(Math.abs(timer.volumeFactor() - 0.5) < 0.001);
  now += 5000;
  assert.equal(timer.shouldStop(), true);
  assert.equal(timer.volumeFactor(), 0);
  timer.cancel();
  assert.equal(timer.remainingMs(), null);
  assert.equal(timer.shouldStop(), false);
  assert.equal(timer.volumeFactor(), 1);
  assert.equal(timer.mode, 'off');
});

test('sleep timer "end of story" stops when the story ends, one time', () => {
  const timer = Core.createSleepTimer(() => 0);
  assert.equal(timer.storyEnded(), false);
  timer.startEndOfStory();
  assert.equal(timer.mode, 'end');
  assert.equal(timer.shouldStop(), false);
  assert.equal(timer.remainingMs(), null);
  assert.equal(timer.storyEnded(), true);
  assert.equal(timer.storyEnded(), false);
  assert.equal(timer.mode, 'off');
});

test('a timer with a bad number of minutes is refused', () => {
  const timer = Core.createSleepTimer(() => 0);
  for (const bad of [0, -5, NaN, 'abc', null]) assert.throws(() => timer.start(bad), /minutes/);
});

test('speech text is cut into short parts at sentence ends, and no word is lost', () => {
  const paragraphs = [
    'It was very early. A cart driver was walking to work. He saw a shape on the ground near a gate. '
      + 'He thought it was an old sheet of cloth. It was not cloth. It was something much worse than that, and he ran.',
    'Dr. Smith did not agree. He wrote a long report.',
  ];
  const parts = Core.splitForSpeech(paragraphs, 120);
  assert.ok(parts.length >= 3);
  assert.ok(parts.every((p) => p.length <= 120), parts.join(' | '));
  assert.equal(parts.join(' '), paragraphs.join(' '));
  assert.ok(parts.every((p) => /[.!?]$/.test(p)));
  assert.deepEqual(Core.splitForSpeech([], 120), []);
  assert.deepEqual(Core.splitForSpeech(['', '  '], 120), []);
});

test('a sentence longer than the limit stays in one part', () => {
  const long = 'word '.repeat(60).trim() + '.';
  assert.deepEqual(Core.splitForSpeech([long], 100), [long]);
});

test('source choice: MP3 first, then device voice, then none', () => {
  assert.equal(Core.pickSource(STORIES[1], { hasSpeech: true }), 'mp3');
  assert.equal(Core.pickSource(STORIES[1], { hasSpeech: false }), 'mp3');
  assert.equal(Core.pickSource(STORIES[0], { hasSpeech: true }), 'speech');
  assert.equal(Core.pickSource(STORIES[0], { hasSpeech: false }), 'none');
  assert.equal(Core.pickSource(STORIES[1], { hasSpeech: true, mp3Failed: true }), 'speech');
  assert.equal(Core.pickSource(STORIES[1], { hasSpeech: false, mp3Failed: true }), 'none');
});

test('session (what was playing) is saved and loaded', () => {
  const storage = memoryStorage();
  assert.equal(Core.loadSession(storage), null);
  Core.saveSession(storage, { listId: 'all', slug: 'a2', position: 61.5, mode: 'random', part: 3 });
  assert.deepEqual(Core.loadSession(storage), { listId: 'all', slug: 'a2', position: 61.5, mode: 'random', part: 3 });
  Core.clearSession(storage);
  assert.equal(Core.loadSession(storage), null);
});

test('time is shown as m:ss or h:mm:ss', () => {
  assert.equal(Core.formatTime(0), '0:00');
  assert.equal(Core.formatTime(65.9), '1:05');
  assert.equal(Core.formatTime(3725), '1:02:05');
  assert.equal(Core.formatTime(NaN), '0:00');
});

// --- Review Focus: conditions that must not break the player -----------------

test('no storage (private mode): playlists work in memory', () => {
  const lib = Core.createLibrary(STORIES, null);
  const id = lib.createList('Mine');
  lib.addStory(id, 'a1');
  assert.deepEqual(lib.lists()[4].slugs, ['a1']);
  assert.equal(Core.loadSession(null), null);
  assert.doesNotThrow(() => Core.saveSession(null, { listId: 'all', slug: 'a1' }));
});

test('storage that throws (full or blocked): no error reaches the reader', () => {
  const broken = {
    getItem: () => { throw new Error('blocked'); },
    setItem: () => { throw new Error('quota'); },
  };
  const lib = Core.createLibrary(STORIES, broken);
  const id = lib.createList('Mine');
  assert.equal(lib.addStory(id, 'a1'), true);
  assert.equal(lib.lists().length, 5);
  assert.equal(Core.loadSession(broken), null);
  assert.doesNotThrow(() => Core.saveSession(broken, { listId: 'all', slug: 'a1' }));
});

test('a saved playlist with a story that no longer exists: the story is dropped', () => {
  const storage = memoryStorage({
    [Core.STORAGE_KEY]: JSON.stringify({ version: 1, lists: [{ id: 'u1x', name: 'Old', slugs: ['a1', 'gone-slug', 'a1', 'h1'] }] }),
  });
  assert.deepEqual(Core.createLibrary(STORIES, storage).lists()[4].slugs, ['a1', 'h1']);
});

test('saved data with a bad format gives clean defaults', () => {
  const bad = ['{bad json', '[]', '{"lists":5}', 'null', '42', '{"lists":[null,7,{"id":5},{"id":"all","name":"x","slugs":[]}]}',
    '{"lists":[{"id":"ok","name":"Good","slugs":"nope"}]}'];
  for (const value of bad) {
    const storage = memoryStorage({ [Core.STORAGE_KEY]: value, [Core.SESSION_KEY]: value });
    let lists;
    assert.doesNotThrow(() => { lists = Core.createLibrary(STORIES, storage).lists(); }, value);
    assert.ok(lists.length === 4 || (lists.length === 5 && lists[4].id === 'ok' && lists[4].slugs.length === 0), value);
    assert.equal(Core.loadSession(storage), null, value);
  }
});

test('a saved session for a story that no longer exists is ignored by the caller check', () => {
  const storage = memoryStorage({ [Core.SESSION_KEY]: JSON.stringify({ listId: 'all', slug: 'gone', position: 'x' }) });
  const session = Core.loadSession(storage);
  assert.equal(session.slug, 'gone');
  assert.equal(session.position, 0); // bad number becomes 0
  assert.equal(session.mode, 'order');
});
