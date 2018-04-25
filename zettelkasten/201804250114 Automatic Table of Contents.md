#### Automatic Table Of Contents
Some notes can get quite long, especially when turning overview notes into growing documents. At some stage it might make sense to introduce a table of contents into the text. This can be useful when using some Markdown Preview app to quickly check your text in a browser.

To insert a table of contents at your current cursor position:

* from the edit menu select `Insert Table of Contents`
* press <kbd>Control</kbd> + <kbd>Shift</kbd> + <kbd>T</kbd>

The table of contents will be placed between two automatically generated comments that also serve as markers for the app. It will consist of a bulleted list consisting of links to the headings in your text. The links are only relevant when converting your text into HTML.

Why a bulleted list and not a numbered one? You might have numbered the sections yourself. Numbered lists would get in the way in that case. Also, numbered lists produce `ii.` instead of `1.2` when nesting them.

Example before TOC:

```markdown
# 201711250024 Working with tocs
tags = #sublime_zk #toc


## This is a very long note!
At least we pretend so.

## It contains many headings
That's why we are going to need a table of contents.

### **with funny chäråcters!**
Funny characters can be a challenge in the `(#references)`.

## as can duplicate headings

# as can duplicate headings
.
```

Example after TOC:

```markdown
# 201711250024 Working with tocs
tags = #sublime_zk #toc

<!-- table of contents (auto) -->
* [201711250024 Working with tocs](#201711250024-working-with-tocs)
    * [This is a very long note!](#this-is-a-very-long-note)
    * [It contains many headings](#it-contains-many-headings)
        * [**with funny chäråcters!**](#with-funny-characters)
    * [as can duplicate headings](#as-can-duplicate-headings)
* [as can duplicate headings](#as-can-duplicate-headings_1)
<!-- (end of auto-toc) -->

## This is a very long note!
At least we pretend so.

## It contains many headings
That's why we are going to need a table of contents.

### **with funny chäråcters!**
Funny characters can be a challenge in the `(#references)`.

## as can duplicate headings

# as can duplicate headings
.
```

**Note:** Whenever you need to refresh the table of contents, just repeat the above command.

**Note:** You can configure the separator used to append a numerical suffix for making references to duplicate headers distinct: by changing the `toc_suffix_separator` in the settings. It is set to an underscore by default (*markdown preview*, parsers based on Python's *markdown* module). If you use [pandoc](https://pandoc.org/), you should set it to `-`.
