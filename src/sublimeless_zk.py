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
        self.newAction = QAction("New Zettel Note", self)
        self.newAction.setShortcuts(["Ctrl+N", "Shift+Return", "Shift+Enter"])

        self.insertLinkAction = QAction('Insert Link to Note', self)
        self.insertLinkAction.setShortcut('[,[')

        self.showReferencingNotesAction = QAction('Show referencing notes', self)
        self.showReferencingNotesAction.setShortcut('Alt+Enter')

        self.insertTagAction = QAction('Insert Tag', self)
        self.insertTagAction.setShortcut('#, ?')

        self.showTagsAction = QAction('Show all Tags', self)
        self.showTagsAction.setShortcut('#,!')

        self.expandLinkAction = QAction('Expand link', self)
        self.expandLinkAction.setShortcut('Ctrl+.')
        if sys.platform == 'darwin':
            self.expandLinkAction.setShortcut('Meta+.')

        self.insertCitationAction = QAction('Insert Citation', self)
        self.insertCitationAction.setShortcuts(['[,@', '[,#'])

        self.expandOverviewNoteAction = QAction('Expand Overview Note', self)
        self.expandOverviewNoteAction.setShortcut('Ctrl+E')

        self.refreshExpandedNoteAction = QAction('Refresh expanded Note', self)
        self.refreshExpandedNoteAction.setShortcut('Ctrl+R')

        self.advancedTagSearchAction = QAction('Search for tag combination', self)
        self.advancedTagSearchAction.setShortcut('Ctrl+T')

        self.autoBibAction = QAction('Insert Bibliography', self)
        self.autoBibAction.setShortcut('Ctrl+B')

        self.showImagesAction = QAction('Show Images', self)
        self.showImagesAction.setShortcut('Shift+Ctrl+I')

        self.hideImagesAction = QAction('Hide Images', self)
        self.hideImagesAction.setShortcut('Shift+Ctrl+H')

        self.autoTocAction = QAction('Insert Table of Contents', self)
        self.autoTocAction.setShortcut('Shift+Ctrl+T')

        self.numberHeadingsAction = QAction('Insert Section Numbers', self)
        self.numberHeadingsAction.setShortcut('Ctrl+Shift+I')

        self.denumberHeadingsAction = QAction('Remove Section Numbers', self)
        self.denumberHeadingsAction.setShortcut('Ctrl+Shift+R')

        self.showAllNotesAction = QAction('Show all Notes', self)
        self.showAllNotesAction.setShortcut('[,!')

        """
        { "caption": "ZK: Auto-TOC", "command": "zk_toc" },
        { "caption": "ZK: Number Headings", "command": "zk_renumber_headings" },
        { "caption": "ZK: Remove Heading Numbers", "command": "zk_denumber_headings" },
        { "caption": "ZK: Show all Notes", "command": "zk_show_all_notes" },
        """





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
        tools = menubar.addMenu('Tools')
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
        edit.addAction(self.showReferencingNotesAction)
        edit.addAction(self.insertTagAction)
        edit.addAction(self.expandLinkAction)
        edit.addAction(self.insertCitationAction)
        edit.addAction(self.autoBibAction)
        edit.addAction(self.autoTocAction)
        edit.addAction(self.numberHeadingsAction)
        edit.addAction(self.denumberHeadingsAction)

        # edit.addAction(self.undoAction)
        # edit.addAction(self.redoAction)
        # edit.addSeparator()
        # edit.addAction(self.copyAction)
        # edit.addAction(self.cutAction)
        # edit.addAction(self.pasteAction)
        # edit.addAction(self.FRAct)

        view.addAction(self.showAllNotesAction)
        view.addAction(self.showTagsAction)
        view.addAction(self.showImagesAction)
        view.addAction(self.hideImagesAction)

        tools.addAction(self.expandOverviewNoteAction)
        tools.addAction(self.refreshExpandedNoteAction)
        tools.addAction(self.advancedTagSearchAction)

        # about.addAction(self.aboutAction)

    def connect_signals(self):
        # lexer actions
        self.gui.lexer.tag_clicked.connect(self.clicked_tag)
        self.gui.lexer.note_id_clicked.connect(self.clicked_noteid)
        self.gui.search_results_editor.lexer().tag_clicked.connect(self.clicked_tag)
        self.gui.search_results_editor.lexer().note_id_clicked.connect(self.clicked_tag)
        self.gui.saved_searches_editor.lexer().tag_clicked.connect(self.clicked_tag)
        self.gui.saved_searches_editor.lexer().note_id_clicked.connect(self.clicked_tag)

        # tab actions
        self.gui.qtabs.tabCloseRequested.connect(self.gui.qtabs.removeTab)
        self.gui.qtabs.tabCloseRequested.connect(self.lessTabs)

        # normal actions
        self.newAction.triggered.connect(self.zk_new_zettel)
        self.insertLinkAction.triggered.connect(self.insert_link)
        self.showReferencingNotesAction.triggered.connect(self.show_referencing_notes)
        self.insertTagAction.triggered.connect(self.insert_tag)
        self.showTagsAction.triggered.connect(self.show_all_tags)
        self.expandLinkAction.triggered.connect(self.expand_link)
        self.insertCitationAction.triggered.connect(self.insert_citation)
        self.expandOverviewNoteAction.triggered.connect(self.expand_overview_note)
        self.refreshExpandedNoteAction.triggered.connect(self.refresh_expanded_note)
        self.advancedTagSearchAction.triggered.connect(self.advanced_tag_search)
        self.autoBibAction.triggered.connect(self.auto_bib)
        self.showImagesAction.triggered.connect(self.show_images)
        self.hideImagesAction.triggered.connect(self.hide_images)
        self.autoTocAction.triggered.connect(self.auto_toc)
        self.numberHeadingsAction.triggered.connect(self.number_headings)
        self.denumberHeadingsAction.triggered.connect(self.denumber_headings)
        self.showAllNotesAction.triggered.connect(self.show_all_notes)

        # text shortcut actions
        self.gui.editor.text_shortcut_handler.shortcut_insert_link.connect(self.insert_link)



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

    def show_referencing_notes(self):
        print('Show referencing note')

    def insert_tag(self):
        print('insert tag')

    def show_all_tags(self):
        print('show all tags')

    def expand_link(self):
        print('expand link')

    def insert_citation(self):
        print('insert citation')

    def show_all_notes(self):
        print('show all notes')

    def expand_overview_note(self):
        print('expand overview note')

    def refresh_expanded_note(self):
        pass

    def advanced_tag_search(self):
        pass

    def auto_bib(self):
        pass

    def show_images(self):
        pass

    def hide_images(self):
        pass

    def auto_toc(self):
        pass

    def number_headings(self):
        pass

    def denumber_headings(self):
        pass

    def show_all_notes(self):
        pass

if __name__ == '__main__':
    Sublimeless_Zk().run()


