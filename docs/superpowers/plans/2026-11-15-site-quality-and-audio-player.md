# Past Mystery Site Quality and Audio Player Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make all 91 pages consistent, readable for age 10+, correctly grouped and illustrated, and add a hybrid (MP3 + browser voice) audio player with playlists and a sleep timer, with a test for each problem found.

**Architecture:** The site stays static HTML in `src/`. Python scripts in `tools/` make repeatable changes (menu, feed, group moves, `stories.json`). The player is two plain JS files: `player-core.js` (logic, no browser calls, tested in Node) and `player-ui.js` (DOM, `<audio>`, `speechSynthesis`).

**Tech Stack:** Python 3 standard library (`unittest`, `html.parser`, `re`, `json`), Node 25 built-in test runner (`node --test`), plain JS/CSS, ffmpeg. No package install.

**Spec:** `docs/superpowers/specs/2026-11-15-site-quality-and-audio-player-design.md`

## Global Constraints

- Work directory: `sessions/mystery_history/project/mystery-history-web`. All paths below are relative to it.
- Commits are local only. Never `git push`. The owner approves each push.
- Audience is age 10+. Paragraph maximum 100 words. Sentence maximum 30 words. Post average sentence length 18 words or less.
- Post body: no `h2`/`h3`/`h4`, no lists, no inline images, prose only. Keep `&mdash;`-style HTML entities.
- Rewrites keep all facts, names, dates, sources, and the Amazon link. Doubtful claims go to `docs/fact-check-list.md`; they are not changed.
- No graphic detail of violence.
- Images: real free-license photo first (credit in `docs/image-credits.md`); generated image only if none. No AI image of a real person. Output `hero.webp`, 1024 px wide or more, same path as before.
- Write HTML with Python `open().write()`, never with shell heredocs.
- Menu on all pages, in this order: Home `/`, All Stories `/archive`, Listen `/listen` (added in Task 9), About `/about`, Editorial Policy `/editorial-policy`, Contact `/contact`.
- The player must not load on a page before the reader interacts, except the two small JS files with `defer`. It must not cover ads or content: when the bar shows, `body` gets bottom padding equal to the bar height.
- Vercel uses `cleanUrls`: link to `/listen`, not `/listen.html`.

## Review Focus

1. `localStorage` is blocked or full (private mode): the player still plays; playlists live in memory for the page; no error shows.
2. A saved playlist holds a slug that no longer exists in `stories.json`: the story is skipped and removed from the list on load.
3. The MP3 URL fails (404, offline): the player falls back to the browser voice for that story; if that also fails it goes to the next story and shows a short message.
4. The browser has no `speechSynthesis` or no voice: stories without MP3 show "Audio not ready for this story" and are skipped in a queue; the player never hangs.
5. Saved state has a bad format (old version, hand-edited, other tab wrote at the same time): load returns clean defaults and does not throw.

Each line has its test in Task 7 (1, 2, 5) or Task 8 (3, 4).

---

## Part 1: tests and format fixes

### Task 1: Test harness and site tests

**Files:**
- Create: `tests/site_lib.py`, `tests/test_site.py`, `run_tests.sh`

**Interfaces:**
- Produces (`tests/site_lib.py`):
  - `SRC: pathlib.Path` — the `src` directory
  - `GROUPS = {"ancient-mysteries": "Ancient Mysteries", "interesting-history": "Interesting History", "unknown-phenomena": "Unknown Phenomena"}`
  - `MENU = [("/", "Home"), ("/archive", "All Stories"), ("/about", "About"), ("/editorial-policy", "Editorial Policy"), ("/contact", "Contact")]` (Task 9 adds Listen)
  - `all_pages() -> list[Path]` — every `*.html` under `src` except `google*.html`
  - `post_slugs() -> list[str]`
  - `read_post(slug) -> dict` with keys `html, title (h1 text), group (badge text), breadcrumb_group, schema_group, paragraphs (list[str], plain text of body `<p>` before `.post-sources`), hero_src, hero_alt`
  - `sentences(text) -> list[str]` — split on `.`, `!`, `?` followed by space and a capital or quote; do not split after `Mr.`, `Mrs.`, `Dr.`, `St.`, `U.S.`, single capital initials, or inside numbers
  - `resolve(page: Path, href: str) -> Path | None` — maps an internal href/src to a file, honoring `cleanUrls` (`/about` → `about.html`); `None` for external links and `/_vercel/`
- `run_tests.sh`: runs `python3 -m unittest discover -s tests -v` then `node --test tests/` ; exits non-zero if either fails.

- [ ] **Step 1: Write `tests/site_lib.py` and `tests/test_site.py`** with these test methods (class `SiteTests`). Each test collects all failures and asserts the list is empty, so one run shows every bad page:

| Method | Assertion |
|---|---|
| `test_internal_links_and_images_resolve` | for every page, every `href`/`src`: `resolve()` is `None` or an existing file |
| `test_menu_is_same_on_all_pages` | the `(href, text)` list inside `<nav class="site-nav">` equals `MENU` |
| `test_footer_links_same_on_all_pages` | footer hrefs equal `["/archive", "/about", "/editorial-policy", "/contact", "/privacy-policy"]` |
| `test_post_head_uses_own_slug` | canonical, `og:url`, both `og:image`/`twitter:image`, schema `@id`, schema `image` each contain `/{slug}`; `og:title`, `twitter:title`, schema `headline` equal the `h1` text (after HTML-unescape) |
| `test_post_format` | body has 0 `h2/h3/h4/ul/ol`, exactly 1 `<img>` (class `hero-image`), has `.post-sources`, `.share-buttons`, `.breadcrumb` |
| `test_group_is_consistent_in_post` | `group == breadcrumb_group == schema_group` and `group in GROUPS.values()` |
| `test_each_post_listed_once_per_listing` | each slug is on exactly 1 category page (the one for its group), exactly once in `archive.html`, `sitemap.xml`, `feed.xml` |
| `test_home_counts` | each `View All (N)` equals the number of posts in that group |
| `test_paragraph_length` | no paragraph over 100 words |
| `test_sentence_length` | no sentence over 30 words; mean sentence length of a post ≤ 18 |
| `test_no_graphic_filler` | none of these phrases (case-insensitive) in a post body: "breathtaking", "masterclass", "nearly severed", "ripped open" |

- [ ] **Step 2: Run** `./run_tests.sh`. Expected now: `test_internal_links_and_images_resolve`, `test_post_head_uses_own_slug`, `test_post_format` (after removing the uncommitted inline `<audio>` block from `jack-the-ripper.html`, which Task 8 replaces) PASS; menu, listing, counts, paragraph, sentence tests FAIL. Record the failing counts in the commit message. If a test expected to pass fails, it found a new problem: keep the test, add the fix to Task 2.
- [ ] **Step 3: Mark the text tests as expected failures until Part 3.** Add env switch: `test_paragraph_length`, `test_sentence_length`, `test_no_graphic_filler` check only slugs listed in `tests/rewritten.txt` (one slug per line; empty now). Part 3 adds slugs as batches finish; Task 5's last step deletes the file and the switch.
- [ ] **Step 4: Commit** `test: add site test harness (menu, links, groups, listings, text rules)`

### Task 2: Format fixes

**Files:**
- Create: `tools/sitelib.py`, `tools/fix_menu.py`, `tools/build_feed.py`
- Modify: every `src/**/*.html` (menu), `src/feed.xml`, `src/categories/ancient-mysteries.html`, `src/index.html`, `src/posts/jack-the-ripper.html`

**Interfaces:**
- Produces: `tools/sitelib.py` re-exports the read helpers of `tests/site_lib.py` (import, do not copy) and adds `write(path, text)`.
- `tools/fix_menu.py`: replaces the inside of `<nav class="site-nav">…</nav>` on all pages with the `MENU` links. Idempotent.
- `tools/build_feed.py`: writes `src/feed.xml` with one `<item>` per post, newest first, date from `src/post-dates.json` (fallback: schema `datePublished`), title = `h1`, description = meta description, link = `https://pastmysteries.com/posts/{slug}`. Keep the existing channel header.

- [ ] **Step 1:** Run the three failing tests from Task 1 (menu, listings, counts) — confirm FAIL.
- [ ] **Step 2:** Write and run `tools/fix_menu.py` and `tools/build_feed.py`. Remove the `skinwalker-ranch` card from `categories/ancient-mysteries.html`, add it to `categories/unknown-phenomena.html` (copy the `category-bar` format), set home count `View All (34)` / `(27)`. Remove the inline `<div class="post-audio-player">` block from `jack-the-ripper.html`.
- [ ] **Step 3:** Run `./run_tests.sh`. Expected: all tests PASS (text tests check 0 posts).
- [ ] **Step 4:** Start `python3 -m http.server 8080 -d src`, open `/`, one post, one category page in the browser; click both carousel arrows, a card, each menu link, each share button. Expected: no console error, no 404.
- [ ] **Step 5: Commit** `fix: same menu on all pages, full feed, skinwalker listing`

## Part 2: groups

### Task 3: Group move tool and the 9 moves

**Files:**
- Create: `tools/move_group.py`
- Modify: the 9 posts, 3 category pages, `src/index.html`, `src/archive.html` (only if it has group sections; today it has one grid)

**Interfaces:**
- `python3 tools/move_group.py <slug> <group-slug>`: updates the badge, breadcrumb link and text, breadcrumb schema (`name` and `item`), moves the `category-bar` card between category pages, moves the `carousel-card` on the home page if the post is there (else nothing), and recomputes all three `View All (N)`. Exits 1 if the slug or group is unknown. Idempotent.

- [ ] **Step 1: Write a failing test** `test_group_assignment` in `tests/test_site.py`: a dict `EXPECTED_GROUP` for the 10 slugs of spec section 6 (9 moves + `skinwalker-ranch: "Unknown Phenomena"`), assert `read_post(slug)["group"]` equals it. Run: 9 FAIL.
- [ ] **Step 2:** Write `tools/move_group.py`; run it for the 9 moves in the spec table.
- [ ] **Step 3:** `./run_tests.sh` — all PASS (the listing and count tests prove the 6 places agree).
- [ ] **Step 4: Commit** `fix: move 9 posts to the correct group`

## Part 3: text

### Task 4: Rewrite one pilot post and fix the method

**Files:**
- Modify: `src/posts/jack-the-ripper.html`, `tests/rewritten.txt`
- Create: `tools/set_body.py`, `docs/fact-check-list.md`, `docs/writing-guide.md`

**Interfaces:**
- `python3 tools/set_body.py <slug> <file-with-paragraphs>`: the input file has one paragraph per block, blank line between blocks, inline `<em>` allowed, plain UTF-8 text. The tool HTML-escapes text, converts `—` `’` `“` `”` `é`-type characters to named entities as the posts use, and replaces only the `<p>` elements between `</header>` and `<div class="post-sources">`. It changes nothing else.
- `docs/writing-guide.md`: the rules of spec section 7 plus 3 before/after examples taken from the pilot. Every later batch follows it.

- [ ] **Step 1:** Add `jack-the-ripper` to `tests/rewritten.txt`. Run text tests: FAIL.
- [ ] **Step 2:** Rewrite the post by the spec rules. Check each fact against the old text; list doubts in `docs/fact-check-list.md` as `slug | claim | why doubtful`.
- [ ] **Step 3:** `./run_tests.sh` PASS. Word count is 70% to 110% of the old count (a rewrite must not cut the story).
- [ ] **Step 4:** Show the owner the first 4 paragraphs before/after. **Stop for owner approval of the style** before Task 5.
- [ ] **Step 5: Commit** `content: rewrite jack-the-ripper for age 10+ (pilot)`

### Task 5: Rewrite the other 80 posts in 8 batches of 10

**Files:** Modify: `src/posts/*.html`, `tests/rewritten.txt`, `docs/fact-check-list.md`; category pages and meta descriptions only if a title changes (titles do not change in this plan).

Batches are alphabetical by slug. For each batch:

- [ ] **Step 1:** Add the 10 slugs to `tests/rewritten.txt`; text tests FAIL for them.
- [ ] **Step 2:** Rewrite each post with `docs/writing-guide.md` and `tools/set_body.py`. While reading, confirm the group (spec section 6 rules) and that the hero image agrees with the text; add disagreements to `docs/image-review.md` as `slug | problem`.
- [ ] **Step 3:** `./run_tests.sh` PASS; word count check as Task 4.
- [ ] **Step 4: Commit** `content: rewrite batch N (first-slug … last-slug)`

After batch 8:
- [ ] **Step 5:** Delete `tests/rewritten.txt` and the switch; text tests now check all 81 posts. `./run_tests.sh` PASS. Commit.

## Part 4: images

### Task 6: Replace wrong hero images

**Files:**
- Modify: `src/static/images/posts/{slug}/hero.webp` for each slug in spec section 8 plus `docs/image-review.md`; `alt` text in the post, home card, archive card, category card
- Create: `docs/image-credits.md`, `tools/set_hero.py`

**Interfaces:**
- `python3 tools/set_hero.py <slug> <image-file> "<alt text>"`: converts to WebP (ffmpeg, quality 80, longest side 1600 px maximum), writes `hero.webp`, and sets the same `alt` on the post hero and on every card that shows this hero.

- [ ] **Step 1: Write failing tests:** `test_hero_alt_same_on_all_cards` (the alt of each card equals the post hero alt) and `test_image_credits` (every row of `docs/image-credits.md` names an existing slug, a source URL, an author, and a license from `{"Public domain", "CC0", "CC BY", "CC BY-SA"}`; any slug in `REPLACED_HEROES` list in the test has a row or the word `generated`).
- [ ] **Step 2:** For each slug: search Wikimedia Commons for a real photo of the subject. Ask the owner before each download (file name, source, size). If none fits, generate with `skills/builtin_skills/generate-image` and a prompt taken from the post text. View every new image next to the post's first paragraph before use.
- [ ] **Step 3:** If a license needs credit (CC BY, CC BY-SA), add `<p class="image-credit">Image: {author}, {license}, via Wikimedia Commons</p>` directly after the hero `<img>`; update `test_post_format` to allow it; add a small style in `post-styles.css`.
- [ ] **Step 4:** `./run_tests.sh` PASS; view each changed post in the browser. Commit `fix: replace hero images that did not agree with the story`.

## Part 5: audio player

### Task 7: `stories.json` and player logic

**Files:**
- Create: `tools/build_stories.py`, `src/static/data/stories.json`, `src/static/js/player-core.js`, `tests/player.test.js`
- Modify: `tests/test_site.py`

**Interfaces:**
- `stories.json`: `[{"slug", "title", "group" (slug form), "image": "/static/images/posts/{slug}/hero.webp", "audio": "/static/audio/{slug}.mp3" | null, "duration": seconds | null}]`, in archive order. `audio` is set only when the file exists; duration from `ffprobe`.
- `player-core.js` — one file that works with `require()` in Node and as `window.PlayerCore` in the browser:

```js
DEFAULT_LISTS  // [{id:'all',name:'All Stories'},{id:'ancient-mysteries',name:'Ancient Mysteries'},{id:'interesting-history',name:'Interesting History'},{id:'unknown-phenomena',name:'Unknown Phenomena'}]
createLibrary(stories, storage)        // storage: {getItem,setItem} or null
  .lists()            -> [{id, name, isDefault, slugs}]   // 4 defaults first
  .createList(name)   -> id            // trims; throws Error('name required') if empty; max 60 chars
  .renameList(id, name)                // throws Error('default list') on a default
  .deleteList(id)                      // throws Error('default list') on a default
  .addStory(id, slug) -> boolean       // false if already there; throws on default or unknown slug
  .removeStory(id, slug)
createQueue(slugs, {mode: 'order'|'random', startSlug, rng = Math.random})
  .current() -> slug|null   .next() -> slug|null   .prev() -> slug|null
  .setMode(mode)            .mode
createSleepTimer(now = Date.now)
  .start(minutes)  .startEndOfStory()  .cancel()
  .remainingMs() -> number|null        // null when off or end-of-story
  .volumeFactor() -> 0..1              // 1 until the last 10 s, then linear to 0
  .shouldStop() -> boolean
  .storyEnded() -> boolean             // true if the player must stop now
splitForSpeech(paragraphs, maxChars = 220) -> string[]   // split at sentence ends; no piece over maxChars unless one sentence is longer
saveSession(storage, {listId, slug, position, mode})   loadSession(storage) -> object|null
STORAGE_KEY = 'pm.player.v1'
```

- [ ] **Step 1: Write failing tests** — `tests/test_site.py::test_stories_json_matches_posts` (81 entries; slug, title, group equal the post; `audio` non-null only if the file exists) and `tests/player.test.js` with these cases:
  - defaults: `lists()` returns 4 defaults; `all` has every slug; group lists hold only their group
  - create/rename/delete a list; data survives a new `createLibrary` on the same storage
  - rename/delete/add on a default list throws `'default list'`
  - `addStory` twice → second returns `false`, list length 1
  - order queue: `next()` walks the list, returns `null` at the end; `prev()` at the start returns the first slug
  - random queue with a seeded `rng` over 10 slugs: 10 calls give 10 different slugs, then `null`; `startSlug` is first
  - timer: `start(30)`, advance fake clock 29 min 55 s → `shouldStop()` false, `volumeFactor()` ≈ 0.5; at 30 min → `shouldStop()` true; `cancel()` → `remainingMs()` null
  - timer end-of-story: `storyEnded()` true once, `shouldStop()` false before
  - `splitForSpeech`: no piece over 220 chars for normal text; joined pieces equal the input words
  - Review Focus 1: `storage = null` and a storage whose `setItem` throws → all calls work
  - Review Focus 2: saved list holds `'gone-slug'` → `lists()` omits it
  - Review Focus 5: storage holds `'{bad json'`, `'[]'`, `'{"lists":5}'` → defaults, no throw
- [ ] **Step 2:** Run `./run_tests.sh` — new tests FAIL.
- [ ] **Step 3:** Write `tools/build_stories.py` and `player-core.js`. Random mode: Fisher–Yates on a copy with `rng`, then move `startSlug` to index 0.
- [ ] **Step 4:** `./run_tests.sh` PASS. Commit `feat: stories.json and player logic with tests`.

### Task 8: Player bar and story-page buttons

**Files:**
- Create: `src/static/js/player-ui.js`, `src/static/css/player.css`, `tools/add_player.py`
- Modify: all `src/**/*.html` (one `<link>` and two `<script defer>` tags before `</body>`; posts also get the button row), `tests/test_site.py`, `tests/player.test.js`

**Interfaces:**
- Consumes: `window.PlayerCore` and `/static/data/stories.json` from Task 7.
- `tools/add_player.py`: idempotent. Adds, with absolute paths, `/static/css/player.css`, `/static/js/player-core.js`, `/static/js/player-ui.js`. In posts, adds directly after the hero image: `<div class="listen-row" data-slug="{slug}"><button class="listen-btn" type="button">&#9654; Listen</button><button class="listen-add" type="button">+ Add to playlist</button></div>`.
- `player-ui.js` exposes `window.PastPlayer = { play(listId, slug), toggle(), next(), prev(), setMode(mode), setTimer(minutes|'end'|null) }` for the Listen page.
- Source choice, in `player-ui.js` as a pure function exported for the test: `pickSource(story, {hasSpeech}) -> 'mp3' | 'speech' | 'none'`.
- Speech text: `fetch('/posts/' + slug)`, parse with `DOMParser`, take `article.post-content > p` before `.post-sources`, then `PlayerCore.splitForSpeech`. Speak the title first.

Behavior decided here:
- The bar (`<div id="pm-player" role="region" aria-label="Audio player">`) is created on first play, or on load if `loadSession` returns a session; then it shows paused with a "Continue" label. Controls: previous, play/pause, next, title (link to the post), time (MP3) or "Paragraph 3 of 24" (speech), Order/Random switch, Timer menu (Off, 15, 30, 45, 60, End of story), source tag ("Recorded" / "Device voice"), close.
- "+ Add to playlist" opens a small menu of the reader's lists plus "New playlist…".
- Position is saved every 5 s and on `pagehide`.
- Timer: tick each second; set `audio.volume = volumeFactor()`; on `shouldStop()` pause, reset volume to 1, clear the timer.
- Media Session: set title, artist "Past Mystery", artwork = story image; handlers for play, pause, next, previous.
- Errors: Review Focus 3 and 4 as written there. Message area is `aria-live="polite"`.
- All buttons are real `<button>` elements with text or `aria-label`; the bar works with keyboard only.

- [ ] **Step 1: Write failing tests:** `test_player_assets_on_all_pages` (every page has the 3 tags once; every post has one `.listen-row` with its own slug) and, in `player.test.js`, `pickSource`: mp3 when `audio` set; speech when `audio` null and `hasSpeech`; none when neither.
- [ ] **Step 2:** FAIL. Write the files; run `tools/add_player.py`.
- [ ] **Step 3:** `./run_tests.sh` PASS.
- [ ] **Step 4: Browser check** on the local server, desktop and mobile width: Listen on Jack the Ripper (MP3) plays; Listen on another post (speech) plays; next/previous; Random; timer "End of story"; reload → "Continue" resumes at the saved place; block the MP3 URL → falls back to device voice; no console errors; the bar does not cover the footer.
- [ ] **Step 5: Commit** `feat: player bar and listen buttons on story pages`

### Task 9: Listen page

**Files:**
- Create: `src/listen.html`
- Modify: `tests/site_lib.py` (`MENU` gains `("/listen", "Listen")` after All Stories), all pages via `tools/fix_menu.py`, `src/sitemap.xml`, `src/static/css/player.css`, `src/static/js/player-ui.js`

Behavior: copy the head, header, and footer of `archive.html` (own title, description, canonical `https://pastmysteries.com/listen`). Left column: the lists (4 defaults with counts, then the reader's lists with Rename and Delete buttons, then "+ New playlist"). Right column: stories of the selected list with image, title, group, a Play button, a "+" (add to another list) and, in the reader's lists, a Remove button. Above the stories: "Play all" and "Play random". Delete asks for confirmation with the list name. One column on screens under 700 px. Without JavaScript the page shows a line of text and a link to All Stories.

- [ ] **Step 1: Failing tests:** menu test now expects 6 links; `test_listen_page` (exists, in sitemap, has `id="pm-lists"` and `id="pm-stories"`, loads the player files).
- [ ] **Step 2:** Build the page; run `tools/fix_menu.py`.
- [ ] **Step 3:** `./run_tests.sh` PASS.
- [ ] **Step 4: Browser check:** create "Sleep list", add 3 stories from the page and 1 from a story page, rename it, play in order, play random, remove a story, delete the list, reload between steps (data stays). Set timer 15 and confirm the countdown shows.
- [ ] **Step 5: Commit** `feat: listen page with playlists`

### Task 10: MP3 files

**Files:**
- Modify: `src/static/audio/*.mp3`, `src/static/data/stories.json`, `.gitignore` (no change unless the owner picks outside storage)
- Create: `tools/encode_audio.sh`

- [ ] **Step 1:** `tools/encode_audio.sh <in> <slug>`: `ffmpeg -i <in> -ac 1 -ar 44100 -b:a 64k src/static/audio/<slug>.mp3`. Add `test_audio_files_small` : every MP3 in `src/static/audio` is mono and at most 72 kbit/s. Run: FAIL on the 35 MB file.
- [ ] **Step 2:** Regenerate Jack the Ripper from the new text with `sessions/mystery_history/scripts/chunked_audio_gen.py`. First confirm the local model service starts (state in `~/.helix/services/local-model-service/state.json`). If it cannot start from this session, stop and tell the owner the exact command to run; the player already works with the device voice.
- [ ] **Step 3:** Encode, run `tools/build_stories.py`, `./run_tests.sh` PASS, listen to the first minute and one middle minute. Commit.
- [ ] **Step 4:** Before more audio is added: read the Vercel limits page and report to the owner how many stories fit in the repo, with a recommendation (repo or storage service). Then generate in batches of 5 in the background, same steps, one commit per batch.

---

## Self-review notes

- Spec sections 5–9 map to Tasks 1–2, 3, 4–5, 6, 7–10. Section 11 decisions are in Global Constraints.
- Owner stops: Task 4 Step 4 (style), each image download in Task 6, Vercel/storage in Task 10, and any push.
