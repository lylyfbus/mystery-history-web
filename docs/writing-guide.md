# Writing guide for Past Mystery stories

Audience: readers of age 10 and older. A child of 10 must be able to read each
sentence without help. The text is also read aloud by the audio player.

`./run_tests.sh` checks the rules marked with (test).

## Rules

1. **Short sentences.** Maximum 30 words (test). Average 18 words or less for a
   post (test). Aim for 10 to 15. One idea for each sentence.
2. **Short paragraphs.** Maximum 100 words (test). Aim for 2 to 5 sentences.
   One idea for each paragraph.
3. **Common words.** If a hard word is necessary, explain it immediately.
   Example: "Anatomy is the study of how a body is built."
4. **Start with the story.** Begin with a person, a place, and a moment. Do not
   begin with a summary.
5. **Keep the facts.** Keep all names, dates, numbers, and sources. Do not add
   facts. If a claim looks wrong, do not change it. Add a line to
   `docs/fact-check-list.md`.
6. **No graphic violence.** Say what happened. Do not describe wounds.
7. **No filler.** Do not use "breathtaking", "masterclass" (test), "one of the
   most extraordinary", "it is worth noting", "a testament to".
8. **No time words that become wrong.** Write "more than 130 years", not
   "137 years".
9. **Format.** Prose only. No subheadings, no lists, no images in the body (test).
   Use `<em>` for titles of books, films, and ships.
10. **Length.** Keep 70% to 110% of the old word count. A rewrite must not
    remove parts of the story.

## Examples (from the pilot post, Jack the Ripper)

**Long sentence to short sentences**

- Before: "In the early hours of August 31, 1888, a cart driver named Charles
  Allen Cross was walking to work along Buck's Row, a dim, narrow street in the
  Whitechapel district of London's East End, when he saw what he thought was a
  tarpaulin lying in the street gateway."
- After: "It was very early on August 31, 1888. A cart driver named Charles
  Allen Cross was walking to work in London. His path took him along Buck's
  Row, a dark and narrow street in a poor area called Whitechapel. He saw a
  shape on the ground near a gate."

**Graphic detail removed, fact kept**

- Before: "Her throat had been cut so deeply that the wound nearly severed her
  head from her body."
- After: "Someone had killed her with a knife."

**Hard word explained**

- Before: "DNA analysis of a shawl allegedly found at the Eddowes murder scene
  pointed to Kosminski — but the shawl's provenance and the testing methodology
  have been widely criticized."
- After: "He said that DNA on an old shawl proved Kosminski was the killer. DNA
  is the code inside every living cell, and it is different for each person.
  But many experts doubt the claim. Nobody can prove where the shawl came from,
  and the tests have been strongly criticized."

## How to change a post

1. Write the new text in a plain text file. One paragraph for each block, with
   a blank line between blocks.
2. Run `python3 tools/set_body.py <slug> <file>`. It prints the old and new
   word counts.
3. Add the slug to `tests/rewritten.txt` and run `./run_tests.sh`.
