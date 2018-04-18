from PyQt5.QtCore import QObject, pyqtSignal
from time import time
from PyQt5.QtCore import Qt


class EditorTextShortCutHandler(QObject):
    """
    { "keys": ["[", "["], "command": "zk_get_wiki_link"},
    { "keys": ["#", "?"], "command": "zk_tag_selector"},
    { "keys": ["#", "!"], "command": "zk_show_all_tags"},
    { "keys": ["ctrl+."], "command": "zk_expand_link"},
    { "keys": ["[", "@"], "command": "zk_insert_citation"},
    { "keys": ["[", "#"], "command": "zk_insert_citation"},
    { "keys": ["[", "!"], "command": "zk_show_all_notes"},
    """
    shortcut_insert_link = pyqtSignal(int)   # text position
    shortcut_tag_selector = pyqtSignal(int)
    shortcut_tag_list = pyqtSignal(int)
    # shortcut_expand_link = pyqtSignal(int)
    shortcut_insert_citation = pyqtSignal(int)
    shortcut_all_notes = pyqtSignal(int)

    def __init__(self, parent=None):
        QObject.__init__(self, parent=parent)

        # special shortcuts that cannot be implemented by un-binding QsciCommands
        self.time_since = {'[': 0, '#': 0}
        self.time_threshold = 1.5  # seconds

        self.shortcut_map = {
            '[': {
                '[': self.shortcut_insert_link,
                '@': self.shortcut_insert_citation,
                '#': self.shortcut_insert_citation,
                '!': self.shortcut_all_notes
            },
            '#': {
                '?': self.shortcut_tag_selector,
                '!': self.shortcut_tag_list
            }
        }
        self.leader_received = None

    def keyPressEvent(self, event):
        current_char = event.text()
        if not current_char:
            # shift, etc
            return

        time_now = time()
        if self.leader_received:
            time_then = self.time_since[self.leader_received]
            time_since = time_now - time_then
            if time_since <= self.time_threshold:
                shortcuts = self.shortcut_map[self.leader_received]
                if current_char in shortcuts:
                    signal = shortcuts[current_char]
                    editor = self.parent()
                    line, index = editor.getCursorPosition()
                    textpos = editor.positionFromLineIndex(line, index)
                    signal.emit(textpos)
                    print(self.leader_received+current_char, '@', textpos)
            # clear leader in any case
            self.leader_received = None

        if current_char in self.shortcut_map:
            self.time_since[current_char] = time()
            self.leader_received = current_char
