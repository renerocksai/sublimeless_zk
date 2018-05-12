# -*- coding: utf-8 -*-
import sys
import os
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.Qsci import *
from PyQt5.QtCore import Qt, pyqtSignal

from zkscintilla import ZettelkastenScintilla
from zkmdlexer import ZkMdLexer
from themes import Theme
from settings import base_dir


class MainWindow(QMainWindow):    
    def __init__(self, theme, close_handler):
        super(MainWindow, self).__init__()

        # load theme
        self.theme = theme
        self.close_handler = close_handler
        
        self.setGeometry(300, 200, 900, 600)
        self.setWindowTitle("Sublimeless Zettelkasten")
        self.setStyleSheet("QTabBar{font: 8px;}")

        self._frm = QFrame(self)
        self._frm.setStyleSheet("QWidget { background-color: #ffeaeaea }")
        self._lyt = QVBoxLayout()
        self._frm.setLayout(self._lyt)
        self.setCentralWidget(self._frm)
        self._myFont = QFont()
        self._myFont.setPointSize(14)

        self.qtabs = QTabWidget()
        # start with a 50:50 split
        self.qtabs.setGeometry(0,0,300,600)

        mainsplit = QSplitter()
        mainsplit.setOrientation(Qt.Horizontal)
        subsplit = QSplitter()
        self.search_results_editor = self.make_search_results_editor()
        self.saved_searches_editor = self.make_saved_searches_editor()
        subsplit.addWidget(self.search_results_editor)
        subsplit.addWidget(self.saved_searches_editor)
        subsplit.setOrientation(Qt.Vertical)
        mainsplit.addWidget(self.qtabs)
        mainsplit.addWidget(subsplit)
        mainsplit.setCollapsible(0, False)
        mainsplit.setCollapsible(1, False)

        self.qtabs.setMovable(True)
        self.qtabs.setDocumentMode(True)
        self._lyt.addWidget(mainsplit)
        self.setUnifiedTitleAndToolBarOnMac(True)
        self.qtabs.setTabsClosable(True)
        if sys.platform == 'win32':
            self.setWindowIcon(QIcon(f"{os.path.join(base_dir(), 'sublimeless_zk.ico')}"))
            
        self.tab_spaces_label = QLabel('')
        self.tab_spaces_label.setStyleSheet('QLabel{ font: 9px; color: #606060; }')
        self.line_count_label = QLabel('')
        self.line_count_label.setStyleSheet('QLabel{ font: 9px; color: #303030; }')
        self.word_count_label = QLabel('')
        self.word_count_label.setStyleSheet('QLabel{ font: 9px; color: #303030; }')
        self.statusBar().addPermanentWidget(self.tab_spaces_label)
        spc = QWidget()
        spc.setMinimumWidth(20)

        self.statusBar().addPermanentWidget(spc)
        self.statusBar().addPermanentWidget(self.line_count_label)
        self.statusBar().addPermanentWidget(self.word_count_label)
        self.statusBar().showMessage('Welcome to Sublimeless_ZK', 3000)
        self.show()

    def new_zk_editor(self, filn=None, settings=None):
        editor = ZettelkastenScintilla(document_filn=filn)
        editor.setUtf8(True)             # Set encoding to UTF-8
        if filn:
            with open(filn,
                      mode='r', encoding='utf-8', errors='ignore') as f:
                txt = f.read()
            editor.setText(txt)
        editor.setLexer(None)            # We install lexer later

        if settings is None:
            settings = {}
        
        wrapmode = QsciScintilla.WrapWord
        wrapvisual = QsciScintilla.WrapFlagByText
        wrapindentmode = QsciScintilla.WrapIndentIndented
        autoindent = True
        indentationguides = True
        usetabs = False

        if settings.get('wrap_lines', True) == False:
            wrapmode = QsciScintilla.WrapNone
        if settings.get('show_wrap_markers', True) == False:
            wrapvisual = QsciScintilla.WrapFlagNone
        if settings.get('indent_wrapped_lines', True) == False:
            wrapindentmode = QsciScintilla.WrapIndentSame
        if settings.get('auto_indent', True) == False:
            autoindent = False
        if settings.get('show_indentation_guides', True) == False:
            indentationguides = False
        if settings.get('use_tabs', False) == True:
            usetabs = True

        editor.setWrapMode(wrapmode)
        editor.setWrapVisualFlags(wrapvisual)
        editor.visual_flags = wrapvisual
        editor.setWrapIndentMode(wrapindentmode)

        editor.setEolMode(QsciScintilla.EolUnix)
        editor.setEolVisibility(False)

        editor.setIndentationsUseTabs(usetabs)
        editor.setTabWidth(4)
        editor.setIndentationGuides(indentationguides)
        editor.setTabIndents(True)
        editor.setAutoIndent(autoindent)
        editor.setScrollWidthTracking(True)
        editor.setMarginType(0, QsciScintilla.SymbolMargin)
        editor.setMarginWidth(0, "0")        # todo: do we want margins?
        editor.setMarginWidth(1, "")
        editor.setMarginsForegroundColor(QColor("#ff888888"))

        show_block_quotes = True
        lexer = ZkMdLexer(editor, self.theme, highlight_saved_searches=False, show_block_quotes=show_block_quotes)
        editor.setLexer(lexer)
        editor.setCaretLineVisible(True)
        editor.setCaretWidth(8)
        #editor.setMarginsBackgroundColor(QColor("#ff404040"))

        # give it a good size
        editor.setMinimumWidth(QFontMetrics(editor.lexer().default_font).width('M' * 20))
        self.apply_theme(editor)
        return editor

    def apply_theme(self, editors=None, new_theme=None):
        if new_theme is not None:
            self.theme = new_theme
        if editors is not None:
            # got passed in a single editor
            if not isinstance(editors, list):
                editors = [editors]
        else:
            editors = [self.qtabs.widget(i) for i in range(self.qtabs.count())]

        for editor in editors:
            lexer = editor.lexer()
            lexer.apply_theme(self.theme)
            editor.setMarginsBackgroundColor(QColor(self.theme.style_infos['default']['background']))
            editor.set_calculation_font(lexer.default_font)
            editor.setCaretForegroundColor(QColor(lexer.theme.caret))
            editor.setCaretLineBackgroundColor(QColor(lexer.theme.highlight))
            editor.setFont(lexer.default_font)
            editor.setExtraAscent(self.theme.line_pad_top)
            editor.setExtraDescent(self.theme.line_pad_bottom)


    def format_editor_info(self, editor):
        if editor.indentationsUseTabs():
            usetabs = 'TAB'
        else:
            usetabs = 'SPC'
        
        if editor.wrapMode() == QsciScintilla.WrapWord:
            wrapmode = 'Wrap:Y'
        else:
            wrapmode = 'Wrap:N'
        
        if editor.visual_flags == QsciScintilla.WrapFlagByText:
            wrapmode += '+show'
        
        if editor.wrapIndentMode() == QsciScintilla.WrapIndentIndented:
            wrapmode += '+indent'
        
        if editor.autoIndent() == True:
            autoindent = 'Indent:auto'
        else:
            autoindent = 'Indent:no'
        
        if editor.indentationGuides() == True:
            guides = 'Guides:yes'
        else:
            guides = 'Guides:no'
        
        self.tab_spaces_label.setText(f'{usetabs:20} {wrapmode:20} {autoindent:20} {guides:20}')
        return

    def make_search_results_editor(self):
        editor = ZettelkastenScintilla(editor_type='searchresults')
        editor.setUtf8(True)             # Set encoding to UTF-8

        editor.setLexer(None)
        editor.setWrapMode(QsciScintilla.WrapWord)
        editor.setWrapVisualFlags(QsciScintilla.WrapFlagNone)
        editor.setWrapIndentMode(QsciScintilla.WrapIndentSame)

        editor.setEolMode(QsciScintilla.EolUnix)
        editor.setEolVisibility(False)

        editor.setIndentationsUseTabs(False)
        editor.setTabWidth(4)
        editor.setIndentationGuides(False)
        editor.setTabIndents(True)
        editor.setAutoIndent(True)

        editor.setMarginType(0, QsciScintilla.SymbolMargin)
        editor.setMarginWidth(0, 10)
        editor.setMarginWidth(1, 10)
        editor.setMarginsForegroundColor(QColor("#ff888888"))

        theme = Theme(f'{base_dir()}/themes/search_results.json')

        lexer = ZkMdLexer(editor, theme, highlight_saved_searches=False, show_block_quotes=False)
        editor.setLexer(lexer)
        editor.set_calculation_font(lexer.default_font)

        editor.setCaretForegroundColor(QColor(lexer.theme.caret))
        editor.setCaretLineVisible(True)
        editor.setCaretLineBackgroundColor(QColor(lexer.theme.highlight))
        editor.setCaretWidth(2)
        editor.setMarginsBackgroundColor(QColor(theme.background))
        editor.setFont(lexer.default_font)
        editor.setExtraAscent(theme.line_pad_top)
        editor.setExtraDescent(theme.line_pad_bottom)

        # no minimum width
        return editor

    def make_saved_searches_editor(self):
        editor = ZettelkastenScintilla(editor_type='savedsearches')
        editor.setUtf8(True)             # Set encoding to UTF-8

        editor.setLexer(None)            # We install lexer later
        editor.setWrapMode(QsciScintilla.WrapWord)
        editor.setWrapVisualFlags(QsciScintilla.WrapFlagNone)
        editor.setWrapIndentMode(QsciScintilla.WrapIndentSame)

        editor.setEolMode(QsciScintilla.EolUnix)
        editor.setEolVisibility(False)

        editor.setIndentationsUseTabs(False)
        editor.setTabWidth(4)
        editor.setIndentationGuides(False)
        editor.setTabIndents(True)
        editor.setAutoIndent(True)

        editor.setMarginType(0, QsciScintilla.SymbolMargin)
        editor.setMarginWidth(0, 10)
        editor.setMarginWidth(1, 10)
        editor.setMarginsForegroundColor(QColor("#ff888888"))

        theme = Theme(f'{base_dir()}/themes/saved_searches.json')

        lexer = ZkMdLexer(editor, theme, highlight_saved_searches=True, show_block_quotes=False)
        editor.setLexer(lexer)
        editor.set_calculation_font(lexer.default_font)

        editor.setCaretForegroundColor(QColor(lexer.theme.caret))
        editor.setCaretLineVisible(True)
        editor.setCaretLineBackgroundColor(QColor(lexer.theme.highlight))
        editor.setCaretWidth(2)
        editor.setMarginsBackgroundColor(QColor(theme.background))
        editor.setFont(lexer.default_font)
        editor.setExtraAscent(theme.line_pad_top)
        editor.setExtraDescent(theme.line_pad_bottom)

        # no minimum width
        return editor
        

    def closeEvent(self, event):
        if self.close_handler() == False:
            event.ignore()
