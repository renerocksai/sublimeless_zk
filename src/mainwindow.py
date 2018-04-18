# -*- coding: utf-8 -*-
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.Qsci import *
from PyQt5.QtCore import Qt

from imagescintilla import ImageScintilla
from zkmdlexer import ZkMdLexer
from themes import Theme


class MainWindow(QMainWindow):
    def __init__(self, theme):
        super(MainWindow, self).__init__()

        # load theme
        self.theme = theme
        # -------------------------------- #
        #           Window setup           #
        # -------------------------------- #

        # 1. Define the geometry of the main window
        # ------------------------------------------
        self.setGeometry(300, 200, 800, 600)
        self.setWindowTitle("Sublimeless Zettelkasten")

        # 2. Create frame and layout
        # ---------------------------
        self._frm = QFrame(self)
        self._frm.setStyleSheet("QWidget { background-color: #ffeaeaea }")
        self._lyt = QVBoxLayout()
        self._frm.setLayout(self._lyt)
        self.setCentralWidget(self._frm)
        self._myFont = QFont()
        self._myFont.setPointSize(14)

        # 3. Place a button
        # ------------------
        self._btn = QPushButton("Qsci")
        self._btn.setFixedWidth(50)
        self._btn.setFixedHeight(50)
        self._btn.clicked.connect(self._btn_action)
        self._btn.setFont(self._myFont)
        #self._lyt.addWidget(self._btn)

        # -------------------------------- #
        #     QScintilla editor setup      #
        # -------------------------------- #

        # ! Make instance of QSciScintilla class!
        # ----------------------------------------
        self.editor = ImageScintilla()
        self.editor.setUtf8(True)             # Set encoding to UTF-8
        with open('../zettelkasten/201804141018 testnote.md',
                  mode='r', encoding='utf-8', errors='ignore') as f:
            txt = f.read()
        self.editor.setText(txt)     # 'myCodeSample' is a string containing some C-code
        self.editor.setLexer(None)            # We install lexer later
        #self.editor.setFont(self._myFont)    # Gets overridden by lexer later on

        # 1. Text wrapping
        # -----------------
        self.editor.setWrapMode(QsciScintilla.WrapWord)
        self.editor.setWrapVisualFlags(QsciScintilla.WrapFlagByText)
        self.editor.setWrapIndentMode(QsciScintilla.WrapIndentIndented)

        # 2. End-of-line mode
        # --------------------
        self.editor.setEolMode(QsciScintilla.EolUnix)
        self.editor.setEolVisibility(False)

        # 3. Indentation
        # ---------------
        self.editor.setIndentationsUseTabs(False)
        self.editor.setTabWidth(4)
        self.editor.setIndentationGuides(True)
        self.editor.setTabIndents(True)
        self.editor.setAutoIndent(True)


        # 5. Margins
        # -----------
        # Margin 0 = Line nr margin
        #self.editor.setMarginType(0, QsciScintilla.NumberMargin)
        self.editor.setMarginType(0, QsciScintilla.SymbolMargin)
        self.editor.setMarginWidth(0, "0000")
        self.editor.setMarginWidth(1, "0000")
        self.editor.setMarginsForegroundColor(QColor("#ff888888"))

        # -------------------------------- #
        #          Install lexer           #
        # -------------------------------- #
        self.lexer = ZkMdLexer(self.editor, self.theme, highlight_saved_searches=False)
        self.editor.setLexer(self.lexer)
        self.editor.set_calculation_font(self.lexer.default_font)

        # 4. Caret
        # ---------
        self.editor.setCaretForegroundColor(QColor(self.lexer.theme.caret))
        self.editor.setCaretLineVisible(True)
        self.editor.setCaretLineBackgroundColor(QColor(self.lexer.theme.highlight))
        self.editor.setCaretWidth(8)
        #self.editor.setMarginsBackgroundColor(QColor("#ff404040"))
        self.editor.setFont(self.lexer.default_font)
        self.editor.setExtraAscent(self.theme.line_pad_top)
        self.editor.setExtraDescent(self.theme.line_pad_bottom)

        # give it a good size
        self.editor.setMinimumWidth(QFontMetrics(self.editor.lexer().default_font).width('M' * 80))

        # ! Add editor to layout !
        # -------------------------
        self.qtabs = QTabWidget()
        # Set up the tabs
        # self.qtabs.tabCloseRequested.connect(self.tab.removeTab)
        # self.qtabs.tabCloseRequested.connect(self.lessTabs)

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

        self.qtabs.setMovable(True)
        self.qtabs.setDocumentMode(True)
        self._lyt.addWidget(mainsplit)
        self.setUnifiedTitleAndToolBarOnMac(True)
        self.qtabs.addTab(self.editor, '201804141018 testnote.md')
        self.qtabs.setTabsClosable(True)

        self.show()

    ''''''

    def _btn_action(self):
        print("Hello World!")
    ''''''

    def recommended_editor_width(self, editor):
        font_metrics = QFontMetrics(editor.lexer().default_font)
        max_width = 150
        for line in editor.text().split('\n'):
            max_width = max(max_width, font_metrics.width(line))
        return max_width + 2 * 10 + 10    # 2 * margin width (we have 2 margins)

    def make_search_results_editor(self):
        editor = QsciScintilla()
        editor.setUtf8(True)             # Set encoding to UTF-8
        with open('../search_results_default.md',
                  mode='r', encoding='utf-8', errors='ignore') as f:
            txt = f.read()
        editor.setText(txt)     # 'myCodeSample' is a string containing some C-code
        editor.setLexer(None)            # We install lexer later
        editor.setWrapMode(QsciScintilla.WrapWord)
        editor.setWrapVisualFlags(QsciScintilla.WrapFlagByText)
        editor.setWrapIndentMode(QsciScintilla.WrapIndentIndented)

        editor.setEolMode(QsciScintilla.EolUnix)
        editor.setEolVisibility(False)

        editor.setIndentationsUseTabs(False)
        editor.setTabWidth(4)
        editor.setIndentationGuides(True)
        editor.setTabIndents(True)
        editor.setAutoIndent(True)

        editor.setMarginType(0, QsciScintilla.SymbolMargin)
        editor.setMarginWidth(0, 10)
        editor.setMarginWidth(1, 10)
        editor.setMarginsForegroundColor(QColor("#ff888888"))

        theme = Theme('../themes/search_results.json')

        lexer = ZkMdLexer(editor, theme, highlight_saved_searches=False, show_block_quotes=False)
        editor.setLexer(lexer)

        editor.setCaretForegroundColor(QColor(lexer.theme.caret))
        editor.setCaretLineVisible(True)
        editor.setCaretLineBackgroundColor(QColor(lexer.theme.highlight))
        editor.setCaretWidth(8)
        #editor.setMarginsBackgroundColor(QColor("#ff404040"))
        editor.setFont(lexer.default_font)
        editor.setExtraAscent(theme.line_pad_top)
        editor.setExtraDescent(theme.line_pad_bottom)

        editor.setMinimumWidth(self.recommended_editor_width(editor))
        editor.setMaximumWidth(800)
        return editor

    def make_saved_searches_editor(self):
        editor = QsciScintilla()
        editor.setUtf8(True)             # Set encoding to UTF-8
        with open('../saved_searches_default.md',
                  mode='r', encoding='utf-8', errors='ignore') as f:
            txt = f.read()
        editor.setText(txt)     # 'myCodeSample' is a string containing some C-code
        editor.setLexer(None)            # We install lexer later
        editor.setWrapMode(QsciScintilla.WrapWord)
        editor.setWrapVisualFlags(QsciScintilla.WrapFlagByText)
        editor.setWrapIndentMode(QsciScintilla.WrapIndentIndented)

        editor.setEolMode(QsciScintilla.EolUnix)
        editor.setEolVisibility(False)

        editor.setIndentationsUseTabs(False)
        editor.setTabWidth(8)
        editor.setIndentationGuides(True)
        editor.setTabIndents(True)
        editor.setAutoIndent(True)

        editor.setMarginType(0, QsciScintilla.SymbolMargin)
        editor.setMarginWidth(0, 10)
        editor.setMarginWidth(1, 10)
        editor.setMarginsForegroundColor(QColor("#ff888888"))

        theme = Theme('../themes/saved_searches.json')

        lexer = ZkMdLexer(editor, theme, highlight_saved_searches=True, show_block_quotes=False)
        editor.setLexer(lexer)

        editor.setCaretForegroundColor(QColor(lexer.theme.caret))
        editor.setCaretLineVisible(True)
        editor.setCaretLineBackgroundColor(QColor(lexer.theme.highlight))
        editor.setCaretWidth(8)
        #editor.setMarginsBackgroundColor(QColor("#ff404040"))
        editor.setFont(lexer.default_font)
        editor.setExtraAscent(theme.line_pad_top)
        editor.setExtraDescent(theme.line_pad_bottom)

        editor.setMinimumWidth(self.recommended_editor_width(editor))
        editor.setMaximumWidth(1024)
        return editor

    def on_search_results_changed(self):
        # todo
        pass


''' End Class '''

