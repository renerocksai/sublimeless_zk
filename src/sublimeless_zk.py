# -*- coding: utf-8 -*-
import os
import sys
import traceback
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.Qsci import *
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QObject, QTimer, QEventLoop
import re
import unicodedata
from collections import Counter
import time
from json import JSONDecodeError
import jstyleson as json
import tempfile
import subprocess
from collections import defaultdict

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
from settings import settings_filn, base_dir, get_settings, get_pandoc, get_real_error_lineno
from about import AboutDlg
from findandreplace import FindDlg
from semantic_zk import SemanticZKDialog
from custmenuitem import CustomMenuItemAction
from buildcommands import BuildCommands
from zkutils import sanitize_filename, split_search_terms, open_hyperlink
from findrefcountdlg import show_find_refcount_dlg
from notewatcher import NotesWatcher


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
        self.bib_entries = None # caching bib
        self.current_search_attrs = None
        self.notes_watcher = None

    def on_timer(self):
        time_now = int(time.time())
        if time_now % 1 == 0:
            self.update_status_bar()
        if not self.autosave_interval:
            return
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

        self.insertLinkAction = CustomMenuItemAction('Insert Link to Note', self)
        self.insertLinkAction.setShortcut('[[')

        self.showReferencingNotesAction = QAction('Show referencing notes', self)
        self.showReferencingNotesAction.setShortcuts(['Alt+Return', 'Alt+Enter'])

        self.insertTagAction = CustomMenuItemAction('Insert Tag', self)
        self.insertTagAction.setShortcut('#?')

        self.showTagsAction = CustomMenuItemAction('Show all Tags', self)
        self.showTagsAction.setShortcut('#!')

        self.expandLinkAction = QAction('Expand link', self)
        self.expandLinkAction.setShortcut('Ctrl+.')
        if sys.platform == 'darwin':
            self.expandLinkAction.setShortcut('Meta+.')

        self.insertCitationAction = CustomMenuItemAction('Insert Citation', self)
        self.insertCitationAction.setShortcuts(['[@', '[#'])

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
        self.denumberHeadingsAction.setShortcut('Ctrl+Shift+V')

        self.showAllNotesAction = CustomMenuItemAction('Show all Notes', self)
        self.showAllNotesAction.setShortcut('[!')

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

        self.fuzzyOpenAction = QAction('Browse notes to open...', self)
        self.fuzzyOpenAction.setShortcut('Ctrl+P')

        self.closeCurrentTabAction = QAction('Close current tab', self)
        self.closeCurrentTabAction.setShortcut('Ctrl+W')

        self.cycleTabsAction = QAction('Cycle backwards through tabs', self)
        self.cycleTabsAction.setShortcut('Ctrl+Shift+[')

        self.cycleTabsForwardAction = QAction('Cycle forwards through tabs', self)
        self.cycleTabsForwardAction.setShortcut('Ctrl+Shift+]')

        self.newThemeAction = QAction('New Theme...', self)
        self.editThemeAction = QAction('Edit current Theme...', self)
        self.chooseThemeAction = QAction('Switch Theme...', self)

        self.renameNoteAction = QAction('Rename Note...', self)
        self.renameNoteAction.setShortcut('Ctrl+Shift+R')

        self.deleteNoteAction = QAction('Delete Note...', self)

        self.exportHtmlAction = QAction('Export  archive to HTML...', self)

        self.quitApplicationAction = QAction('Exit...', self)
        self.quitApplicationAction.setShortcut('Ctrl+Q')

        self.showHideSidePanelAction = QAction('Toggle Side Panel', self)
        self.showHideSidePanelAction.setShortcut('Ctrl+Shift+K')

        self.toggleStatusBarAction = QAction('Toggle Status Bar', self)
        self.toggleStatusBarAction.setShortcut('Ctrl+Shift+J')

        self.reloadBibfileAction = QAction('Reload BIB file', self)
        self.reloadBibfileAction.setShortcut('Ctrl+Shift+B')

        self.toggleWrapLineAction = QAction('Toggle Line Wrap', self)
        self.toggleWrapMarkersAction = QAction('Toggle Wrap Markers', self)
        self.toggleWrapIndentAction = QAction('Toggle Wrap Indent', self)
        self.toggleAutoIndentAction = QAction('Toggle Auto-Indent')
        self.toggleIndentationGuidesAction = QAction('Toggle Indentation Guides', self)
        self.toggleUseTabsAction = QAction('Toggle TABs / Spaces', self)

        self.runExternalCommandAction = QAction('Run External Command...', self)
        self.runExternalCommandAction.setShortcut('Ctrl+Shift+X')
        self.editExternalCommandsAction = QAction('Edit external commands...', self)

        self.gotoAction = QAction('Go to...', self)
        self.gotoAction.setShortcut('Ctrl+Shift+G')

        self.findRefcountAction = QAction('Find notes with references...', self)
        self.findRefcountAction.setShortcut('Ctrl+Shift+W')

        self.moveLineUpAction = QAction('Move Line Up', self)
        self.moveLineUpAction.setShortcut('Ctrl+Shift+U')
        self.moveLineDownAction = QAction('Move Line Down', self)
        self.moveLineDownAction.setShortcut('Ctrl+Shift+D')

        self.showRecentViewsAction = QAction('Show recently viewed notes')
        self.showRecentViewsAction.setShortcut('Shift+Ctrl+Alt+H')

        self.toggleOpenFilesPanelAction = QAction('Toggle Open Files Panel', self)
        self.toggleOpenFilesPanelAction.setShortcut('Shift+Alt+K')

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
            self.ctrl_return_sc = QShortcut(Qt.MetaModifier| Qt.Key_Return, self.gui)
        else:
            self.ctrl_return_sc = QShortcut(Qt.ControlModifier | Qt.Key_Return, self.gui)
        self.ctrl_return_sc.activated.connect(self.zk_follow_link)

        # command palette action **must come last**
        self.command_palette_actions = {action.text(): action for action in self.__dict__.values() if isinstance(action, QAction)}
        self.commandPaletteAction = QAction('Show Command Palette...', self)
        self.commandPaletteAction.setShortcut('Ctrl+Shift+P')
        return

    def update_status_bar(self):
        editor = self.get_active_editor()
        if not editor:
            self.gui.tab_spaces_label.setText('')
            self.gui.line_count_label.setText('')
            self.gui.word_count_label.setText('')
            return
        if editor.editor_type != 'normal':
            self.gui.tab_spaces_label.setText('')
            self.gui.line_count_label.setText('')
            self.gui.word_count_label.setText('')
            return
        t = editor.text()
        line_count = len(t.split('\n'))
        word_count = len(t.split())
        self.gui.line_count_label.setText(f'Lines: {line_count}')
        self.gui.word_count_label.setText(f'Words: {word_count}')
        
        self.gui.format_editor_info(editor)
        return

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
        self.file_menu.addAction(self.closeCurrentTabAction)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.fuzzyOpenAction)
        self.file_menu.addAction(self.renameNoteAction)
        self.file_menu.addAction(self.deleteNoteAction)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.exportHtmlAction)
        self.file_menu.addSeparator()
        # here go the most recents
        for i in range(self.recent_projects_limit):
            self.file_menu.addAction(self.recent_projects_actions[i])
        self.update_recent_project_actions()
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.quitApplicationAction)

        edit.addAction(self.undoAction)
        edit.addAction(self.redoAction)
        edit.addSeparator()
        edit.addAction(self.copyAction)
        edit.addAction(self.cutAction)
        edit.addAction(self.pasteAction)
        edit.addAction(self.moveLineUpAction)
        edit.addAction(self.moveLineDownAction)
        edit.addSeparator()

        edit_editor = edit.addMenu('Editor')
        edit_editor.addAction(self.toggleAutoIndentAction)
        edit_editor.addAction(self.toggleWrapLineAction)
        edit_editor.addAction(self.toggleWrapMarkersAction)
        edit_editor.addAction(self.toggleWrapIndentAction)
        edit_editor.addAction(self.toggleIndentationGuidesAction)
        edit_editor.addAction(self.toggleUseTabsAction)
        
        edit.addSeparator()
        edit.addAction(self.insertLinkAction)
        edit.addAction(self.insertTagAction)
        edit.addAction(self.insertCitationAction)
        edit.addAction(self.expandLinkAction)
        edit.addAction(self.autoBibAction)
        edit.addAction(self.autoTocAction)
        edit.addAction(self.numberHeadingsAction)
        edit.addAction(self.denumberHeadingsAction)
        edit.addAction(self.showPreferencesAction)

        find.addAction(self.findReplaceAction)
        find.addAction(self.findInFilesAction)
        find.addAction(self.advancedTagSearchAction)
        find.addAction(self.findRefcountAction)

        view.addAction(self.commandPaletteAction)
        view.addAction(self.cycleTabsForwardAction)
        view.addAction(self.cycleTabsAction)
        view.addAction(self.gotoAction)
        view.addAction(self.showHideSidePanelAction)
        view.addAction(self.toggleOpenFilesPanelAction)
        view.addAction(self.toggleStatusBarAction)
        view.addSeparator()
        view.addAction(self.showAllNotesAction)
        view.addAction(self.showRecentViewsAction)
        view.addAction(self.showReferencingNotesAction)
        view.addAction(self.showTagsAction)
        view.addSeparator()
        view.addAction(self.newThemeAction)
        view.addAction(self.chooseThemeAction)
        view.addAction(self.editThemeAction)

        if not self._show_images_disabled:
            view.addSeparator()
            view.addAction(self.showImagesAction)
            view.addAction(self.hideImagesAction)

        tools.addAction(self.reloadBibfileAction)
        tools.addAction(self.expandOverviewNoteAction)
        tools.addAction(self.refreshExpandedNoteAction)
        tools.addSeparator()
        tools.addAction(self.runExternalCommandAction)
        tools.addAction(self.editExternalCommandsAction)

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
        self.fuzzyOpenAction.triggered.connect(self.fuzzy_open)
        self.closeCurrentTabAction.triggered.connect(self.close_current_tab)
        self.cycleTabsAction.triggered.connect(self.cycle_tabs_backward)
        self.cycleTabsForwardAction.triggered.connect(self.cycle_tabs_forward)
        self.newThemeAction.triggered.connect(self.new_theme)
        self.editThemeAction.triggered.connect(self.edit_theme)
        self.chooseThemeAction.triggered.connect(self.switch_theme)
        self.renameNoteAction.triggered.connect(self.rename_note)
        self.deleteNoteAction.triggered.connect(self.delete_note)
        self.exportHtmlAction.triggered.connect(self.export_to_html)
        self.quitApplicationAction.triggered.connect(self.quit_application)
        self.commandPaletteAction.triggered.connect(self.show_command_palette)
        self.showHideSidePanelAction.triggered.connect(self.show_hide_sidepanel)
        self.toggleStatusBarAction.triggered.connect(self.toggle_statusbar)
        self.reloadBibfileAction.triggered.connect(self.reload_bibfile)

        self.toggleAutoIndentAction.triggered.connect(self.toggle_auto_indent)
        self.toggleIndentationGuidesAction.triggered.connect(self.toggle_indentation_guides)
        self.toggleUseTabsAction.triggered.connect(self.toggle_use_tabs)
        self.toggleWrapIndentAction.triggered.connect(self.toggle_wrap_indent)
        self.toggleWrapLineAction.triggered.connect(self.toggle_wrap_line)
        self.toggleWrapMarkersAction.triggered.connect(self.toggle_wrap_markers)
        self.runExternalCommandAction.triggered.connect(self.run_external_command)
        self.editExternalCommandsAction.triggered.connect(self.edit_external_commands)
        self.gotoAction.triggered.connect(self.goto)
        self.findRefcountAction.triggered.connect(self.find_notes_with_refcounts)
        self.moveLineUpAction.triggered.connect(self.move_line_up)
        self.moveLineDownAction.triggered.connect(self.move_line_down)
        self.showRecentViewsAction.triggered.connect(self.show_recent_views)

        self.toggleOpenFilesPanelAction.triggered.connect(self.toggle_open_files_panel)
        self.gui.notelist_panel.file_clicked.connect(self.open_document)

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
            Qt.Key_E, Qt.Key_R,
            Qt.Key_T,
            Qt.Key_B,
            Qt.ShiftModifier | Qt.Key_I,
            Qt.ShiftModifier | Qt.Key_H,
            Qt.ShiftModifier | Qt.Key_T,
            Qt.ShiftModifier | Qt.Key_N,
            Qt.ShiftModifier | Qt.Key_R,
            Qt.ShiftModifier | Qt.Key_W,
            Qt.ShiftModifier | Qt.Key_U,
            Qt.ShiftModifier | Qt.Key_D,
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
                #print('Clearing key combo', QKeySequence(key_combo).toString(), 'for command', command.description())
                if command.key() == key_combo:
                    command.setKey(0)
                if command.alternateKey() == key_combo:
                    command.setAlternateKey(0)
                #print(command.key(), command.alternateKey())

        # 
        # ctrl/cmd + shift + [
        command = commands.find(QsciCommand.ParaUpExtend)
        if command:
            command.setKey(Qt.ShiftModifier | Qt.ControlModifier | Qt.Key_Up)
            command.setAlternateKey(0)
        # ctrl/cmd + shift + ]
        command = commands.find(QsciCommand.ParaDownExtend)
        if command:
            command.setKey(Qt.ShiftModifier | Qt.ControlModifier | Qt.Key_Down)
            command.setAlternateKey(0)

        command = commands.find(QsciCommand.ParaDown)
        if command:
            command.setKey(Qt.AltModifier | Qt.Key_Down)
            command.setAlternateKey(0)
        
        command = commands.find(QsciCommand.ParaUp)
        if command:
            command.setKey(Qt.AltModifier | Qt.Key_Up)
            command.setAlternateKey(0)
        
        # change opt+del from undo
        command = commands.find(QsciCommand.Undo)
        if command:
            #command.setKey(0)   leave cmd+z intact
            command.setAlternateKey(0)
        # free opt+backspace and assign to cmd+backspace
        command = commands.find(QsciCommand.DeleteWordLeft)
        if command:
            command.setKey(Qt.AltModifier|Qt.Key_Backspace)
        # delete line left from cursor with cmd+backspace
        command = commands.find(QsciCommand.DeleteLineLeft)
        if command:
            command.setKey(Qt.ControlModifier | Qt.Key_Backspace)
        
        # ctrl+shift+u -> convert sel to uppercase --> delete this shortcut
        command = commands.find(QsciCommand.SelectionUpperCase)
        if command:
            command.setKey(0)
            command.setAlternateKey(0)

        # zoom in
        command = commands.find(QsciCommand.ZoomIn)
        if command:
            command.setKey(Qt.ControlModifier | Qt.Key_Plus)
            command.setAlternateKey(Qt.ControlModifier | Qt.Key_Equal)

    def connect_editor_signals(self, editor):
        # text shortcut actions
        self.init_editor_text_shortcuts(editor)
        # lexer actions
        editor.lexer().tag_clicked.connect(self.clicked_tag)
        editor.lexer().cite_key_clicked.connect(self.clicked_citekey)
        editor.lexer().note_id_clicked.connect(self.clicked_noteid)
        editor.lexer().search_spec_clicked.connect(self.search_spec_clicked)
        editor.lexer().hyperlink_clicked.connect(self.open_hyperlink)
        editor.lexer().create_link_from_title_clicked.connect(self.create_link_from_title_clicked)
        editor.text_shortcut_handler.shortcut_insert_link.connect(self.insert_link)
        editor.text_shortcut_handler.shortcut_tag_selector.connect(self.insert_tag)
        editor.text_shortcut_handler.shortcut_tag_list.connect(self.show_all_tags)
        editor.text_shortcut_handler.shortcut_insert_citation.connect(self.insert_citation)
        editor.text_shortcut_handler.shortcut_all_notes.connect(self.show_all_notes)
        editor.textChanged.connect(self.unsaved)

    def on_settings_editor_json_error(self, editor=None, jsonerror=None):
        if editor is None:
            editor = self.show_preferences()
        editor.setCursorPosition(jsonerror.lineno, jsonerror.colno)
        QMessageBox.critical(editor, "Parsing Error in JSON", f'{jsonerror.msg} in line {jsonerror.lineno} column {jsonerror.colno}')
        editor.setCursorPosition(jsonerror.lineno, jsonerror.colno)

    def about_to_quit(self):
        self.notes_watcher.quit_thread()
        time.sleep(0.3)

    def run(self):
        self.app = QApplication(sys.argv)
        if sys.platform == 'darwin':
            # TODO: this sort-of fixes the menu formatting for [,[ style shortcuts
            # self.app.setAttribute(Qt.AA_DontUseNativeMenuBar)
            pass

        # notes watcher!!!
        self.notes_watcher = NotesWatcher.create(1000)
        self.notes_watcher.files_changed_on_disk.connect(self.files_changed_on_disk)
        self.app.aboutToQuit.connect(self.about_to_quit)
        time.sleep(0.1)
        self.notes_watcher.keep_going()
        # end of notes watcher

        QApplication.setStyle(QStyleFactory.create('Fusion'))
        Theme.prepare_theme_folder()
        theme_f = os.path.basename(get_settings().get('theme', 'Office.json'))
        theme = Theme(theme_f)
        self.gui = MainWindow(theme, self.mainwindow_close_handler)
        self.gui.setFocus()
        self.init_actions()
        self.initMenubar()
        self.connect_signals()
        self.project = None
        self.open_folder(self.app_state.recent_projects[-1])
        self.autosave_timer.start(1000)
        test_settings = get_settings(raw=False, on_error=self.on_settings_editor_json_error)
        if 'ui.font.face' in test_settings and 'ui.font.size' in test_settings:
            try:
                self.app.setFont(QFont(test_settings['ui.font.face'], test_settings['ui.font.size']))
            except:
                pass
        self.gui.apply_font_settings(test_settings)
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

    def files_changed_on_disk(self, d):
        if d:
            print('Files changed:')
            for fn, mt in d.items():
                print(f'    file={fn} : mtime={mt}')

            editor_list = [self.gui.qtabs.widget(i) for i in range(self.gui.qtabs.count())]
            for fn in d:
                msg = f"{os.path.basename(fn)} has changed on disk. Reload?"
                buttonReply = QMessageBox.question(self.gui, 'External file change', msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                if buttonReply == QMessageBox.Yes:
                    for i, editor in enumerate(editor_list):
                        if editor.file_name == fn:
                            self.gui.qtabs.removeTab(i)
                            self.gui.notelist_panel.remove_note_filn(fn)
                            self.open_document(fn)
                            break
                else:
                    self.notes_watcher.on_ignore_clicked(fn)
        self.notes_watcher.keep_going()

    def open_recent_project(self):
        action = self.sender()
        if action:
            self.open_folder(action.data())

    def find_and_replace(self):
        editor = self.get_active_editor()
        if not editor:
            return
        finder = FindDlg(self.gui, qtabs=self.gui.qtabs)
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
                return self.open_document(filn)

    def clicked_tag(self, tag, ctrl, alt, shift):
        print('tag', tag)
        id2tags, tags2ids = self.project.find_all_notes_all_tags()
        note_ids = tags2ids[tag]
        notes = [self.project.note_file_by_id(note_id) for note_id in note_ids]
        title = f'# {len(notes)} Notes referencing {tag}'
        self.project.externalize_note_links(notes, title)
        self.reload(self.gui.search_results_editor)

    def clicked_citekey(self, citekey, ctrl, alt, shift):
        print('citekey', citekey)
        notes = self.project.find_all_citations(citekey)
        self.project.externalize_note_links(notes, prefix=f'# {len(notes)} Notes citing {citekey}')
        self.reload(self.gui.search_results_editor)

    def search_spec_clicked(self, search_spec, ctrl, alt, shift):
        print('search spec', search_spec)
        self.advanced_tag_search(search_spec)

    def create_link_from_title_clicked(self, title, ctrl, alt, shift, pos, length):
        """
        title : nice python utf-8 string of the title
        pos : position of link in text() -- the nice python utf-8 string
        length :  length of the python string title
        """
        print('create link from title', title)
        editor = self.get_active_editor()
        if not editor:
            return

        # create new note with title of link
        settings = self.project.settings
        extension = settings.get('markdown_extension', '.md')
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
        link_txt = self.project.style_link(new_id, title)
        repl_from, repl_to = self.project.extend_link_to_brackets(editor.text(), pos, pos + length)
        txt = editor.text()
        txt = txt[:repl_from] + link_txt + txt[repl_to+1:]
        editor.setText(txt)
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
            if self.gui.qtabs.count():
                return self.gui.qtabs.currentWidget()
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
        if self.project:
            self.save_appstate()
        editor_list = [self.gui.qtabs.widget(i) for i in range(self.gui.qtabs.count())]

        # auto-save if auto-save is on, instead of nagging us
        if self.autosave_interval > 0 and editor_list:
            self.save_all()
        else:
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
            self.notes_watcher.reset()
            self.gui.notelist_panel.clear()
            if folder in self.app_state.recent_projects:
                self.app_state.recent_projects = [f for f in self.app_state.recent_projects if f != folder]
            self.app_state.recent_projects.append(folder)
            self.project = Project(folder)
            self.project.prepare()
            self.reopen_notes()
            self.save_appstate()
            self.gui.saved_searches_editor.file_name = self.project.get_saved_searches_filn()
            self.gui.search_results_editor.file_name = self.project.get_search_results_filn()
            self.reload(self.gui.saved_searches_editor)
            self.reload(self.gui.search_results_editor)
            if self.project.show_welcome:
                self.open_document(self.project.welcome_note)
            self.gui.setWindowTitle(f'Sublimeless Zettelkasten - {self.project.folder}')
            self.update_recent_project_actions()
            self.bib_entries = None

    def update_open_notes(self):
        recent_files = []
        for i in range(self.gui.qtabs.count()):
            editor = self.gui.qtabs.widget(i)
            if editor.editor_type == 'normal':
                recent_files.append(editor.file_name)
        self.app_state.open_notes[self.project.folder] = recent_files


    def reopen_notes(self):
        if self.project.folder in self.app_state.open_notes:
            for filn in self.app_state.open_notes[self.project.folder]:
                # if file still exists
                if os.path.exists(filn):
                    self.open_document(filn)

    def save_appstate(self):
        print('save appstate')
        self.update_open_notes()
        now = int(time.time())
        too_old = now - 31 * 24 * 60 * 60
        if self.project:
            # only keep files that exist
            pfolder = self.project.folder
            if pfolder in self.app_state.open_notes:
                open_notes = self.app_state.open_notes[pfolder]
                self.app_state.open_notes[pfolder] = [f for f in open_notes if os.path.exists(f)]
            else:
                self.app_state.open_notes[pfolder] = []
            if pfolder in self.app_state.recently_viewed:
                rv = self.app_state.recently_viewed[pfolder]
                self.app_state.recently_viewed[pfolder] = {f: t for f, t in rv.items() if os.path.exists(f) and t > too_old} # keep only files that exist and have been viewed within the last 30 days
            else:
                self.app_state.recently_viewed[pfolder] = {}
        self.app_state.save()

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

    def open_document(self, document_filn, is_settings_file=False, editor_type=None):
        """
        Helper function to open a markdown or settings document in a new tab
        """
        # if it exists or not, we start watching. it might jump into existence
        self.notes_watcher.on_file_open(document_filn)

        #check if exists
        tab_index, editor = self.document_to_index_editor(document_filn)
        if os.path.exists(document_filn):
            # only if file exists
            self.app_state.register_note_access(self.project.folder, document_filn)
        if editor:
            # if file in editor: open it
            # if file removed from disk but still in open editor, open it
            self.gui.qtabs.setCurrentIndex(tab_index)
            editor.setFocus()
            return editor

        if not os.path.exists(document_filn):
            return
        
        # make new editor from file
        if is_settings_file:
            if editor_type is None:
                editor_type = 'settings'
            editor = SettingsEditor(self.gui.theme, document_filn, editor_type)
        else:
            editor = self.gui.new_zk_editor(document_filn, settings = self.project.settings)
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
        
        if self.gui.qtabs.count() == 1:
            # if this is the first tab, i.e. there was no editor before:
            pass
        self.gui.notelist_panel.add_note_filn(document_filn)
        return editor
    ''''''

    def fuzzy_open(self):
        extension = self.project.settings.get('markdown_extension')
        note_list_dict = {f: f for f in [os.path.basename(x).replace(extension, '') for x in self.project.get_all_note_files()]}
        selected_note, _ = show_fuzzy_panel(self.gui.qtabs, 'Open Note', note_list_dict)

        if selected_note:
            the_path = os.path.join(self.project.folder, selected_note + extension)
            if os.path.exists(the_path):
                self.open_document(the_path)
    ''''''

    def close_current_tab(self):
        self.tab_close_requested(self.gui.qtabs.currentIndex())

    def cycle_tabs_forward(self):
        index = self.gui.qtabs.currentIndex()
        index += 1
        if index >= self.gui.qtabs.count():
            index = 0
        self.gui.qtabs.setCurrentIndex(index)

    def cycle_tabs_backward(self):
        index = self.gui.qtabs.currentIndex()
        index -= 1
        if index <0:
            index = self.gui.qtabs.count() - 1
        self.gui.qtabs.setCurrentIndex(index)

    def validate_json(self, editor, on_error):
        txt = editor.text()
        try:
            _ = json.loads(txt)
            return True
        except JSONDecodeError as e:
            if on_error:
                e.lineno = get_real_error_lineno(txt, e.lineno)
                on_error(editor, e)
        return False

    def save(self):
        tab_index = self.gui.qtabs.currentIndex()
        editor = self.gui.qtabs.currentWidget()
        if editor:
            if editor.editor_type == 'theme' or editor.editor_type == 'settings' or editor.editor_type == 'build-commands':
                txt = editor.text()
                if not self.validate_json(editor, self.on_settings_editor_json_error):
                    return
            # ignore watching this file for now
            self.notes_watcher.on_ignore_clicked(editor.file_name)
            with open(editor.file_name, mode='w', encoding='utf-8', errors='ignore') as f:
                f.write(editor.text())
            # start tracking this file again
            self.notes_watcher.on_file_saved(editor.file_name)

            editor.setModified(False)
            self.gui.qtabs.setTabText(tab_index, os.path.basename(editor.file_name))
            # Settings changed
            if editor.editor_type == 'settings':
                test_settings = get_settings(on_error=self.on_settings_editor_json_error)
                self.project.reload_settings()
            elif editor.editor_type == 'theme':
                if os.path.basename(editor.file_name) == self.gui.theme.theme_name + '.json':
                    # load the theme
                    theme_f = os.path.basename(editor.file_name)
                    theme = Theme(theme_f)
                    self.gui.apply_theme(new_theme=theme)
                    #QMessageBox.information(self.gui, 'Please restart', 'Please restart Sublime_ZK for the theme changes to take effect.')

        # always save saved searches
        editor = self.gui.saved_searches_editor
        with open(self.project.get_saved_searches_filn(),
                  mode='w', encoding='utf-8', errors='ignore') as f:
            f.write(editor.text())
        editor.setModified(False)

    def save_all(self):
        for tab_index in range(self.gui.qtabs.count()):
            editor = self.gui.qtabs.widget(tab_index)
            if editor and editor.isModified():
                self.notes_watcher.on_ignore_clicked(editor.file_name)
                with open(editor.file_name, mode='w', encoding='utf-8', errors='ignore') as f:
                    f.write(editor.text())
                editor.setModified(False)
                self.notes_watcher.on_file_saved(editor.file_name)
                self.gui.qtabs.setTabText(tab_index, os.path.basename(editor.file_name))

        # always save saved searches
        editor = self.gui.saved_searches_editor
        with open(self.project.get_saved_searches_filn(),
                  mode='w', encoding='utf-8', errors='ignore') as f:
            f.write(editor.text())
        editor.setModified(False)

    def show_preferences(self, filn=None):
        if not filn:
            filn = settings_filn
        editor = self.open_document(filn, is_settings_file=True)
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
                textbytes = bytearray(editor.text(), "utf-8")
                suggested_title = textbytes[sel_start:sel_end].decode('utf-8')
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

        input_text = input_text.strip()

        settings = self.project.settings
        extension = settings.get('markdown_extension')
        id_in_title = settings.get('id_in_title')

        new_id = self.project.timestamp()
        the_file = os.path.join(self.project.folder, new_id + ' ' + sanitize_filename(input_text) + extension)
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
        sort, order = self.retrieve_sort_and_order()
        note_files = self.project.get_all_note_files()
        self.project.externalize_note_links(note_files, f'# All Notes ({len(note_files)})', sort=sort, order=order)
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
        selected_tag, _ = show_fuzzy_panel(self.gui.qtabs, 'Insert Tag', tag_list_dict)
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
        if not editor:
            return
        if not isinstance(note_id, str):
            link, editor_region = self.project.select_link_in_editor(editor)
            if not editor_region:
                return
            note_id = self.project.cut_after_note_id(link)
            if not note_id:
                return
            print(note_id, editor_region)
        ref_note_files = self.project.find_referencing_notes(note_id)
        filn = self.project.note_file_by_id(note_id)
        title = os.path.basename(filn).split(' ', 1)[1].strip().rsplit('.')[0]
        styled_link = self.project.style_link(note_id, title, force_title=True)
        self.project.externalize_note_links(ref_note_files, f'# {len(ref_note_files)} Notes referencing {styled_link}')
        self.reload(self.gui.search_results_editor)

    def reload_bibfile(self):
        bibfile = Autobib.look_for_bibfile(self.project)
        if not bibfile:
            return
        self._show_status_message(f'Loading {bibfile} ...')
        settings = self.project.settings
        convert_to_unicode = settings.get('convert_bibtex_to_unicode', False)

        self.bib_entries = Autobib.extract_all_entries(bibfile, unicode_conversion=convert_to_unicode)
        self.gui.statusBar().clearMessage()

    def insert_citation(self, pos=None):
        print('insert citation')
        editor = self.get_active_editor()
        if not isinstance(editor, ZettelkastenScintilla):
            return
        
        if self.bib_entries is None:
            self.reload_bibfile()

        if self.bib_entries is None:
            bibfile = Autobib.look_for_bibfile(self.project)
            self.gui.statusBar().showMessage('No .bib file found!', 3000)
            return

        ck_choices = {}
        for citekey, d in self.bib_entries.items():
            if not d['authors']:
                d['authors'] = d['editors']
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
            line_num_start, index_start = editor.lineIndexFromPosition(self.project.convert_pos_to_bytepos(editor.text(), toc_start))
            line_num_end, index_end = editor.lineIndexFromPosition(self.project.convert_pos_to_bytepos(editor.text(), toc_end))
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

        settings = self.project.settings
        skip_first_heading = settings.get('skip_first_heading_when_numbering', False)
        if skip_first_heading:
            headings_to_skip = 1

        while True:
            for heading_index, heading_match in enumerate(heading_matcher.finditer(text)):
                if heading_index < headings_to_skip:
                    continue
                headings_to_skip += 1
                heading = heading_match.group()
                match = re.match(r'(\s*)(#+)(\s*[0-9.]*\s)(.*)', heading)
                if not match:
                    continue
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

        settings = self.project.settings
        skip_first_heading = settings.get('skip_first_heading_when_numbering', False)
        if skip_first_heading:
            headings_to_skip = 1

        while True:
            for heading_index, heading_match in enumerate(heading_matcher.finditer(text)):
                if heading_index < headings_to_skip:
                    continue
                headings_to_skip += 1
                heading = heading_match.group()
                match = re.match(r'(\s*)(#+)(\s*[0-9.]*\s)(.*)', heading)
                if not match:
                    continue
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

    def parse_current_search_attrs(self, spec):
        p_sub = re.compile(r'\s*?(=\w*?\(.*?\)\s*?)?{sortby:\s*?(id|title|refcount|mtime|history)\s*?(,\s*?order:\s*?(asc|desc))?\s*}')
        
        match = p_sub.search(spec)
        attrs = {
            'function': None,
            'args': {},
            'sortby': None,
            'order': None,
            }
        if match:
            if match.group(1):
                # parse function into args and name
                p_foo = re.compile(r'\s*?=(\w+)\((.*?)\)')
                sub_match = p_foo.match(match.group(1))
                if sub_match:
                    attrs['function'] = sub_match.group(1)
                    t_args = sub_match.group(2).split(',')
                    args = {}
                    for t_arg in t_args:
                        kv = t_arg.split(':')
                        if len(kv) == 2:
                            key, value = kv
                            attrs['args'][key.strip()] = value.strip()
            if match.group(2):
                attrs['sortby'] = match.group(2)
            if match.group(4):
                attrs['order'] = match.group(4).lower()
        # now remove attrs from the spec
        new_spec = p_sub.sub('', spec)
        return new_spec, attrs
 

    def advanced_tag_search(self, search_spec=None):
        if not search_spec:
            search_spec = show_input_panel(None, '#tags and not !#tags:', '')
        if not search_spec:
            return
        # get search attrs and strip them from search term
        search_spec, attrs = self.parse_current_search_attrs(search_spec)
        
        # remember current search attrs
        self.current_search_attrs = attrs
        sort, order = self.retrieve_sort_and_order()

        if search_spec.startswith('[!'):
            self.show_all_notes(check_editor=False)
            self.current_search_attrs = None
            return
        elif search_spec.startswith('#!'):
            self.show_all_tags(check_editor=False)
            self.current_search_attrs = None
            return

        if search_spec.strip().startswith('#') or search_spec.startswith('!#'):
            notes = TagSearch.advanced_tag_search(search_spec, self.project)
            notes = [self.project.note_file_by_id(note_id) for note_id in notes]
            self.project.externalize_note_links(notes, f'# {len(notes)} Notes matching search ' + search_spec, sort=sort, order=order)
            self.reload(self.gui.search_results_editor)
        elif 'function' in attrs and attrs['function'] is not None:
            if attrs['function'] == 'refcounts':
                # sanitize args
                args = self.current_search_attrs['args']
                try:
                    refmin = int(args.get('min', 0))
                except ValueError:
                    refmin = 0
                try:
                    refmax = int(args.get('max', 1000))
                except ValueError:
                    refmax = 1000
                self.current_search_attrs['args']['min'] = refmin
                self.current_search_attrs['args']['max'] = refmax
                self.find_notes_with_refcounts()
            elif attrs['function'] == 'view_history':
                self.show_recent_views()
        elif search_spec:
            self.find_in_files(search_spec)
        self.current_search_attrs = None
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

        # auto-save if auto-save is on, instead of nagging us
        if self.autosave_interval > 0:
            self.save_all()
        else:
            if editor.isModified():
                msg = f"You have unsaved changes in {os.path.basename(editor.file_name)} Close anyway?"
                buttonReply = QMessageBox.question(editor, 'Unsaved Changes', msg, QMessageBox.Yes | QMessageBox.No,
                                                QMessageBox.No)
                if buttonReply == QMessageBox.No:
                    return    # ignore
        self.gui.qtabs.removeTab(index)
        self.gui.notelist_panel.remove_note_filn(editor.file_name)
        self.notes_watcher.on_file_closed(editor.file_name)

    def about(self):
        about = AboutDlg(self.gui)
        about.exec_()

    def find_in_files(self, search_terms=None):
        sort, order = self.retrieve_sort_and_order()
        if not search_terms:
            suggested_terms = ''
            editor = self.get_active_editor()
            if editor and editor.hasSelectedText():
                sel = editor.getSelection()
                sel_start = editor.positionFromLineIndex(sel[0], sel[1])
                sel_end = editor.positionFromLineIndex(sel[2], sel[3])
                textbytes = bytearray(editor.text(), "utf-8")
                suggested_terms = textbytes[sel_start:sel_end].decode('utf-8')
            search_terms = show_input_panel(None, 'Find in files:', suggested_terms)
        if not search_terms:
            return
        orig_search_terms = search_terms

        search_terms = search_terms.lower()
        search_terms = split_search_terms(search_terms)

        note_files = self.project.get_all_note_files()
        result_notes = []
        for note in note_files:
            with open(note, mode='r', encoding='utf-8', errors='ignore') as f:
                text = f.read().lower()
                for presence, search_term in search_terms:
                    if presence and search_term not in text:
                        break
                    elif not presence and search_term in text:
                        break
                else:
                    result_notes.append(note)
        self.project.externalize_note_links(result_notes, f'# {len(result_notes)} Notes matching search ' + orig_search_terms, sort=sort, order=order)
        self.reload(self.gui.search_results_editor)
        return result_notes

    def new_theme(self):
        theme_name = show_input_panel(self.gui, 'New Theme:', 'custom')
        if not theme_name:
            return
        theme_path = Theme.prepare_new_theme(theme_name, self.gui.theme.theme_name)
        editor = self.open_document(theme_path, is_settings_file=True)
        return editor

    def edit_theme(self):
        filp = Theme.get_named_theme_path(self.gui.theme.theme_name)
        editor = self.open_document(filp, is_settings_file=True, editor_type='theme')
        return editor

    def switch_theme(self):
        available_themes = Theme.list_available_themes()
        theme_list_dict = {t: t for t in available_themes}
        selected_theme, _ = show_fuzzy_panel(self.gui, 'Switch to Theme', theme_list_dict)
        if selected_theme:
            if selected_theme == self.gui.theme.theme_name:
                return
            settings_raw = get_settings(raw=True)
            repl_with = f'"theme": "themes/{selected_theme + ".json"}",'

            re_what = re.compile(r'"theme":.*$', flags=re.MULTILINE)
            settings_raw = re_what.sub(repl_with, settings_raw)

            with open(settings_filn, mode='w', encoding='utf-8', errors='ignore') as f:
                f.write(settings_raw)
            # load the theme
            theme_f = os.path.basename(get_settings().get('theme', 'Office.json'))
            theme = Theme(theme_f)
            self.gui.apply_theme(new_theme=theme)
            #QMessageBox.information(self.gui,'New Theme selected', f'Please restart Sublimeless_ZK to load the {selected_theme} theme')

    def rename_note(self):
        editor = self.get_active_editor()
        if not editor:
            return
        if editor.editor_type != 'normal':
            return
        note_filn = os.path.basename(editor.file_name)
        note_id, title = os.path.splitext(os.path.basename(note_filn))[0].split(' ', 1)
        new_title = show_input_panel(self.gui, 'New Title:', title)
        if not new_title:
            return
        new_title = new_title.strip()
        if new_title == title:
            return
        self.save()
        settings = self.project.settings
        extension = settings.get('markdown_extension', '.md')
        new_note_filn = os.path.join(self.project.folder, f'{note_id} {sanitize_filename(new_title)}{extension}')
        os.rename(editor.file_name, new_note_filn)
        # close tab
        index = self.gui.qtabs.currentIndex()
        self.gui.qtabs.removeTab(index)
        self.open_document(new_note_filn)

    def delete_note(self):
        editor = self.get_active_editor()
        if not editor:
            return
        if editor.editor_type != 'normal':
            return
        note_filn = os.path.basename(editor.file_name)
        msg = f"Are you sure you want to delete note {note_filn} ?"
        buttonReply = QMessageBox.question(self.gui, 'Delete Note', msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if buttonReply == QMessageBox.Yes:
            try:
                os.unlink(editor.file_name)
            except:
                pass
            # close tab
            index = self.gui.qtabs.currentIndex()
            self.gui.qtabs.removeTab(index)

    def export_to_html(self):
        dlg = SemanticZKDialog(None, 'Export notes to HTML', self.project)
        return dlg.exec_()

    def quit_application(self):
        self.gui.close()
    
    def show_command_palette(self):
        editor = self.get_active_editor()   # for maybe later: external command

        d = {x: x for x in self.command_palette_actions.keys()}

        # add external commands
        settings_dir = os.path.join(self.app_state.home, 'sublimeless_zk.rc')
        templates_dir = base_dir()
        bc = BuildCommands(settings_dir, templates_dir)
        command_names = list(bc.commands.keys())
        command_names_dict = {'> ' + cn: cn for cn in command_names}
        d.update(command_names_dict)
        actionText, aux =show_fuzzy_panel(self.gui, 'Run command', d)
        if actionText:
            if actionText.startswith('>'):
                # it is an external command
                self._run_external_command(aux, editor)
            else:
                self.command_palette_actions[actionText].activate(QAction.Trigger)
    
    def show_hide_sidepanel(self):
        if self.gui.saved_searches_editor.isVisible():
            self.gui.saved_searches_editor.setVisible(False)
            self.gui.search_results_editor.setVisible(False)
        else:
            self.gui.saved_searches_editor.setVisible(True)
            self.gui.search_results_editor.setVisible(True)
            
    def toggle_statusbar(self):
        self.gui.statusBar().setVisible(not self.gui.statusBar().isVisible())
    
    def toggle_auto_indent(self):
        editor = self.get_active_editor()
        if not editor:
            return
        if editor.editor_type == 'normal':
            editor.toggle_auto_indent()
        
    def toggle_indentation_guides(self):
        editor = self.get_active_editor()
        if not editor:
            return
        if editor.editor_type == 'normal':
            editor.toggle_indentation_guides()
    
    def toggle_use_tabs(self):
        editor = self.get_active_editor()
        if not editor:
            return
        if editor.editor_type == 'normal':
            editor.toggle_use_tabs()

    def toggle_wrap_indent(self):
        editor = self.get_active_editor()
        if not editor:
            return
        if editor.editor_type == 'normal':
            editor.toggle_wrap_indent()
    
    def toggle_wrap_line(self):
        editor = self.get_active_editor()
        if not editor:
            return
        if editor.editor_type == 'normal':
            editor.toggle_wrap_line()
    
    def toggle_wrap_markers(self):
        editor = self.get_active_editor()
        if not editor:
            return
        if editor.editor_type == 'normal':
            editor.toggle_wrap_markers()

    def run_external_command(self):
        editor = self.get_active_editor()
        if not editor:
            return
        settings_dir = os.path.join(self.app_state.home, 'sublimeless_zk.rc')
        templates_dir = base_dir()
        bc = BuildCommands(settings_dir, templates_dir)
        command_names = list(bc.commands.keys())
        command_names_dict = {cn: cn for cn in command_names}
        selected_command, _ = show_fuzzy_panel(self.gui.qtabs, 'Run external command', command_names_dict)
        if selected_command:
            self._run_external_command(selected_command, editor)
        return

    def _show_status_message(self, msg):
        self.gui.statusBar().showMessage(msg)
        # call the event loop to show the status message
        loop = QEventLoop()
        QTimer.singleShot(1, loop.quit)
        loop.exec_()

    def _run_external_command(self, selected_command, editor):
        if not editor:
            return
        settings_dir = os.path.join(self.app_state.home, 'sublimeless_zk.rc')
        templates_dir = base_dir()
        bc = BuildCommands(settings_dir, templates_dir)
        note_name, ext = os.path.splitext(editor.file_name)
        tmpf = tempfile.NamedTemporaryFile()    # create and close
        tempfile_name = tmpf.name
        tmpf.close() # close and delete
        new_note_id = self.project.timestamp()
        vars_dict = {
            'note_path': os.path.dirname(note_name) + os.path.sep,
            'note_name': os.path.basename(note_name),
            'note_ext': ext,
            'bib': Autobib.look_for_bibfile(self.project),   # up-to-date
            'tempfile': tempfile_name,
            'new_note_id': new_note_id
        }
        vars_dict = defaultdict(dict, **vars_dict)
        if selected_command and selected_command in bc.commands:
            cmd_json_dict = bc.commands[selected_command]
            self._show_status_message(f'Running {selected_command} ...')
            return_code, stdout, args = bc.run_build_command(selected_command, vars_dict)
            if return_code == 0:
                on_finish_dict = cmd_json_dict.get('on_finish', dict())
                if 'open' in on_finish_dict:
                    output_filn = on_finish_dict['open'].format(**vars_dict)
                    if os.path.exists(output_filn):
                        self._show_status_message(f'Opening {output_filn} ...')
                        if sys.platform == 'darwin':
                            subprocess.call(['open', output_filn])
                        elif sys.platform == 'win32':
                            os.startfile(output_filn)
                        else:
                            # assume linux
                            subprocess.call(('LD_LIBRARY_PATH="" ; xdg-open  ' + output_filn), shell=True)
                if on_finish_dict.get('reload_note', False):
                    self.reload(editor)
                if on_finish_dict.get('open_new_note', False):
                    # try to open the note with the new note_id
                    self.clicked_noteid(new_note_id)
            else:
                on_error_dict = cmd_json_dict.get('on_error', dict())
                if on_error_dict.get('show_error', False):
                    error_text = ' '.join(args) + '\n\n' + stdout
                    QMessageBox.information(self.gui, f'Error running {selected_command}', stdout)
            self.gui.statusBar().clearMessage()
        return
    
    def edit_external_commands(self):
        settings_dir = os.path.join(self.app_state.home, 'sublimeless_zk.rc')
        templates_dir = base_dir()
        bc = BuildCommands(settings_dir, templates_dir)
        filp = bc.filn
        editor = self.open_document(filp, is_settings_file=True, editor_type='build-commands')
    
    def goto(self):
        """
        Go to open tab / heading
        """
        selections = {}
        heading_re = re.compile(r'^#{1,6}\s')
        for i in range(self.gui.qtabs.count()):
            editor = self.gui.qtabs.widget(i)
            if editor.editor_type == 'normal':
                note_id, title = self.project.get_note_id_and_title_of(editor)
                selections[f'{note_id} {title}'] = note_id
                # now come the headings
                for line_index, line in enumerate(editor.text().split('\n')):
                    if heading_re.match(line):
                        selections[line] = f'{note_id}:{line_index}'
        if selections:
            selected_text, associated_noteid = show_fuzzy_panel(self.gui.qtabs, 'Goto open note', selections)
            if selected_text:
                if ':' in associated_noteid:
                    note_id, line_index = associated_noteid.split(':')
                    line_index = int(line_index)
                else:
                    note_id = associated_noteid
                    line_index = -1
                editor = self.clicked_noteid(note_id, ctrl=False, alt=False, shift=False)
                if line_index != -1:
                    stop_index = min(line_index + 5, editor.lines())
                    editor.setCursorPosition(stop_index, 0)   # ensure we're below the line
                    editor.setCursorPosition(line_index, 0)

    def mainwindow_close_handler(self):
        self.save_appstate()
        if self.autosave_interval > 0:
            self.save_all()
            return True
        editor_list = [self.gui.qtabs.widget(i) for i in range(self.gui.qtabs.count())]
        for editor in editor_list:
            if editor.isModified():
                msg = "You have unsaved changes. Quit anyway?"
                buttonReply = QMessageBox.question(self.gui, 'Unsaved Changes', msg, QMessageBox.Yes | QMessageBox.No,
                                                   QMessageBox.No)
                if buttonReply == QMessageBox.Yes:
                    return True
                else:
                    return False
        return True
    
    def retrieve_sort_and_order(self):
        sort = None
        order = None
        if self.current_search_attrs:
            sort = self.current_search_attrs.get('sortby', None)
            order = self.current_search_attrs.get('order', None)
        return sort, order

    def find_notes_with_refcounts(self):
        sort, order = self.retrieve_sort_and_order()
        if self.current_search_attrs is None:
            refmin, refmax = show_find_refcount_dlg(self.gui)
        else:
            args = self.current_search_attrs['args']
            refmin = int(args.get('min', 0))
            refmax = int(args.get('max', 1000))

        if refmin is None:
            return
        
        d = self.project.get_notes_with_refcounts(refmin, refmax)
        title = f'# {len(d)} Notes with min. {refmin} and max. {refmax} references'
        note_files = [x[2] for x in d.values()]
        refcounts = {note_id: x[0] for note_id, x in d.items()} # produce a dict of refcounts 
        
        self.project.externalize_note_links(note_files, prefix=title, refcounts=refcounts, sort=sort, order=order)
        self.reload(self.gui.search_results_editor)
        
    def move_line_up(self):
        editor = self.get_active_editor()
        if not editor:
            return
        line_index, col_index = editor.getCursorPosition()
        if line_index == 0:
            return
        lines = editor.text().split('\n')
        new_lines = lines[:line_index - 1]
        new_lines.extend([lines[line_index], lines[line_index - 1]])
        new_lines.extend(lines[line_index + 1:])
        editor.setText('\n'.join(new_lines))
        editor.ensureLineVisible(line_index + 1)
        editor.setCursorPosition(line_index - 1, col_index)

    def move_line_down(self):
        editor = self.get_active_editor()
        if not editor:
            return
        line_index, col_index = editor.getCursorPosition()
        if line_index == editor.lines() - 1:
            return
        lines = editor.text().split('\n')
        new_lines = lines[:line_index]
        new_lines.extend([lines[line_index + 1], lines[line_index]])
        new_lines.extend(lines[line_index + 2:])
        editor.setText('\n'.join(new_lines))
        editor.ensureLineVisible(line_index + 1)
        editor.setCursorPosition(line_index + 1, col_index)

    def show_recent_views(self):
        d = self.app_state.recently_viewed.get(self.project.folder, {})
        now = int(time.time())
        days30 = now - 30 * 24 * 60 * 60
        days7 = now - 7 * 24 * 60 * 60
        hours24 = now - 24 * 60 * 60
        hour1 = now - 60 * 60

        # sort and filter
        hour_notes = {note_filn: t for t, note_filn in sorted([(t, note_filn) for note_filn, t in d.items() if t > hour1])}
        day_notes = {note_filn: t for t, note_filn in sorted([(t, note_filn) for note_filn, t in d.items() if t > hours24 and note_filn not in hour_notes])}
        week_notes = {note_filn: t for t, note_filn in sorted([(t, note_filn) for note_filn, t in d.items() if t > days7 and note_filn not in hour_notes and note_filn not in day_notes])}
        rest_notes = {note_filn: t for t, note_filn in sorted([(t, note_filn) for note_filn, t in d.items() if t > days30 and note_filn not in hour_notes and note_filn not in day_notes and note_filn not in week_notes])}

        lines = ['# Recently Opened Notes']
        for desc, d in {'Last hour': hour_notes, 'Last 24 hours': day_notes, 'Last 7 days': week_notes, 'Last 30 days': rest_notes}.items():
            lines.append(f'\n## {desc}')
            fake_refcounts = {os.path.basename(filn).split(' ', 1)[0]: t for filn, t in d.items()}
            note_files = list(d.keys())
            lines.extend(self.project.externalize_note_links(note_files, refcounts=fake_refcounts, sort='refcount', order='desc', do_write=False))
        self.gui.search_results_editor.setText('\n'.join(lines))

    def toggle_open_files_panel(self):
        self.gui.notelist_panel.setVisible(not self.gui.notelist_panel.isVisible())        

    def open_hyperlink(self, hyperlink):
        open_hyperlink(hyperlink)
            










if __name__ == '__main__':
    Sublimeless_Zk().run()
