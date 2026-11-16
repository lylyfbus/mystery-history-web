// Tests for the sort logic of the story lists (src/static/js/sort.js).
const test = require('node:test');
const assert = require('node:assert/strict');
const Sort = require('../src/static/js/sort.js');

const S = [
  { slug: 'a', added: '2026-04-17', year: 1888, when: '1888', views: 50 },
  { slug: 'b', added: '2026-04-17', year: -360, when: 'about 360 BCE', views: null },
  { slug: 'c', added: '2026-02-20', year: 1977, when: '1977', views: 900 },
  { slug: 'd', added: '2026-03-01', year: 79, when: '79 CE', views: 50 },
];
const order = (type, dir) => Sort.sortStories(S, type, dir).map((s) => s.slug);

test('default is added time, newest first', () => {
  assert.deepEqual(Sort.DEFAULT, { type: 'added', dir: 'desc' });
  assert.deepEqual(order('added', 'desc'), ['a', 'b', 'd', 'c']);
});

test('added time, oldest first', () => {
  assert.deepEqual(order('added', 'asc'), ['c', 'd', 'a', 'b']);
});

test('story time puts years before the year 1 first when ascending', () => {
  assert.deepEqual(order('year', 'asc'), ['b', 'd', 'a', 'c']);
  assert.deepEqual(order('year', 'desc'), ['c', 'a', 'd', 'b']);
});

test('views: a story with no number is last in both directions', () => {
  assert.deepEqual(order('views', 'desc'), ['c', 'a', 'd', 'b']);
  assert.deepEqual(order('views', 'asc'), ['a', 'd', 'c', 'b']);
});

test('equal values keep the order of the input', () => {
  assert.deepEqual(order('views', 'desc').slice(1, 3), ['a', 'd']);
});

test('the input list is not changed, and bad input uses the default', () => {
  const before = S.map((s) => s.slug);
  Sort.sortStories(S, 'year', 'asc');
  assert.deepEqual(S.map((s) => s.slug), before);
  assert.deepEqual(Sort.sortStories(S, 'nonsense', 'sideways').map((s) => s.slug), order('added', 'desc'));
});

test('hasViews is true only when a story has a number', () => {
  assert.equal(Sort.hasViews(S), true);
  assert.equal(Sort.hasViews([{ slug: 'x', views: null }, { slug: 'y' }]), false);
});

test('meta text for a card', () => {
  assert.equal(Sort.metaText(S[1], 'year'), 'about 360 BCE');
  assert.equal(Sort.metaText(S[2], 'views'), '900 views');
  assert.equal(Sort.metaText({ views: 1 }, 'views'), '1 view');
  assert.equal(Sort.metaText(S[1], 'views'), '');
  assert.equal(Sort.metaText(S[0], 'added'), 'Added April 17, 2026');
});

test('saved choice: bad data gives the default', () => {
  assert.deepEqual(Sort.readChoice('{"type":"year","dir":"asc"}'), { type: 'year', dir: 'asc' });
  assert.deepEqual(Sort.readChoice('not json'), Sort.DEFAULT);
  assert.deepEqual(Sort.readChoice('{"type":"x","dir":"asc"}'), Sort.DEFAULT);
  assert.deepEqual(Sort.readChoice(null), Sort.DEFAULT);
});
