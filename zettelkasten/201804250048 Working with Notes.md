# Working with notes

See also [[201804250052]] Creating a Link.

## Note Archive Folder

When you first start the app, it creates a `zettelkasten` folder in your home / user directory. On Windows, this is typically `C:\Users\your.username\`, on macOS it is typically `/Users/your.username/`, and on Linux it usually is `/home/your.username/`.

This `zettelkasten` folder comes with one or more default notes to get you started.

If you have an existing note archive already, you can switch to it with <kbd>ctrl</kbd>+<kbd>O</kbd>, or use the File > Open... menu.

The app keeps track of up to 10 recently opened note archive folders, which are accessible at the bottom of the File menu.


## Creating a new note

* Press `[shift]+[enter]`. This will prompt you for the title of the new note.
* Press `[ESC]` to cancel without creating a new note.
* Enter the note title and press `[enter]`.

A new note will be created and assigned the timestamp based ID in the format described above.

Example: Let's say you entered "AI is going to kill us all" as the note title, then a file with the name `201710282118 AI is going to kill us all.md` will be created and opened for you.

The new note will look like this:

```markdown
# AI is going to kill us all
tags =
.
```

## Creating a new note and link from selected text

There is a very convenient shortcut to create notes from selected text and automatically inserting a link to the new note, replacing the selected text: Just select the text you want to use as note title before pressing `[shift]+[enter]`.

This will bring up the same input field at the bottom of the window, this time pre-filled with the selected text. When you press `[enter]`, a new note will be created, using the selected text as its title. In addition, the selected text in the original note will be replaced by a link to the new note.

As a bonus feature, you can even select multiple lines and create a new note complete with title and body:

* the first selected line will become the note's title
* all the other selected lines will become the note's body (text).
