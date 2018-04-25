# Creating a link
Let's assume, you work in the note "201710282120 The rise of the machines":

```markdown
# The rise of the machines
tags = #AI #world-domination

Machines are becoming more and more intelligent and powerful.

This might reach a point where they might develop a consciensce of their own.
```

You figure, a link to the "AI is going to kill us all" note is a good fit to expand on that aspect of the whole machine-rise story, so you want to place a link in there.

You start typing:

```markdown
# The rise of the machines
tags = #AI #world-domination

Machines are becoming more and more intelligent and powerful.

This might reach a point where they might develop a consciensce of their own.

As a consequence, they might turn evil and try to kill us all ........... [[
```

The moment you type `[[`, a list pops up with all the notes in your archive. You enter "kill" to narrow down the selection list and select the target note. Voila! You have just placed a link into your note, which now looks like this:

```markdown
# The rise of the machines
tags = #AI #world-domination

Machines are becoming more and more intelligent and powerful.

This might reach a point where they might develop a consciensce of their own.

As a consequence, they might turn evil and try to kill us all ........... [[201710282118]]
```

**Note:** Only files ending with the extension specified in the settings (`.md` by default) will be listed in the popup list. If your files end with `.txt`, you need to change this setting.

**Note:** With [this setting](#insert-links-with-or-without-titles) you can have the note's title inserted right after the link as well: `[[201710282118]] AI is going to kill us all`

If you now click into `[[201710282118]]`, the target note will be opened in a new tab where you can read up on how AI is potentially going to kill us all.

Here you can see what the list of notes to choose from looks like:

![screenshot2](https://user-images.githubusercontent.com/30892199/32403198-25f55650-c134-11e7-8f62-58fdbfb13c2b.png)

#### Implicitly creating a new note via a link
There is another way to create a new note: Just create a link containing its title and click it.

To showcase this, let's modify our example from above: Say, the "AI is going to kill us all" does **not** exist and you're in your "The rise of the machines" note.

This is what it might look like:

```markdown
# The rise of the machines
tags = #AI #world-domination

Machines are becoming more and more intelligent and powerful.

This might reach a point where they might develop a consciensce of their own.
```

You now want to branch into the new thought you just had, that AI might potentially eventually be going to kill us all. You prepare for that by mentioning it and inserting a link, like this:

```markdown
# The rise of the machines
tags = #AI #world-domination

Machines are becoming more and more intelligent and powerful.

This might reach a point where they might develop a consciensce of their own.

As a consequence, they might turn evil and try to kill us all ........... [[AI is going to kill us all]]
```

**Note:** You will have to press `[ESC]` after typing `[[` to get out of the note selection that pops up, before entering the note title.

**Note:** Of course this also works if you use a single quote link: `[AI is going to kill us all]`.

Now, in order to actually create the new note and its link, all you have to do is to click inside the new note's title, just as you would if you wanted to open a regular linked note.

And voila! A new note `201710282118 AI is going to kill us all.md` will be created and opened for you.

But the really cool thing is, that the link in the original note will be updated to the correct ID, so again you will end up with the following in the parent note:

```markdown
# The rise of the machines
tags = #AI #world-domination

Machines are becoming more and more intelligent and powerful.

This might reach a point where they might develop a consciensce of their own.

As a consequence, they might turn evil and try to kill us all ........... [[201710282118]]
```

**Note** how the note title "AI is going to kill us all" has been replaced by the note's ID "201710282118".

**Note:** With [this setting](#insert-links-with-or-without-titles) you can have the note's title inserted right after the link as well, like in : `[[201710282118]] AI is going to kill us all`

The new note will be pre-filled with the following text:

```markdown
# AI is going to kill us all
tags =
.
```

## Supported link styles
When inserting links manually, you are can choose between the following supported link styles:

```markdown
## Wiki Style
[[201711111707]] Ordinary double-bracket wiki-style links

## Wiki Style with title
[[201711111708 here goes the note's title]] same with title

## Old-School
§201711111709 support for old-school links :)

## Single-Pair
[201711111709] one pair of brackets is enough

## Single-Pair with title
[201711111709 one pair of brackets is enough]
```

