# -*- coding: utf-8 -*-
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.Qsci import *
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QObject

from themes import Theme
from mainwindow import MainWindow


class Sublimeless_Zk(QObject):
    def __init__(self, parent=None):
        QObject.__init__(self, parent=parent)
        self.app = None
        self.gui = None


    def init_actions(self):
        """
        { "caption": "ZK: New Zettel Note", "command": "zk_new_zettel" },
        { "caption": "ZK: Insert Citation", "command": "zk_insert_citation" },
        { "caption": "ZK: Pick tag from list", "command": "zk_tag_selector" },
        { "caption": "ZK: Find all tags in archive", "command": "zk_show_all_tags" },
        { "caption": "ZK: Expand Overview Note", "command": "zk_expand_overview_note" },
        { "caption": "ZK: Refresh Expanded Note", "command": "zk_refresh_expanded_note" },
        { "caption": "ZK: Expand Link inline", "command": "zk_expand_link" },
        { "caption": "ZK: Search for tag combination", "command": "zk_multi_tag_search" },
        { "caption": "ZK: Auto-Bib", "command": "zk_auto_bib" },
        { "caption": "ZK: Show Images", "command": "zk_show_images" },
        { "caption": "ZK: Hide Images", "command": "zk_hide_images" },
        { "caption": "ZK: Auto-TOC", "command": "zk_toc" },
        { "caption": "ZK: Number Headings", "command": "zk_renumber_headings" },
        { "caption": "ZK: Remove Heading Numbers", "command": "zk_denumber_headings" },
        { "caption": "ZK: Select Panes for opening notes/results", "command": "zk_select_panes" },
        { "caption": "ZK: Insert Link", "command": "zk_get_wiki_link" },
        { "caption": "ZK: Show all Notes", "command": "zk_show_all_notes" },
        { "caption": "ZK: Enter Zettelkasten Mode", "command": "zk_enter_zk_mode" },
        """
        self.newAction = QAction("New Zettel Note", self)
        self.newAction.setShortcuts(["Ctrl+N", "Shift+Return", "Shift+Enter"])
        self.newAction.triggered.connect(self.zk_new_zettel)

        self.insertLinkAction = QAction('Insert Link to Note', self)
        self.insertLinkAction.setShortcut('[,[')
        self.insertLinkAction.triggered.connect(self.insert_link)
        self.gui.editor.text_shortcut_handler.shortcut_insert_link.connect(self.insert_link)


        ## Editor shortcut overrides
        ##
        for editor in self.gui.editor, self.gui.saved_searches_editor, self.gui.search_results_editor:
            commands = editor.standardCommands()
            deletable_keys = (
                Qt.ShiftModifier | Qt.Key_Return, Qt.ControlModifier | Qt.Key_Return,
                Qt.ShiftModifier | Qt.Key_Enter, Qt.ControlModifier | Qt.Key_Enter,
                Qt.AltModifier | Qt.Key_Enter, Qt.AltModifier | Qt.Key_Return,

            )
            if sys.platform == 'darwin':
                deletable_keys = (
                    Qt.ShiftModifier | Qt.Key_Return, Qt.MetaModifier | Qt.Key_Return,
                    Qt.ShiftModifier | Qt.Key_Enter, Qt.MetaModifier | Qt.Key_Enter,
                    Qt.AltModifier | Qt.Key_Enter, Qt.AltModifier | Qt.Key_Return,
                )

            for key_combo in deletable_keys:
                command = commands.boundTo(key_combo)
                if command is not None:
                    print('Clearing key combo', key_combo, 'for command', command.description())
                    if command.key() == key_combo:
                        command.setKey(0)
                    elif command.alternateKey() == key_combo:
                        command.setAlternateKey(0)
                    print(command.key(), command.alternateKey())

        # todo: pack this into an action, too
        if sys.platform == 'darwin':
            shortcut = QShortcut(Qt.MetaModifier| Qt.Key_Return, self.gui)
        else:
            shortcut = QShortcut(Qt.ControlModifier | Qt.Key_Return, self.gui)
        shortcut.activated.connect(self.zk_follow_link)


    def initMenubar(self):
        menubar = self.gui.menuBar()

        file = menubar.addMenu("File")
        edit = menubar.addMenu("Edit")
        view = menubar.addMenu("View")
        about = menubar.addMenu("About")

        file.addAction(self.newAction)
        # file.addAction(self.newTabAction)
        # file.addAction(self.openAction)
        # file.addAction(self.saveAction)
        # file.addAction(self.saveasAction)
        # file.addSeparator()
        # file.addAction(self.fontAct)
        # file.addAction(self.dirAct)

        edit.addAction(self.insertLinkAction)
        # edit.addAction(self.undoAction)
        # edit.addAction(self.redoAction)
        # edit.addSeparator()
        # edit.addAction(self.copyAction)
        # edit.addAction(self.cutAction)
        # edit.addAction(self.pasteAction)
        # edit.addAction(self.FRAct)

        # view.addAction(self.treeAct)

        # about.addAction(self.aboutAction)

    def connect_signals(self):
        self.gui.lexer.tag_clicked.connect(self.clicked_tag)
        self.gui.lexer.note_id_clicked.connect(self.clicked_noteid)
        self.gui.search_results_editor.lexer().tag_clicked.connect(self.clicked_tag)
        self.gui.search_results_editor.lexer().note_id_clicked.connect(self.clicked_tag)
        self.gui.saved_searches_editor.lexer().tag_clicked.connect(self.clicked_tag)
        self.gui.saved_searches_editor.lexer().note_id_clicked.connect(self.clicked_tag)
        self.gui.qtabs.tabCloseRequested.connect(self.gui.qtabs.removeTab)
        self.gui.qtabs.tabCloseRequested.connect(self.lessTabs)

    def run(self):
        self.app = QApplication(sys.argv)
        QApplication.setStyle(QStyleFactory.create('Fusion'))
        theme = Theme('../themes/solarized_light.json')
        self.gui = MainWindow(theme)
        self.gui.setFocus()
        self.init_actions()
        self.initMenubar()
        self.connect_signals()
        sys.exit(self.app.exec_())

    #
    # Qt SLOTS
    #
    def clicked_noteid(self, noteid, ctrl, alt, shift):
        print('noteid', noteid, ctrl, alt, shift)

    def clicked_tag(self, tag, ctrl, alt, shift):
        print('tag', tag)

    def lessTabs(self):
        pass

    #
    # Zettelkasten Command Slots
    #

    def zk_new_zettel(self):
        print('New Zettel')

    def zk_follow_link(self):
        print('Follow Link', end=' ')
        if self.app.focusWidget() == self.gui.editor:
            print('from main editor')
        elif self.app.focusWidget() == self.gui.search_results_editor:
            print('from results editor')
        elif self.app.focusWidget() == self.gui.saved_searches_editor:
            print('from search editor')
        else:
            print('irrelevant')

    def insert_link(self):
        print('Insert Link')

if __name__ == '__main__':
    Sublimeless_Zk().run()


