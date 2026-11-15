# Writing guide for Past Mystery stories

Audience: readers of age 10 and older. A child of 10 must be able to read each
sentence without help. The text is also read aloud by the audio player.

Design: `docs/superpowers/specs/2026-11-15-story-style-design.md`.
Model stories: `lost-city-atlantis-plato`, `jack-the-ripper`, `wow-signal`.
`./run_tests.sh` checks the rules marked with (test).

## The voice: the friendly guide

The storyteller walks with the reader through the story, like a kind teacher on
a museum visit.

- Speak to the reader: "you", "let us", "imagine". Use "I" two times at most.
- Do not repeat one phrase as a formula. "Let us" three times at most in a
  story. "Imagine" two times at most.
- Warm and curious. Light humor is permitted, but never about death, victims of
  crime, illness, or beliefs.
- Honest. Say "nobody knows" plainly. If experts disagree, say who thinks what.
- One comparison from daily life for a hard number or shape ("like a target").
- End each section with one line that leads to the next section.

## The structure

A story has **5 key points** (4 or 6 if necessary) and 6 to 8 sections (test).
Each section has a short title (test: 8 words or less).

```
1. The opening     One person, one place, one moment. From a source.
2. The story       What happened, or what the object or place is.
3. The source      How we know: who found it, who reported it.
4. Answer 1        The weakest explanation, and why it fails.
5. Answer 2        A better explanation, for and against.
6. Answer 3        The strongest explanation, for and against.
7. The ending      What we know now, what is open, back to the opening.
```

- **Ancient Mysteries:** open with the discovery or the first written report.
- **Interesting History:** sections 2 and 3 tell the event in time order.
- **Unknown Phenomena:** open with one witness report; the explanations are the main part.
- A story with fewer than three explanations uses the free sections for the
  story or the clues. A story with no "explanations" (a plain history story)
  uses them for the steps of the event and its results.
- A title tells part of the story ("Who told Plato?"). It is not a label
  ("Sources", "Theories", "Introduction", "Conclusion").

## Rules

1. **Length.** 1,200 to 1,500 words (test: 1,100 to 1,600).
2. **Short sentences.** Maximum 30 words (test). Average 9 to 15 words (test).
   Mix short and medium sentences so that the text does not sound choppy.
3. **Short paragraphs.** Maximum 100 words (test). Usually 2 to 5 sentences.
4. **Common words.** If a hard word is necessary, explain it immediately.
   Example: "An alibi is proof that a person was in a different place."
5. **Only checked facts.** Use claims from `docs/fact-check/<slug>.md` and the
   checked text. A new fact (also a definition or a comparison) needs a source
   that you opened, and a new row in the record.
6. **No invented scene detail.** No weather, feelings, thoughts, or speech that
   a source does not give. You may ask the reader to imagine: that is not a fact.
7. **No graphic violence.** Say what happened. Do not describe wounds or bodies.
   Nothing unsuitable for a child of 10.
8. **No filler.** Not "breathtaking", "masterclass" (test), "one of the most
   extraordinary", "it is worth noting", "a testament to", "delve".
9. **No time words that become wrong.** "More than 130 years", not "137 years".
10. **Format.** Section titles and paragraphs only. No lists, no images, no bold
    (test). `<em>` for titles of books, films, and ships. Keep links to other
    stories: `<a href="/posts/slug">words</a>`.

## How to change a story

```
python3 tools/get_body.py <slug> draft.txt     # export: "## Title" lines and paragraphs
python3 tools/set_body.py <slug> draft.txt     # write it back
python3 tools/restore_links.py <slug>          # links to other stories
python3 tools/check_text.py <slug>             # must print OK
./run_tests.sh
```

Then add `Restructured: YYYY-MM-DD` and the new rows to `docs/fact-check/<slug>.md`,
and remove the slug from `tests/style_pending.txt`.
