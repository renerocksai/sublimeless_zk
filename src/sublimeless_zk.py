# -*- coding: utf-8 -*-
import os
import sys
import traceback
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.Qsci import *
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QObject, QTimer
import re
import unicodedata
from collections import Counter
import time

from themes import Theme
from mainwindow import MainWindow
from settingseditor import SettingsEditor
from project import Project
from appstate import AppState
from zkscintilla import ZettelkastenScintilla
from inputpanel import show_input_panel
from fuzzypanel import show_fuzzy_panel
from autobib import Autobib
from textproduction import TextProduction
from tagsearch import TagSearch
from imagehandler import ImageHandler
from settings import settings_filn, base_dir, get_settings, get_pandoc
from about import AboutDlg
from findandreplace import FindDlg


class Sublimeless_Zk(QObject):
    def __init__(self, parent=None):
        QObject.__init__(self, parent=parent)
        self.app = None
        self.gui = None
        self.app_state = AppState()
        self.project = Project(self.app_state.recent_projects[-1])
        self._show_images_disabled = True and getattr(sys, 'frozen', False)
        self.recent_projects_limit = 10
        self.recent_projects_actions = []
        self.autosave_timer = QTimer()
        self.time_since_last_autosave = 0
        self.autosave_interval = get_settings().get('auto_save_interval', 0)

    def on_timer(self):
        if not self.autosave_interval:
            return
        time_now = time.time()
        if time_now > self.time_since_last_autosave + self.autosave_interval:
            self.time_since_last_autosave = time_now
            self.save_all()
        return


    def init_actions(self):
        self.aboutAction = QAction('About Sublimeless Zettelkasten', self)
        self.findReplaceAction = QAction('Find/replace...', self)
        self.findReplaceAction.setShortcut('Ctrl+F')
        self.findInFilesAction = QAction('Find in files...', self)
        self.findInFilesAction.setShortcut('Shift+Ctrl+F')

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
        self.showReferencingNotesAction.setShortcuts(['Alt+Return', 'Alt+Enter'])

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

        if not self._show_images_disabled:
            self.showImagesAction = QAction('Show Images', self)
            self.showImagesAction.setShortcut('Shift+Ctrl+I')

            self.hideImagesAction = QAction('Hide Images', self)
            self.hideImagesAction.setShortcut('Shift+Ctrl+H')

        self.autoTocAction = QAction('Insert Table of Contents', self)
        self.autoTocAction.setShortcut('Shift+Ctrl+T')

        self.numberHeadingsAction = QAction('Insert Section Numbers', self)
        self.numberHeadingsAction.setShortcut('Ctrl+Shift+N')

        self.denumberHeadingsAction = QAction('Remove Section Numbers', self)
        self.denumberHeadingsAction.setShortcut('Ctrl+Shift+R')

        self.showAllNotesAction = QAction('Show all Notes', self)
        self.showAllNotesAction.setShortcut('[,!')

        self.copyAction = QAction('Copy', self)
        self.copyAction.setShortcut('Ctrl+C')
        self.pasteAction = QAction('Paste', self)
        self.pasteAction.setShortcut('Ctrl+V')
        self.cutAction = QAction('Cut', self)
        self.cutAction.setShortcut('Ctrl+X')
        self.undoAction = QAction('Undo', self)
        self.undoAction.setShortcut('Ctrl+Z')
        self.redoAction = QAction('Redo', self)
        self.redoAction.setShortcut('Shift+Ctrl+Z')

        # Recent folders actions
        for i in range(self.recent_projects_limit):
            self.recent_projects_actions.append(
                QAction(self, visible=False,
                        triggered=self.open_recent_project)
            )

        ## Editor shortcut overrides
        ##
        editor_list = [self.gui.qtabs.widget(i) for i in range(self.gui.qtabs.count())]
        editor_list.extend([self.gui.saved_searches_editor, self.gui.search_results_editor])
        [self.connect_editor_signals(editor) for editor in editor_list]

        # todo: pack this into an action, too
        if sys.platform == 'darwin':
            shortcut = QShortcut(Qt.MetaModifier| Qt.Key_Return, self.gui)
        else:
            shortcut = QShortcut(Qt.ControlModifier | Qt.Key_Return, self.gui)
        shortcut.activated.connect(self.zk_follow_link)

    def initMenubar(self):
        menubar = self.gui.menuBar()

        self.file_menu = menubar.addMenu("File")
        edit = menubar.addMenu("Edit")
        find = menubar.addMenu("Search")
        view = menubar.addMenu("View")
        tools = menubar.addMenu('Tools')
        about = menubar.addMenu("About")

        self.file_menu.addAction(self.newAction)
        # file.addAction(self.newTabAction)
        self.file_menu.addAction(self.openFolderAction)
        self.file_menu.addAction(self.saveAction)
        self.file_menu.addAction(self.saveAllAction)
        self.file_menu.addSeparator()
        # here go the most recents
        for i in range(self.recent_projects_limit):
            self.file_menu.addAction(self.recent_projects_actions[i])
        self.update_recent_project_actions()

        edit.addAction(self.undoAction)
        edit.addAction(self.redoAction)
        edit.addSeparator()
        edit.addAction(self.copyAction)
        edit.addAction(self.cutAction)
        edit.addAction(self.pasteAction)
        edit.addSeparator()
        edit.addAction(self.insertLinkAction)
        edit.addAction(self.insertTagAction)
        edit.addAction(self.expandLinkAction)
        edit.addAction(self.insertCitationAction)
        edit.addAction(self.autoBibAction)
        edit.addAction(self.autoTocAction)
        edit.addAction(self.numberHeadingsAction)
        edit.addAction(self.denumberHeadingsAction)
        edit.addAction(self.showPreferencesAction)

        find.addAction(self.findReplaceAction)
        find.addAction(self.findInFilesAction)
        find.addAction(self.advancedTagSearchAction)

        view.addAction(self.showAllNotesAction)
        view.addAction(self.showReferencingNotesAction)
        view.addAction(self.showTagsAction)


        if not self._show_images_disabled:
            view.addAction(self.showImagesAction)
            view.addAction(self.hideImagesAction)

        tools.addAction(self.expandOverviewNoteAction)
        tools.addAction(self.refreshExpandedNoteAction)

        about.addAction(self.aboutAction)

    def connect_signals(self):
        # tab actions
        self.gui.qtabs.tabCloseRequested.connect(self.tab_close_requested)

        # normal actions
        self.autosave_timer.timeout.connect(self.on_timer)
        self.findReplaceAction.triggered.connect(self.find_and_replace)
        self.findInFilesAction.triggered.connect(self.find_in_files)
        self.aboutAction.triggered.connect(self.about)
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

        if not self._show_images_disabled:
            self.showImagesAction.triggered.connect(self.show_images)
            self.hideImagesAction.triggered.connect(self.hide_images)
        self.autoTocAction.triggered.connect(self.auto_toc)
        self.numberHeadingsAction.triggered.connect(self.number_headings)
        self.denumberHeadingsAction.triggered.connect(self.denumber_headings)
        self.showAllNotesAction.triggered.connect(self.show_all_notes)

    def init_editor_text_shortcuts(self, editor):
        commands = editor.standardCommands()
        deletable_keys = [
            Qt.ShiftModifier | Qt.Key_Return, Qt.ControlModifier | Qt.Key_Return,
            Qt.ShiftModifier | Qt.Key_Enter, Qt.ControlModifier | Qt.Key_Enter,
            Qt.AltModifier | Qt.Key_Enter, Qt.AltModifier | Qt.Key_Return,

        ]
        if sys.platform == 'darwin':
            deletable_keys = [
                Qt.ShiftModifier | Qt.Key_Return, Qt.MetaModifier | Qt.Key_Return,
                Qt.ShiftModifier | Qt.Key_Enter, Qt.MetaModifier | Qt.Key_Enter,
                Qt.AltModifier | Qt.Key_Enter, Qt.AltModifier | Qt.Key_Return,
            ]

        # now make sure our other actions won't get consumed by QScintilla
        other_ctrl_keys = [
            Qt.Key_E, Qt.Key_R, Qt.Key_T, Qt.Key_B,
            Qt.ShiftModifier | Qt.Key_I,
            Qt.ShiftModifier | Qt.Key_H,
            Qt.ShiftModifier | Qt.Key_T,
            Qt.ShiftModifier | Qt.Key_N,
            Qt.ShiftModifier | Qt.Key_R,
        ]

        if sys.platform == 'darwin':
            modifier = Qt.ControlModifier    # very strange auto-translation
        else:
            modifier = Qt.ControlModifier

        for key_combo in other_ctrl_keys:
            key_combo |= modifier
            deletable_keys.append(key_combo)

        for key_combo in deletable_keys:
            command = commands.boundTo(key_combo)
            if command is not None:
                print('Clearing key combo', key_combo, 'for command', command.description())
                if command.key() == key_combo:
                    command.setKey(0)
                elif command.alternateKey() == key_combo:
                    command.setAlternateKey(0)
                #print(command.key(), command.alternateKey())

    def connect_editor_signals(self, editor):
        # text shortcut actions
        self.init_editor_text_shortcuts(editor)
        # lexer actions
        editor.lexer().tag_clicked.connect(self.clicked_tag)
        editor.lexer().cite_key_clicked.connect(self.clicked_citekey)
        editor.lexer().note_id_clicked.connect(self.clicked_noteid)
        editor.lexer().search_spec_clicked.connect(self.search_spec_clicked)
        editor.lexer().create_link_from_title_clicked.connect(self.create_link_from_title_clicked)
        editor.text_shortcut_handler.shortcut_insert_link.connect(self.insert_link)
        editor.text_shortcut_handler.shortcut_tag_selector.connect(self.insert_tag)
        editor.text_shortcut_handler.shortcut_tag_list.connect(self.show_all_tags)
        editor.text_shortcut_handler.shortcut_insert_citation.connect(self.insert_citation)
        editor.text_shortcut_handler.shortcut_all_notes.connect(self.show_all_notes)
        editor.textChanged.connect(self.unsaved)

    def on_settings_editor_json_error(self, jsonerror):
        settings_editor = self.show_preferences()
        settings_editor.setCursorPosition(jsonerror.lineno, jsonerror.colno)
        QMessageBox.critical(settings_editor, "Parsing Error in Settings", f'{jsonerror.msg} in line {jsonerror.lineno} column {jsonerror.colno}')
        settings_editor.setCursorPosition(jsonerror.lineno, jsonerror.colno)


    def run(self):
        self.app = QApplication(sys.argv)
        if sys.platform == 'darwin':
            # TODO: this sort-of fixes the menu formatting for [,[ style shortcuts
            # self.app.setAttribute(Qt.AA_DontUseNativeMenuBar)
            pass
        QApplication.setStyle(QStyleFactory.create('Fusion'))
        theme_f = os.path.join(base_dir(), get_settings().get('theme', 'themes/monokai.json'))
        theme = Theme(f'{theme_f}')
        self.gui = MainWindow(theme)
        self.gui.setFocus()
        self.init_actions()
        self.initMenubar()
        self.connect_signals()
        self.project = None
        self.open_folder(self.app_state.recent_projects[-1])
        self.autosave_timer.start(1000)
        test_settings = get_settings(raw=False, on_error=self.on_settings_editor_json_error)

        exit_code = 0
        try:
            exit_code = self.app.exec_()
        except Exception as e:
            mb = QMessageBox()
            mb.setIcon(QMessageBox.Critical)
            mb.setWindowTitle('Error')
            mb.setText('Exception caught:')
            mb.setDetailedText(str(e) + '\n' + traceback.format_exc())
            mb.setStandardButtons(QMessageBox.Ok)
            mb.exec_()

            traceback.print_exc()
        sys.exit(exit_code)

    #
    # Qt SLOTS
    #
    def open_recent_project(self):
        action = self.sender()
        if action:
            self.open_folder(action.data())

    def find_and_replace(self):
        editor = self.get_active_editor()
        if not editor:
            return
        finder = FindDlg(self.gui, editor)
        finder.show()

    def update_recent_project_actions(self):
        for i in range(self.recent_projects_limit):
            self.recent_projects_actions[i].setVisible(False)

        for i, folder in enumerate(reversed(self.app_state.recent_projects[:self.recent_projects_limit])):
            text = f'&{i+1}: {os.path.basename(folder)}'
            self.recent_projects_actions[i].setText(text)
            self.recent_projects_actions[i].setData(folder)
            self.recent_projects_actions[i].setVisible(True)


    def clicked_noteid(self, noteid, ctrl, alt, shift):
        print('noteid', noteid, ctrl, alt, shift)
        filn = self.project.note_file_by_id(noteid)
        if alt:
            self.show_referencing_notes(noteid)
        else:
            if filn:
                self.open_document(filn)

    def clicked_tag(self, tag, ctrl, alt, shift):
        print('tag', tag)
        id2tags, tags2ids = self.project.find_all_notes_all_tags()
        title = f'# Notes referencing {tag}'
        note_ids = tags2ids[tag]
        notes = [self.project.note_file_by_id(note_id) for note_id in note_ids]
        self.project.externalize_note_links(notes, title)
        self.reload(self.gui.search_results_editor)

    def clicked_citekey(self, citekey, ctrl, alt, shift):
        print('citekey', citekey)
        notes = self.project.find_all_citations(citekey)
        self.project.externalize_note_links(notes, prefix=f'# Notes citing {citekey}')
        self.reload(self.gui.search_results_editor)

    def search_spec_clicked(self, search_spec, ctrl, alt, shift):
        print('search spec', search_spec)
        self.advanced_tag_search(search_spec)

    def create_link_from_title_clicked(self, title, ctrl, alt, shift, pos, length):
        print('create link from title', title)
        editor = self.get_active_editor()
        if not editor:
            return
        link = editor.text()[pos:pos+length]
        line_number, index = editor.lineIndexFromPosition(pos)
        line_from, line_to = line_number, line_number
        index_from = index
        index_to = index + length

        # create new note with title of link
        settings = self.project.settings
        extension = settings.get('markdown_extension')
        id_in_title = settings.get('id_in_title')
        new_id = self.project.timestamp()
        the_file = os.path.join(self.project.folder, new_id + ' ' + title + extension)
        new_title = title
        if id_in_title:
            new_title = new_id + ' ' + title
        editor = self.get_active_editor()
        if not editor:
            print('should never happen')
            return
        # get origin
        origin_id, origin_title = self.project.get_note_id_and_title_of(editor)
        editor.setSelection(line_from, index_from, line_to, index_to)
        editor.replaceSelectedText(new_id)
        self.project.create_note(the_file, new_title, origin_id, origin_title)
        self.open_document(the_file)

    def unsaved(self):
        editor = self.gui.qtabs.currentWidget()
        tab_index = self.gui.qtabs.currentIndex()
        if editor is None:
            return
        if editor.isModified():
            self.gui.qtabs.setTabText(tab_index, os.path.basename(editor.file_name) + '*')

    #
    # Comnands / Actions
    #
    def get_active_editor(self):
        """
        Helper function to find out where the keyboard input focus is
        """
        editors = [self.gui.qtabs.widget(i) for i in range(self.gui.qtabs.count())]
        if self.app.focusWidget() in editors:
            return self.app.focusWidget()
        elif self.app.focusWidget() == self.gui.search_results_editor:
            return self.gui.search_results_editor
        elif self.app.focusWidget() == self.gui.saved_searches_editor:
            return self.gui.saved_searches_editor
        else:
            return None

    def document_to_index_editor(self, filn):
        for i in range(self.gui.qtabs.count()):
            editor = self.gui.qtabs.widget(i)
            if editor.file_name == filn:
                return i, editor
        return -1, None

    def open_folder(self, folder=None):
        """
        """
        editor_list = [self.gui.qtabs.widget(i) for i in range(self.gui.qtabs.count())]
        for editor in editor_list:
            if editor.isModified():
                msg = "You have unsaved changes. Save them first?"
                buttonReply = QMessageBox.question(self.gui, 'Save Changes', msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                if buttonReply == QMessageBox.Yes:
                    self.save_all()
                break
        if not folder:
            folder = str(QFileDialog.getExistingDirectory(self.gui, "Select Directory"))
        if folder:
            self.gui.qtabs.clear()
            if folder in self.app_state.recent_projects:
                self.app_state.recent_projects = [f for f in self.app_state.recent_projects if f != folder]
            self.app_state.recent_projects.append(folder)
            self.project = Project(folder)
            self.project.prepare()
            self.app_state.save()
            self.gui.saved_searches_editor.file_name = self.project.get_saved_searches_filn()
            self.gui.search_results_editor.file_name = self.project.get_search_results_filn()
            self.reload(self.gui.saved_searches_editor)
            self.reload(self.gui.search_results_editor)
            if self.project.show_welcome:
                self.open_document(self.project.welcome_note)
            self.gui.setWindowTitle(f'Sublimeless Zettelkasten - {self.project.folder}')
            self.update_recent_project_actions()

    def reload(self, editor):
        if editor == self.gui.saved_searches_editor:
            file_name = self.project.get_saved_searches_filn()
        elif editor == self.gui.search_results_editor:
            file_name = self.project.get_search_results_filn()
        else:
            file_name = editor.file_name
        if not os.path.exists(file_name):
            return
        with open(file_name, mode='r', encoding='utf-8', errors='ignore') as f:
            editor.setText(f.read())
    ''''''

    def open_document(self, document_filn, is_settings_file=False):
        """
        Helper function to open a markdown or settings document in a new tab
        """
        #check if exists
        tab_index, editor = self.document_to_index_editor(document_filn)
        if editor:
            self.gui.qtabs.setCurrentIndex(tab_index)
            editor.setFocus()
            return editor

        # make new editor from file
        if is_settings_file:
            editor = SettingsEditor(self.gui.theme, document_filn)
        else:
            editor = self.gui.new_zk_editor(document_filn)
        document_name = os.path.basename(document_filn)
        self.gui.qtabs.addTab(editor, document_name)
        editor.setModified(False)
        if is_settings_file:
            editor.textChanged.connect(self.unsaved)
        else:
            self.connect_editor_signals(editor)
        editor.setFocus()
        # show that tab
        index, e = self.document_to_index_editor(document_filn)
        if index >= 0:
            self.gui.qtabs.setCurrentIndex(index)
        return editor
    ''''''

    def save(self):
        tab_index = self.gui.qtabs.currentIndex()
        editor = self.gui.qtabs.currentWidget()
        if editor:
            with open(editor.file_name, mode='w', encoding='utf-8', errors='ignore') as f:
                f.write(editor.text())
            editor.setModified(False)
            self.gui.qtabs.setTabText(tab_index, os.path.basename(editor.file_name))
            # Settings changed
            if editor.editor_type == 'settings':
                test_settings = get_settings(on_error=self.on_settings_editor_json_error)
                self.project.reload_settings()

        # always save saved searches
        editor = self.gui.saved_searches_editor
        with open(self.project.get_saved_searches_filn(),
                  mode='w', encoding='utf-8', errors='ignore') as f:
            f.write(editor.text())
        editor.setModified(False)

    def save_all(self):
        for tab_index in range(self.gui.qtabs.count()):
            editor = self.gui.qtabs.widget(tab_index)
            if editor:
                with open(editor.file_name, mode='w', encoding='utf-8', errors='ignore') as f:
                    f.write(editor.text())
                editor.setModified(False)
                self.gui.qtabs.setTabText(tab_index, os.path.basename(editor.file_name))

        # always save saved searches
        editor = self.gui.saved_searches_editor
        with open(self.project.get_saved_searches_filn(),
                  mode='w', encoding='utf-8', errors='ignore') as f:
            f.write(editor.text())
        editor.setModified(False)

    def show_preferences(self):
        editor = self.open_document(settings_filn, is_settings_file=True)
        return editor

    #
    # Zettelkasten Command Slots
    #

    def zk_new_zettel(self):
        print('New Zettel')
        origin = None
        o_title = None
        insert_link = False
        note_body = None
        suggested_title = ''

        # check if text is selected in one editor
        editor = self.get_active_editor()
        if isinstance(editor, ZettelkastenScintilla):
            filn = editor.file_name
            origin, o_title = self.project.get_note_id_and_title_of(editor)
            if editor.hasSelectedText():
                sel = editor.getSelection()
                sel_start = editor.positionFromLineIndex(sel[0], sel[1])
                sel_end = editor.positionFromLineIndex(sel[2], sel[3])
                suggested_title = editor.text()[sel_start:sel_end]
                if '\n' in suggested_title:
                    lines = suggested_title.split('\n')
                    suggested_title = lines[0]
                    if len(lines) > 1:
                        note_body = '\n'.join(lines[1:])
                insert_link = True
        parent = None  # or editor
        input_text = show_input_panel(parent, 'New Title:', suggested_title)
        if not input_text:
            return

        settings = self.project.settings
        extension = settings.get('markdown_extension')
        id_in_title = settings.get('id_in_title')

        new_id = self.project.timestamp()
        the_file = os.path.join(self.project.folder, new_id + ' ' + input_text + extension)
        new_title = input_text
        if id_in_title:
            new_title = new_id + ' ' + input_text

        if insert_link:
            link_txt = self.project.style_link(new_id, input_text)
            editor.replaceSelectedText(link_txt)
        self.project.create_note(the_file, new_title, origin, o_title, note_body)
        self.open_document(the_file)


    def zk_follow_link(self):
        print('Follow Link')

        editor = self.get_active_editor()
        if not editor:
            return

        line, index = editor.getCursorPosition()
        editor.lexer().on_click_indicator(line, index, 0)
        return

    def insert_link(self, pos=None):
        print('Insert Link')
        editor = self.get_active_editor()
        if not isinstance(editor, ZettelkastenScintilla):
            return
        extension = self.project.settings.get('markdown_extension')
        note_list_dict = {f: f for f in [os.path.basename(x).replace(extension, '') for x in self.project.get_all_note_files()]}
        selected_note, _ = show_fuzzy_panel(self.gui.qtabs, 'Insert Link to Note', note_list_dict)

        if selected_note:
            note_id, title = selected_note.split(' ', 1)
            link_txt = self.project.style_link(note_id, title)
            # check if editor contains [[ right before current cursor position
            line, index = editor.getCursorPosition()
            replace_index_start = index
            replace_index_end = index
            # the lexer sends us an int, the QAction a bool
            if isinstance(pos, int) and not isinstance(pos, bool):
                replace_index_start -= 2
            editor.setSelection(line, replace_index_start, line, replace_index_end)
            editor.replaceSelectedText(link_txt)
    ''''''

    def show_all_notes(self, check_editor=True):
        note_files = self.project.get_all_note_files()
        self.project.externalize_note_links(note_files, '# All Notes')
        self.reload(self.gui.search_results_editor)

        # the lexer sends us an int, the QAction a bool
        if isinstance(check_editor, int) and not isinstance(check_editor, bool):
            # now replace the potential [!
            editor = self.get_active_editor()
            if isinstance(editor, ZettelkastenScintilla):
                line, index = editor.getCursorPosition()
                replace_index_start = index - 2
                replace_index_end = index
                editor.setSelection(line, replace_index_start, line, replace_index_end)
                editor.replaceSelectedText('')

    def show_all_tags(self, check_editor=True):
        print('show all tags')
        tags = self.project.find_all_tags()
        tags.sort()
        lines = '# All Tags\n\n'
        lines += '\n'.join(['* ' + tag for tag in tags])

        with open(self.project.get_search_results_filn(),
                  mode='w', encoding='utf-8', errors='ignore') as f:
            f.write(lines)
        self.reload(self.gui.search_results_editor)
        # the lexer sends us an int, the QAction a bool
        if isinstance(check_editor, int) and not isinstance(check_editor, bool):
            # now replace the potential #!
            editor = self.get_active_editor()
            if isinstance(editor, ZettelkastenScintilla):
                line, index = editor.getCursorPosition()
                replace_index_start = index - 2
                replace_index_end = index
                editor.setSelection(line, replace_index_start, line, replace_index_end)
                editor.replaceSelectedText('')

    def insert_tag(self, pos=None):
        print('insert tag')
        editor = self.get_active_editor()
        if not isinstance(editor, ZettelkastenScintilla):
            return
        tag_list_dict = {f: f for f in self.project.find_all_tags()}
        selected_tag, _ = show_fuzzy_panel(self.gui.qtabs, 'Insert Link to Note', tag_list_dict)
        if selected_tag:
            # check if editor contains #? right before current cursor position
            line, index = editor.getCursorPosition()
            replace_index_start = index
            replace_index_end = index
            if isinstance(pos, int) and not isinstance(pos, bool):
                replace_index_start -= 2
            editor.setSelection(line, replace_index_start, line, replace_index_end)
            editor.replaceSelectedText(selected_tag)

    def show_referencing_notes(self, note_id=None):
        print('Show referencing note')
        editor = self.get_active_editor()
        if not isinstance(note_id, str):
            link, editor_region = self.project.select_link_in_editor(editor)
            if not editor_region:
                return
            note_id = self.project.cut_after_note_id(link)
            if not note_id:
                return
            print(note_id, editor_region)
        ref_note_files = self.project.find_referencing_notes(note_id)
        styled_link = self.project.style_link(note_id, '')
        self.project.externalize_note_links(ref_note_files, f'Notes referencing {styled_link}')
        self.reload(self.gui.search_results_editor)

    def insert_citation(self, pos=None):
        print('insert citation')
        editor = self.get_active_editor()
        if not isinstance(editor, ZettelkastenScintilla):
            return
        self.citekey_list = []
        bibfile = Autobib.look_for_bibfile(self.project)
        if not bibfile:
            return
        entries = Autobib.extract_all_entries(bibfile)
        ck_choices = {}
        for citekey, d in entries.items():
            self.citekey_list.append(citekey)
            item = '{} {} - {} ({})'.format(d['authors'], d['year'], d['title'], citekey)
            ck_choices[item] = citekey
        item, citekey = show_fuzzy_panel(self.gui.qtabs, 'Insert Citation', ck_choices, longlines=True, manylines=True)

        if not citekey:
            return
        line, index = editor.getCursorPosition()
        replace_index_start = index
        replace_index_end = index
        if isinstance(pos, int) and not isinstance(pos, bool):
            replace_index_start -= 2
        editor.setSelection(line, replace_index_start, line, replace_index_end)
        mmd_style = self.project.settings.get('citations-mmd-style', None)
        if mmd_style:
            fmt_completion = '[][#{}]'
        else:
            fmt_completion = '[@{}]'
        text = fmt_completion.format(citekey)
        editor.replaceSelectedText(text)

    def auto_bib(self):
        editor = self.get_active_editor()
        if not editor:
            return

        settings = self.project.settings
        mmd_style = settings.get('citations-mmd-style', None)

        bibfile = Autobib.look_for_bibfile(self.project)
        if bibfile:
            try:
                text = editor.text()
                pandoc = get_pandoc()
                if not pandoc:
                    QMessageBox.warning(editor, 'Pandoc not found', 'The pandoc program could not be executed. Have you installed it?\n\nCheck the setting "path_to_pandoc".')
                    return
                ck2bib = Autobib.create_bibliography(text, bibfile, pandoc=pandoc)
                marker = '<!-- references (auto)'
                marker_line = marker
                if mmd_style:
                    marker_line += ' -->'
                bib_lines = [marker_line + '\n']
                for citekey in sorted(ck2bib):
                    bib = ck2bib[citekey]
                    line = '[{}]: {}\n'.format(citekey, bib)
                    bib_lines.append(line)
                if not mmd_style:
                    bib_lines.append('-->')
                new_lines = []
                for line in text.split('\n'):
                    if line.strip().startswith(marker):
                        break
                    new_lines.append(line)
                result_text = '\n'.join(new_lines)
                result_text += '\n' + '\n'.join(bib_lines) + '\n'
                editor.setText(result_text)
                editor.setCursorPosition(editor.lines(), 0)
            except:
                Autobib.log_exception('wtf', True)

    def auto_toc(self):
        # TOC markers
        TOC_HDR = '<!-- table of contents (auto) -->'
        TOC_END = '<!-- (end of auto-toc) -->'

        def heading2ref(heading):
            """
            Turn heading into a reference as in `[heading](#reference)`.
            """
            ref = unicodedata.normalize('NFKD', heading).encode('ascii', 'ignore')
            ref = re.sub(r'[^\w\s-]', '', ref.decode('ascii', errors='ignore')).strip().lower()
            return re.sub(r'[-\s]+', '-', ref)

        def find_toc_region(text):
            """
            Find the entire toc region including start and end markers.
            """
            toc_hdr = re.compile(re.escape(TOC_HDR))
            toc_end = re.compile(re.escape(TOC_END))
            match = toc_hdr.search(text)
            if match:
                start_pos = match.start()
                end_of_start_pos = match.end()
                match = toc_end.search(text, end_of_start_pos)
                if match:
                    end_pos = match.end()
                    return (start_pos, end_pos)
            return None, None

        editor = self.get_active_editor()
        if not editor:
            return
        settings = self.project.settings
        suffix_sep = settings.get('toc_suffix_separator', None)
        if not suffix_sep:
            suffix_sep = '_'
        toc_start, toc_end = find_toc_region(editor.text())
        if toc_start:
            line_num_start, index_start = editor.lineIndexFromPosition(toc_start)
            line_num_end, index_end = editor.lineIndexFromPosition(toc_end)
        else:
            line_num_start, index_start = editor.getCursorPosition()
            line_num_end, index_end = editor.getCursorPosition()

        editor.setSelection(line_num_start, index_start, line_num_end, index_end)

        lines = [TOC_HDR]
        ref_counter = Counter({'': 1})   # '' for unprintable char only headings

        for heading, level, h_start, h_end in editor.lexer().get_headings():
            ref = heading2ref(heading)
            ref_counter[ref] += 1
            if ref_counter[ref] > 1:
                ref = ref + '{}{}'.format(suffix_sep, ref_counter[ref] - 1)

            match = re.match(r'\s*(#+)(.*)', heading)
            hashes, title = match.groups()
            title = title.strip()
            line = '    ' * (level - 1) + f'* [{title}](#{ref})'
            lines.append(line)
        lines.append(TOC_END)
        print('\n'.join(lines))
        editor.replaceSelectedText('\n'.join(lines))

    def number_headings(self):
        editor = self.get_active_editor()
        if not editor:
            return
        current_level = 0
        levels = [0] * 6
        headings_to_skip = 0
        text = editor.text()
        heading_matcher = re.compile('^(#{1,6})(.+)$', flags=re.MULTILINE)
        while True:
            for heading_index, heading_match in enumerate(heading_matcher.finditer(text)):
                if heading_index < headings_to_skip:
                    continue
                headings_to_skip += 1
                heading = heading_match.group()
                match = re.match(r'(\s*)(#+)(\s*[1-9.]*\s)(.*)', heading)
                spaces, hashes, old_numbering, title = match.groups()
                level = len(hashes) - 1
                if level < current_level:
                    levels[level + 1:] = [0] * (6 - level - 1)
                levels[level] += 1
                current_level = level
                numbering = ' ' + '.'.join([str(l) for l in levels[:level+1]]) + ' '
                new_heading = f'{hashes} {numbering}{title}'
                text = text[:heading_match.start()] \
                       + new_heading + \
                       text[heading_match.end():]
                break
            else:
                break
        editor.setText(text)
        return

    def denumber_headings(self):
        editor = self.get_active_editor()
        if not editor:
            return
        headings_to_skip = 0
        text = editor.text()
        heading_matcher = re.compile('^(#{1,6})(.+)$', flags=re.MULTILINE)
        while True:
            for heading_index, heading_match in enumerate(heading_matcher.finditer(text)):
                if heading_index < headings_to_skip:
                    continue
                headings_to_skip += 1
                heading = heading_match.group()
                match = re.match(r'(\s*)(#+)(\s*[1-9.]*\s)(.*)', heading)
                spaces, hashes, old_numbering, title = match.groups()
                new_heading = f'{hashes} {title}'
                text = text[:heading_match.start()] \
                       + new_heading + \
                       text[heading_match.end():]
                break
            else:
                break
        editor.setText(text)
        return

    def expand_link(self):
        print('expand link')
        editor = self.get_active_editor()
        if not editor:
            return
        TextProduction.expand_link_in(editor, self.project)

    def expand_overview_note(self):
        print('expand overview note')
        editor = self.get_active_editor()
        if not editor:
            return
        origin, o_title = self.project.get_note_id_and_title_of(editor)
        if not origin:
            return
        input_text = show_input_panel(None, 'Expansion Note Title:', 'Expanded - ' + origin)
        if not input_text:
            return

        settings = self.project.settings
        extension = settings.get('markdown_extension')
        id_in_title = settings.get('id_in_title')

        new_id = self.project.timestamp()
        the_file = os.path.join(self.project.folder, new_id + ' ' + input_text + extension)
        new_title = input_text
        if id_in_title:
            new_title = new_id + ' ' + input_text

        complete_text = editor.text()
        note_body = TextProduction.expand_links(complete_text, self.project, replace_lines=True)
        note_body = f'\n# Expansion of {origin} {o_title}\n' + note_body
        self.project.create_note(the_file, new_title, origin, o_title, note_body)
        self.open_document(the_file)

    def refresh_expanded_note(self):
        editor = self.get_active_editor()
        if not editor:
            return
        complete_text = editor.text()
        result_text = TextProduction.refresh_result(complete_text, self.project)
        editor.setText(result_text)

    def advanced_tag_search(self, search_spec=None):
        if not search_spec:
            search_spec = show_input_panel(None, '#tags and not !#tags:', '')
        if not search_spec:
            return
        if search_spec.startswith('[!'):
            self.show_all_notes(check_editor=False)
            return
        elif search_spec.startswith('#!'):
            self.show_all_tags(check_editor=False)
            return

        if search_spec.strip().startswith('#') or search_spec.startswith('!#'):
            notes = TagSearch.advanced_tag_search(search_spec, self.project)
            notes = [self.project.note_file_by_id(note_id) for note_id in notes]
            self.project.externalize_note_links(notes, '# Notes matching search ' + search_spec)
            self.reload(self.gui.search_results_editor)
        else:
            self.find_in_files(search_spec)
        return

    def show_images(self):
        # image links with attributes
        RE_IMG_LINKS = r'(!\[)(.*)(\])(\()(.*)(\))(\{)(.*)(\})'

        editor = self.get_active_editor()
        if not editor:
            return
        ImageHandler.show_images(editor, self.project)


    def hide_images(self):
        editor = self.get_active_editor()
        if not editor:
            return
        editor.delete_all_images()

    def tab_close_requested(self, index):
        if self.gui.qtabs.count() == 1:
            return
        editor = self.gui.qtabs.widget(index)
        if editor.isModified():
            msg = f"You have unsaved changes in {os.path.basename(editor.file_name)} Close anyway?"
            buttonReply = QMessageBox.question(editor, 'Unsaved Changes', msg, QMessageBox.Yes | QMessageBox.No,
                                               QMessageBox.No)
            if buttonReply == QMessageBox.No:
                return    # ignore
        self.gui.qtabs.removeTab(index)

    def about(self):
        about = AboutDlg(self.gui)
        about.exec_()

    def find_in_files(self, search_term=None):
        if not search_term:
            search_term = show_input_panel(None, 'Find in files:', '')
        if not search_term:
            return
        note_files = self.project.get_all_note_files()
        result_notes = []
        for note in note_files:
            with open(note, mode='r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
                if search_term in text:
                    result_notes.append(note)
        self.project.externalize_note_links(result_notes, '# Notes matching search ' + search_term)
        self.reload(self.gui.search_results_editor)
        return result_notes


if __name__ == '__main__':
    Sublimeless_Zk().run()
