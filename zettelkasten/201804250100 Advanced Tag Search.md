#### Advanced Tag Search

To search for more sophisticated tag combinations, use the command `Search for Tag Combination` (Control + T) from the search menu.

It will prompt you for the tags you want to search for and understands quite a powerful syntax; let's walk through it:

##### Grammar and Syntax

```
search-spec: search-term [, search-term]*
search-term: tag-spec [ tag-spec]*
tag-spec: [!]#tag-name[*]
tag-name: {any valid tag string}
```

**What does that mean?**

* _search-spec_ consist of one or more _search-terms_ that are separated by comma
* each _search-term_ consists of one or more _tag-specs_
* each _tag-spec_
    * can be:
        * `#tag  ` : matches notes tagged with `#tag`
        * `!#tag ` : matches all results that are **not** tagged with `#tag`
    * and optionally be followed by an `*` asterisk to change the meaning of `#tag`
        * from *exact* `#tag`
        * to tags *starting with* `#tag`

**How does this work?**

* Each search is performed in the order the *search-terms* are specified.
    * With each *search-term* the results can be narrowed down.
    * This is equivalent to a logical _AND_ operation
    * Example: `#car, #diesel` will first search for `#car` and then narrow all `#car` matches down to those also containing `#diesel`.
        * This is equivalent to `#car` _AND_ `#diesel`.
* Each *tag-spec* in a *search-term* adds to the results of that *search-term*.
    * This is equivalent to a logical _OR_ operation.
    * Example: `#car #plane` will match everything tagged with `#car` and also everything tagged with `#plane`
        * This is equivalent to `#car` _OR_ `#plane`.
* Each *tag-spec* can contain an `*` asterisk placeholder to make `#tag*` stand for *all tags starting with `#tag`*
    * This works for `#tag*` and `!#tag*`.
    * Examples:
        * `#car*` : will match everything that contains tags starting with `#car`, such as: `#car`, `#car-manufacturer`, etc.
        * `!#car*` : will match all results that do **not** contain tags starting with `#car`:
            * `#plane #car-manufacturer` will be thrown away
            * `#submarine` will be kept

##### Putting it all together

Examples:

`#transport !#car` : all notes with transport **+** all notes not containing car (such as `#plane`)

There is no comma. Hence, two search terms will be evaluated and the results of all of them will be combined (_OR_).

`#transport, !#car`: all notes with transport **-** all notes containing car

Here, there is a comma. So first all notes tagged with `#transport` will be searched and of those only the ones that are not tagged with `#car` will be kept (_AND_).

Pretty powerful.

`#transport #car, !#plane` : `#transport` or `#car` but never `#plane`

`#transport #car !#plane` : `#transport` or `#car` or anything else that's not `#plane`

I omitted examples using the `*` placeholder, it should be pretty obvious.
