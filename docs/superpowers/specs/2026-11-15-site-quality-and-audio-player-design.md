# Past Mystery: site quality pass and audio player

Date: 2026-11-15. Status: waiting for approval.

## 1. Intent

Past Mystery must be a site that a reader trusts and enjoys. Each page must look
the same, read easily, show a correct picture, and be in the correct group. The
reader must also be able to listen to the stories, for example in bed.

Each problem we find gets an automatic test. A future change that brings the
problem back makes the test fail.

## 2. Goals, non-goals, anti-goals

Goals

- One page format on all 91 pages. No button or link gives an error.
- All 81 stories are easy to read on a phone.
- Each hero image shows the subject of its story.
- Each story is in the correct group, on all pages that list it.
- A reader can listen to all 81 stories, with playlists, random play, and a sleep timer.
- One command runs all tests.

Non-goals

- No reader accounts and no server. Playlists stay in the reader's browser.
- No new stories in this work.
- No change to the hot news site.
- No push to production. The owner approves each push.

Anti-goals (these make the work a failure)

- A rewrite that changes or invents facts.
- A player that breaks ads, analytics, or search ranking.
- An image of a real, living or recently dead person made by AI.

## 3. Current state (from the review)

| Area | Finding |
|---|---|
| Links | 0 broken links, 0 missing images on 91 pages. |
| Menu | Posts show 2 menu links. Home shows 5. Policy and contact pages show 4. |
| Text | All posts: no subheadings (this is the rule from the May 2026 rewrite). Paragraphs are 200 to 360 words. |
| Images | About 10 hero images do not agree with the story. Each post has 2 inline images on disk that no page uses. |
| Groups | Skinwalker Ranch is listed in 2 groups. About 8 posts are possibly in the wrong group. |
| Feed | `feed.xml` has 39 of 81 posts, with duplicates. |
| Audio | 1 MP3 (Jack the Ripper, 35 MB, 18 minutes, not committed). |
| Tests | None. |

## 4. Work order

The work is 5 parts. Each part is complete and tested before the next part starts.

```
1. Tests + format fixes   (small)
2. Groups                 (small)
3. Text of 81 posts       (large, in batches of 10)
4. Images                 (medium)
5. Audio player           (medium)  ->  then MP3 files, in the background
```

## 5. Part 1: tests and format fixes

Tests live in `tests/`. One command runs them: `./run_tests.sh`.

- `tests/test_site.py` (Python `unittest`, no install necessary) reads the HTML files.
- `tests/player.test.js` (Node `node --test`, no install necessary) tests the player logic.

Site tests (each one is a problem we found, or a problem in the knowledge notes):

| Test | Problem it stops |
|---|---|
| All internal links and image paths point to a file | Broken link |
| All pages have the same 5 menu links and the same footer links | Menu changes between pages |
| Title, schema, Open Graph, Twitter, canonical, breadcrumb all use the post's own slug | Data of one post copied into a different post |
| Post body has no `h2`/`h3`, has a hero image, sources, share buttons | Format drift |
| No paragraph in a post body is longer than 100 words | Wall of text |
| No sentence is longer than 30 words; the average for a post is 18 or less | Text too hard for age 10+ |
| The group in the badge, the breadcrumb, and the schema are the same | Group mismatch |
| Each post is on exactly 1 group page, and on the archive, sitemap, and feed | Skinwalker duplicate, feed gaps |
| "View All (N)" on the home page equals the number of posts in the group | Wrong count |
| `stories.json` (see part 5) has exactly the 81 posts with the same title and group | Player list out of date |

Fixes: same 5-link menu on all pages, rebuild `feed.xml` from the posts, fix the
Skinwalker listing and the count. The 2 CSS copies (`src/style.css` and
`src/static/css/style.css`) stay as they are, because pages use both.

## 6. Part 2: groups

Rule for each group:

- **Ancient Mysteries**: places, objects, and people of ancient or lost
  civilizations. The thing itself is old (before about 500 AD), or it is a
  ruin of a lost civilization (Machu Picchu, Angkor, Easter Island).
- **Interesting History**: recorded events, people, and objects after that time.
- **Unknown Phenomena**: reports that science has not explained: lights,
  creatures, sounds, UFOs, zones.

Example: Oak Island. The digging started in 1795. It is a recorded treasure
hunt, not an ancient site. So it moves to Interesting History.

Planned moves (my call, confirmed again when I read each post in part 3):

| Post | From | To | Reason |
|---|---|---|---|
| oak-island-money-pit-nova-scotia | Ancient | History | Starts in 1795 |
| el-dorado-lost-city | Ancient | History | Legend of the 1500s |
| crystal-skulls | Ancient | History | Made in the 1800s |
| shroud-of-turin | Ancient | History | First record in 1354 |
| voynich-manuscript-mystery | Unknown | History | A book from the 1400s |
| winchester-mystery-house | Unknown | History | A house and its owner |
| dancing-plague-1518 | Unknown | History | A recorded event of 1518 |
| flannan-isle-lighthouse | Unknown | History | A disappearance, as Mary Celeste and Roanoke |
| philadelphia-experiment | History | Unknown | A claimed event without records |
| skinwalker-ranch | (2 groups) | Unknown | Remove the second listing |

A move changes 6 places: the badge, the breadcrumb, the breadcrumb schema, the
2 group pages, and the home page count. A script does the move, and the tests of
part 1 check all 6 places.

## 7. Part 3: text

Audience (owner rule, 2026-11-15): readers of age 10 and older. The language
is always clear and simple. A child of 10 can read each sentence without help.

Rules for each post:

- Short sentences. Target: 15 words on average, 30 words maximum. One idea for
  each sentence. No sentence with more than 2 commas of nested clauses.
- Common words. If a hard word is necessary (for example "radiocarbon"),
  explain it in the same sentence or the next one.
- Violence and death: say what happened, but give no graphic detail (builder's
  call, because of the age 10+ rule). Example: "She had been killed with a
  knife", not a description of the wounds. This applies most to Jack the
  Ripper, Black Dahlia, Zodiac Killer, and Chupacabra.
- Keep the facts, the names, the dates, and the sources. If a claim looks
  wrong, I do not change it silently. I put it in a list for the owner.
- Keep the format rule: no subheadings, no lists, prose only.
- Split paragraphs. Maximum 100 words. One idea for each paragraph.
- Start with the story, not with a summary.
- Remove filler words and repeated ideas ("breathtaking in scope",
  "masterclass", "one of the most extraordinary").
- Mix short and long sentences. The text must also sound good when read aloud.

Work in batches of 10 posts. After each batch: run the tests, show the owner a
before/after sample.

## 8. Part 4: images

Heroes to replace (first list, from the review):
sacsayhuaman, shroud-of-turin, pentagon-uap-reports, molasses-flood,
mandela-effect, rosetta-stone, copper-scroll-treasure, gobekli-tepe,
saqqara-bird, baghdad-battery-ancient-electricity, uss-nimitz-tic-tac.

Source of the new images (owner rule, 2026-11-15):

1. First, look for a real photo with a free license (public domain or
   Creative Commons) on Wikimedia Commons. Record the author and the license
   in `docs/image-credits.md`, and show the credit where the license requires it.
2. If no good real photo exists, generate an image that agrees closely with
   the story. Check the result against the text before use.

In part 3, I also check the other 70 heroes against the new text.

After replacement: update the `alt` text on the post and on each card. The 162
unused inline images stay on disk. They are not part of this work.

## 9. Part 5: audio player

### Approaches

| | A. Player bar on each page + Listen page (picked) | B. Listen page only | C. Change the site to load pages without reload |
|---|---|---|---|
| Listen from a story page | Yes | No, the reader must go to a different page | Yes |
| Sound continues when the reader changes page | No. It stops, and the bar offers "Continue" | Not applicable | Yes |
| Risk | Low | Low | High: can break ads, analytics, search |
| Work | Medium | Small | Large |

A is picked. The reader who wants a long session uses the Listen page and stays
there. C is rejected because of the anti-goal about ads and search.

### What the reader sees

```
Story page:      [ > Listen ]  [ + Add to playlist ]        (below the hero image)

Bar (all pages, bottom, only after the first play):
  [img] Jack the Ripper          |<   >/||   >|    3:12 / 18:01   [Order|Random]  [Timer 30:00]

Listen page (/listen):
  Playlists                         Stories in "All Stories"
  ----------------------            ----------------------------------
  * All Stories        (81)         1. Atlantis ...            [>] [+]
  * Ancient Mysteries  (30)         2. Nazca Lines ...         [>] [+]
  * Interesting History(28)         ...
  * Unknown Phenomena  (23)
  My sleep list         (5)  [rename] [delete]
  [ + New playlist ]
```

### Parts

```
build_stories.py  --->  static/data/stories.json   (slug, title, group, image, audio URL or null)
                                  |
                          static/js/player-core.js   (no browser calls: playlists, queue, timer)
                                  |
                          static/js/player-ui.js     (bar, buttons, Listen page)
                              /           \
                  <audio> for MP3     speechSynthesis for stories without MP3
```

- `player-core.js` holds all logic and no browser calls. Thus Node can test it.
- Playlists are saved in `localStorage`. The 4 default lists come from
  `stories.json`. The reader cannot change or delete them.
- Hybrid source: if `stories.json` has an audio URL, the player uses the MP3.
  If not, the player loads the story page, takes the paragraphs before the
  sources, and reads them with the browser voice. The bar shows which source
  is in use.
- Random play: each story plays one time before a story repeats.
- Sleep timer: 15, 30, 45, 60 minutes, or "end of this story". The volume
  goes down in the last 10 seconds (MP3 only), then the player stops.
- Lock screen controls through the Media Session API (MP3 only).
- The position in the story and the queue are saved. After a page change the
  bar shows "Continue".

### Player tests (`tests/player.test.js`)

Create, rename, delete a playlist. A default list refuses change. Add and
remove a story. Add the same story 2 times gives 1 entry. Order mode gives the
list order. Random mode plays each story one time. "Next" at the end stops.
Timer stops at the set time. Saved data with a bad format does not break the player.

### MP3 files

- Format: mono, 64 kbit/s. About 8 MB for an 18-minute story. Re-encode the
  Jack the Ripper file (35 MB) to this format.
- Location: `src/static/audio/{slug}.mp3`. The URL is in `stories.json`, thus
  the files can move to a storage service later without a code change.
- Generation uses the existing `chunked_audio_gen.py` after part 3, because the
  audio must agree with the new text. It runs in batches in the background.
- Open point for the builder: confirm that the local voice model starts from
  this session, and confirm the Vercel size limit before more than about
  100 MB of audio is in the repo.

## 10. Left to the builder

Class names, CSS of the bar, the exact wording of buttons, the script names,
the batch order of the posts.

## 11. Decisions that are the owner's

1. **Image source.** Decided: real photo first, generated image if none (section 8).
2. **Group moves** in section 6: no objection from the owner. Treated as approved.
3. **Text.** Decided: age 10+, clear and simple language (section 7). The
   limits (100 words for a paragraph, 30 for a sentence) are the builder's call.
