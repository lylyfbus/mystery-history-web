# Story style design: one voice and one structure for all 81 stories

Date: 2026-11-15. Status: waiting for owner approval.

## Why

The language of the posts is simple now, but each post has a different structure, because the first rewrite kept the old order of ideas. The owner wants each story to read like a story that a person wrote, with a consistent number of key points, a consistent order, and a consistent voice. The same text is read aloud by the audio player.

## Goals

- All 81 stories use one voice and one skeleton.
- A reader of age 10+ can follow the story and wants to read to the end.
- All facts stay correct. Each claim has a source in the fact-check record.

## Not goals

- No new research topics. A story does not get new key points that the record cannot support.
- No change to page titles, descriptions, hero images, groups, or reference lists, except when a reference supports no claim after the rewrite.
- No audio generation. Audio is made after the text is final.

## Must not happen

- An invented detail in a scene (weather, feelings, speech) that no source gives.
- A voice that talks down to the reader or makes jokes about death or victims.

## The voice: the friendly guide (owner decision)

The owner compared two drafts of the Atlantis story and chose draft B. Model text: `docs/style-pilot/atlantis-B-friendly-guide.md`.

- The storyteller walks with the reader: "let us", "you", "imagine", and sometimes "I think".
- Warm and curious. Light humor is permitted, but not about death, crime victims, or beliefs.
- Honest: "nobody knows" is said plainly. Disputed claims say who disagrees.
- One comparison from daily life for each hard number or shape ("like a target", "three times the height of Mount Everest").
- Each section ends with a line that leads to the next section.
- Techniques come from narrative non-fiction (Sheinkin, Fleming, Grann, Larson, Bryson). No sentences are copied from any book.

## Key points and length

- **5 key points** for each story (4 or 6 is permitted when the story needs it).
- **1,200 to 1,500 words**, about 8 to 10 minutes of audio.
- Existing rules stay: sentence maximum 30 words, paragraph maximum 100 words, no banned filler words. New: the average sentence is 9 to 15 words (my call: the pilot has 9.6).

## The skeleton

```
1. The opening     One person, one place, one moment. From a source.
2. The story       What happened, or what the object or place is.
3. The source      How we know: who found it, who reported it.
4. Answer 1        The weakest explanation, and why it fails.
5. Answer 2        A better explanation, for and against.
6. Answer 3        The strongest explanation, for and against.
7. The ending      What we know now, what is open, back to the opening.
```

Sections 2 to 6 hold the 5 key points. A story with only two explanations uses the free section for more of the story or the clues.

Small changes for each group:

- **Ancient Mysteries:** the opening is the discovery or the first written report.
- **Interesting History:** sections 2 and 3 tell the event in time order.
- **Unknown Phenomena:** the opening is one witness report; the explanations are the main part.

## Section titles

Each section has a short title that tells part of the story ("Who told Plato?"), not a label ("Sources"). 6 to 8 titles for each story. In the page they are `<h2>`. Today the tests forbid `<h2>` in a story, so that test changes.

## Approaches considered

| Approach | Good | Bad |
|---|---|---|
| **1. Rebuild from the checked text and the record (chosen)** | Facts are already checked. Fast. | A scene can only use details that the record has. |
| 2. New research for each story | Richer scenes | A second full fact check of 81 stories; high cost |
| 3. Only add titles and reorder paragraphs | Cheapest | The voice stays inconsistent; not what the owner asked for |

With approach 1, a writer may add a new detail only with a source that they opened, and they add a row to the record.

## Order of work

1. Pilot: 3 stories, one from each group (Atlantis is done as a draft). The owner reads them.
2. Correct the style guide from the owner's comments.
3. The other stories, in groups of 5, by helper agents with one brief. Each group is checked and committed before the next.

## Tests (the owner's rule: a test for each problem)

- Each story has 6 to 8 `<h2>` titles and no other heading level.
- Each story has 1,100 to 1,600 words.
- Sentence average 9 to 15 words; old maximum rules stay.
- The fact-check record has "Restructured: <date>", and each reference still supports a claim.
- Links between stories are kept (existing test).
- The audio player reads a section title, then a pause, then the text (player test).

## Left to the builder

- How `tools/set_body.py` and `tools/check_text.py` accept titles.
- How the player marks a pause after a title.
- `docs/writing-guide.md` is rewritten to match this design, with the Atlantis pilot as the example.
