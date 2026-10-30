# Sources and licensing of the data files

## What the texts are

| Field | Source |
|---|---|
| Hexagram `judgment` and line `text` | James Legge, *The Yi King*, Sacred Books of the East vol. XVI (Oxford, 1882): "The Text", one section per hexagram. |
| Hexagram `image` | The same volume, Appendix II (the *Xiang Zhuan*, "Great Symbolism"): the paragraph for that hexagram. |
| `commentary` on hexagrams 1 and 2 | Legge's Text: the extra statement for when all six lines are nines (1) or all are sixes (2). |
| Trigram `attribute`, `image`, `family` | The same volume, Appendix V (the *Shuo Gua*), chapters 7 to 11. |
| Chinese characters, pinyin, Unicode symbols, binaries | Standard reference facts, not copyrightable. Binaries were derived from the trigram pairs and checked by `tests/test_book.py`. |

Legge's translation was published in 1882 and is in the **public domain**. No modern
translation was used, in particular not the Wilhelm/Baynes translation, which is still under
copyright.

The texts were worked from public-domain copies of the 1882 edition: the archive.org scans
(items `sacredbooksoftheeastvol16_202002` and `wg916`), Wikisource's transcription of
SBE vol. 16, and the Wayback Machine copy of sacred-texts.com's transcription.

## How the texts were edited

Light modernisation only. Each judgment, image and line still says what Legge's does.

- Legge's romanised hexagram names ("Khien", "Khwan", …) are dropped. The text says "this
  hexagram" or uses an English gloss of the name.
- Legge's bracketed interpolations are removed. Where the sentence needs the bracketed words,
  they stay without brackets.
- Line statements open with the conventional label ("Nine at the beginning:", "Six in the
  second place:", … "Nine at the top:") instead of Legge's "The first line, undivided,
  shows…". Nine marks a yang line and Six a yin line. The tests check every label against the
  figure.
- Spelling and punctuation are modernised in places ("waggon" → "wagon").
- "The superior man" is kept as Legge has it.

## Names

The English `name` of each hexagram is a short conventional rendering. Where the text names the
hexagram (most of 17–64), the `name` matches the gloss used in the text, which is drawn from
Legge's own renderings ("Overthrowing", "Long Continuance", "The Caldron"). Short titles are not
subject to copyright.

## Licence of this file set

The underlying texts are public domain. The editing in `hexagrams.json` and `trigrams.json` is
released under this project's MIT licence.
