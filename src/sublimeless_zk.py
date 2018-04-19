# -*- coding: utf-8 -*-
import os
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.Qsci import *
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QObject

from themes import Theme
from mainwindow import MainWindow
from settings import SettingsEditor


class Sublimeless_Zk(QObject):
    def __init__(self, parent=None):
        QObject.__init__(self, parent=parent)
        self.app = None
        self.gui = None
        self.open_documents = []
        self.tabindex2editor = {}
        self.tabindex2filn = {}
        self.doc2tabindex = {}
        self.num_tabs = 0        # maybe redundant
        self.editors = []

    def init_actions(self):
        self.newAction = QAction("New Zettel Note", self)
        self.newAction.setShortcuts(["Ctrl+N", "Shift+Return", "Shift+Enter"])

        self.openFolderAction = QAction('Open Notes Folder', self)
        self.openFolderAction.setShortcut('Ctrl+O')

        self.saveAction = QAction("Save", self)
        self.saveAction.setShortcut('Ctrl+S')

        self.saveAllAction = QAction("Save All", self)
        self.saveAllAction.setShortcut('Ctrl+Alt+S')

        self.showPreferencesAction = QAction("Settings...", self)

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

        ## Editor shortcut overrides
        ##
        editor_list = self.editors[:]
        editor_list.extend([self.gui.saved_searches_editor, self.gui.search_results_editor])
        for editor in editor_list:
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
        file.addAction(self.openFolderAction)
        file.addAction(self.saveAction)
        file.addAction(self.saveAllAction)
        file.addSeparator()
        # here go the most recents

        edit.addAction(self.insertLinkAction)
        edit.addAction(self.showReferencingNotesAction)
        edit.addAction(self.insertTagAction)
        edit.addAction(self.expandLinkAction)
        edit.addAction(self.insertCitationAction)
        edit.addAction(self.autoBibAction)
        edit.addAction(self.autoTocAction)
        edit.addAction(self.numberHeadingsAction)
        edit.addAction(self.denumberHeadingsAction)
        edit.addAction(self.showPreferencesAction)

        # edit.addAction(self.undoAction)
        # edit.addAction(self.redoAction)
        # edit.addSeparator()
        # edit.addAction(self.copyAction)
        # edit.addAction(self.cutAction)
        # edit.addAction(self.pasteAction)

        view.addAction(self.showAllNotesAction)
        view.addAction(self.showTagsAction)
        view.addAction(self.showImagesAction)
        view.addAction(self.hideImagesAction)

        tools.addAction(self.expandOverviewNoteAction)
        tools.addAction(self.refreshExpandedNoteAction)
        tools.addAction(self.advancedTagSearchAction)

        # about.addAction(self.aboutAction)

    def connect_signals(self):
        # tab actions
        self.gui.qtabs.tabCloseRequested.connect(self.gui.qtabs.removeTab)
        self.gui.qtabs.tabCloseRequested.connect(self.lessTabs)

        # normal actions
        self.newAction.triggered.connect(self.zk_new_zettel)
        self.openFolderAction.triggered.connect(self.open_folder)
        self.saveAction.triggered.connect(self.save)
        self.saveAllAction.triggered.connect(self.save_all)
        self.showPreferencesAction.triggered.connect(self.show_preferences)
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

        # editor actions
        self.gui.search_results_editor.lexer().tag_clicked.connect(self.clicked_tag)
        self.gui.search_results_editor.lexer().note_id_clicked.connect(self.clicked_tag)
        self.gui.saved_searches_editor.lexer().tag_clicked.connect(self.clicked_tag)
        self.gui.saved_searches_editor.lexer().note_id_clicked.connect(self.clicked_tag)

    def connect_editor_signals(self, editor):
        # text shortcut actions
        # lexer actions
        editor.lexer().tag_clicked.connect(self.clicked_tag)
        editor.lexer().note_id_clicked.connect(self.clicked_noteid)
        editor.text_shortcut_handler.shortcut_insert_link.connect(self.insert_link)
        editor.text_shortcut_handler.shortcut_tag_selector.connect(self.insert_tag)
        editor.text_shortcut_handler.shortcut_tag_list.connect(self.show_all_tags)
        editor.text_shortcut_handler.shortcut_insert_citation.connect(self.insert_citation)
        editor.text_shortcut_handler.shortcut_all_notes.connect(self.show_all_notes)
        editor.textChanged.connect(self.unsaved)


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

    def unsaved(self):
        tab_index = self.gui.qtabs.currentIndex()
        editor = self.tabindex2editor[tab_index]
        if editor.isModified():
            self.gui.qtabs.setTabText(tab_index, os.path.basename(self.tabindex2filn[tab_index]) + '*')

    #
    # Zettelkasten Command Slots
    #

    def get_active_editor(self):
        """
        Helper function to find out where the keyboard input focus is
        """
        if self.app.focusWidget() == self.gui.editor:
            return self.gui.editor
        elif self.app.focusWidget() == self.gui.search_results_editor:
            return self.gui.search_results_editor
        elif self.app.focusWidget() == self.gui.saved_searches_editor:
            return self.gui.saved_searches_editor
        else:
            return None

    def open_document(self, document_filn, is_settings_file=False):
        """
        Helper function to open a markdown or settings document in a new tab
        """
        if document_filn in self.doc2tabindex:
            tab_index = self.doc2tabindex[document_filn]
            self.gui.qtabs.setCurrentIndex(tab_index)
            return
        # make new editor from file

        if is_settings_file:
            settings = SettingsEditor(self.gui.theme, document_filn)
            editor = settings.editor
        else:
            editor = self.gui.new_zk_editor(document_filn)
        document_name = os.path.basename(document_filn)
        self.gui.qtabs.addTab(editor, document_name)
        self.doc2tabindex[document_filn] = self.num_tabs
        self.tabindex2filn[self.num_tabs] = document_filn
        self.editors.append(editor)
        self.tabindex2editor[self.num_tabs] = editor
        editor.setModified(False)
        if is_settings_file:
            editor.textChanged.connect(self.unsaved)
        else:
            self.connect_editor_signals(editor)
        self.num_tabs += 1
    ''''''

    def show_preferences(self):
        self.open_document('../settings_default.json', is_settings_file=True)






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

    def open_folder(self):
        """
        todo: Call Save All first or sth like that
        """
        pass

    def save(self):
        pass

    def save_all(self):
        pass


if __name__ == '__main__':
    Sublimeless_Zk().run()


