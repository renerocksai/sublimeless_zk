### Working with Bibliographies

#### Inserting a citation
If your note archive contains one or you [configured](#location-of-your-bib-file) a `.bib` file, then you can use the shortcut `[@` or `[#` to insert a citation. Which one you use depends on your preferences, whether your prefer pandoc or multimarkdown.

A fuzzy-searchable list of all entries in your bibfile will pop up, containing authors, year, title, and citekey. To select the entry you like, just press `[enter]`. To exit without selecting anything, press `[esc]`.

When you made your choice, a citation link will be inserted into the text: `[@citekey]` (or `[][#citekey]` if you [use MultiMarkdown style](#citation-reference-style)).



#### Automatic Bibliographies
It is common practice to keep local bibliographies in your notes. This makes each note self-contained and independent of `.bib` files. Manually maintaining a list of all your cited sources can be tedious and error-prone, especially in the case of long notes with many citations. Provided a `.bib` file is part of your note archive or you have [configured](#location-of-your-bib-file) one, then this app can take care of all your citations for you.

**Note:** This will only work if you have `pandoc` and its companion `pandoc-citeproc` installed in a location that is referenced by your `PATH` environment variable! See the [how to install pandoc](https://pandoc.org/installing.html), it's a breeze.

In any note with citations

* pick `Insert Bibliography` from the edit menu
* press <kbd>Control</kbd> + <kbd>B</kbd>

This will add a long comment to your note in the following format *(line wrapping added for github manually)*:

```markdown
<!-- references (auto)

[@AhrensHowTakeSmart2017]: Ahrens, Sönke. 2017. _How to Take Smart Notes: One Simple Technique
to Boost Writing, Learning and Thinking for Students, Academics and Nonfiction Book Writers_. 1st ed.
CreateSpace Independent Publishing Platform.

[@FastZettelkastenmethodeKontrollieredein2015]: Fast, Sascha, and Christian Tietze. 2015.
_Die Zettelkastenmethode: Kontrolliere dein Wissen_. CreateSpace Independent Publishing Platform.

-->
```


**Note:** You don't have to cite in the `[@pandoc]` notation. If a cite-key is in your text, it will get picked up. However, the generated references section will use the `[@pandoc]` notation, except if you set [change the setting](#citation-reference-style) `citations-mmd-style` to `true`, then the `[#citekey]: ...` MultiMarkdown notation will be used.

**WARNING**: Do not write below the generated bibliography. Everything after `<!-- references (auto)` will be replaced when you re-run the command!

#### Searching for notes referencing a specific citekey

In order to be able to search for all notes citing the same source, just like note-links and #tags, **citation keys** can also be "followed" by clicking them.

**Note:** This works with `@pandoc` and `#multimarkdown` style citation keys and is independent of whether the citekey is part of an actual citation (`[@citekey]` or `[][#citekey]`) or just occurs in your text as `@citekey` or `#citekey`.

