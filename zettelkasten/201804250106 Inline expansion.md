### Inline expansion of note-links

Overview note expansion is cool, but there are situations where you might not want to expand all links of a note but just a few. Also, since expansion does not descend into links of expanded notes, you might want to manually expand those.

Manually expanding a note link is easy: You must have your cursor in a note link, obiously. The key combination `[ctrl]+[.]` or `Expand Link inline` from the edit menu will then trigger the expansion. In contrast to the expansion method for overview notes in the previous section, the line containing the link will be preserved.

Here is an example using the already well-known AI notes: Let's start with our first note:

```markdown
# The rise of the machines
tags = #AI #world-domination

Machines are becoming more and more intelligent and powerful.

This might reach a point where they might develop a consciensce of their own.

As a consequence, they might turn evil and try to kill us all ........... [[201710282118]]
```

Now if you put your cursor inside the `[[201710282118]]` link and press `[ctrl]+[.]`, the text will change into this:

```markdown
# The rise of the machines
tags = #AI #world-domination

Machines are becoming more and more intelligent and powerful.

This might reach a point where they might develop a consciensce of their own.

As a consequence, they might turn evil and try to kill us all ........... [[201710282118]]

<!-- !    [[201710282118]] AI is going to kill us all    -->
# AI is going to kill us all
tags =

<!-- (End of note 201710282118) -->
```

*(We've never actually written anything into the linked note. Usually there would be lots of text)*

**Note:** To remember `[ctrl]+[.]`: I wanted to use `...` as shortcut for expansion but it didn't work out :smile:

**Hint:** If, after expansion, you don't like what you see, just undo! :smile:

**Note:** Use this at your own risk when **ever** planning on refreshing an overview note. You are going to have nested expansions and precisely those will get overwritten when the parent note is refreshed.

### Inline expansion of #tags
Another workflow for producing overview notes is by #tag. So if you want to produce an overview note referencing all notes tagged by a single tag, just press `[ctrl]+[.]` while the cursor is inside a #tag. This will produce a **bulleted list** of notes tagged with the #tag.


### Inline expansion of citekeys
In order to produce an outline of all notes citing a specific source, just press `[ctrl]+[.]` while the cursor is inside a *citekey*. This will produce a **bulleted list** of notes containing a reference to the *citekey*.

**Note:** This works with `@pandoc` and `#multimarkdown` style citation keys and is independent of whether the citekey is part of an actual citation (`[@citekey]` or `[][#citekey]`) or just occurs in your text as `@citekey` or `#citekey`.
