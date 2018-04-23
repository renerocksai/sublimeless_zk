# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.Qsci import *
from PyQt5.QtCore import Qt

from zkscintilla import ZettelkastenScintilla
from zkmdlexer import ZkMdLexer
from themes import Theme
from settings import base_dir


class MainWindow(QMainWindow):
    def __init__(self, theme):
        super(MainWindow, self).__init__()

        # load theme
        self.theme = theme

        self.setGeometry(300, 200, 800, 600)
        self.setWindowTitle("Sublimeless Zettelkasten")
        self.setStyleSheet("QTabBar{font: 8px;}")

        self._frm = QFrame(self)
        self._frm.setStyleSheet("QWidget { background-color: #ffeaeaea }")
        self._lyt = QVBoxLayout()
        self._frm.setLayout(self._lyt)
        self.setCentralWidget(self._frm)
        self._myFont = QFont()
        self._myFont.setPointSize(14)

        self._btn = QPushButton("Qsci")
        self._btn.setFixedWidth(50)
        self._btn.setFixedHeight(50)
        self._btn.clicked.connect(self._btn_action)
        self._btn.setFont(self._myFont)
        #self._lyt.addWidget(self._btn)


        self.qtabs = QTabWidget()

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
        self.qtabs.setTabsClosable(True)
        self.show()

    def _btn_action(self):
        print("Hello World!")

    def recommended_editor_width(self, editor):
        font_metrics = QFontMetrics(editor.lexer().default_font)
        max_width = 150
        for line in editor.text().split('\n'):
            max_width = max(max_width, font_metrics.width(line))
        return max_width + 2 * 10 + 20    # 2 * margin width (we have 2 margins)

    def new_zk_editor(self, filn=None):
        editor = ZettelkastenScintilla(document_filn=filn)
        editor.setUtf8(True)             # Set encoding to UTF-8
        if filn:
            with open(filn,
                      mode='r', encoding='utf-8', errors='ignore') as f:
                txt = f.read()
            editor.setText(txt)
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
        editor.setScrollWidthTracking(True)
        editor.setMarginType(0, QsciScintilla.SymbolMargin)
        editor.setMarginWidth(0, "0")        # todo: do we want margins?
        editor.setMarginWidth(1, "")
        editor.setMarginsForegroundColor(QColor("#ff888888"))
        editor.setMarginsBackgroundColor(QColor(self.theme.style_infos['default']['background']))

        show_block_quotes = True
        lexer = ZkMdLexer(editor, self.theme, highlight_saved_searches=False, show_block_quotes=show_block_quotes)
        editor.setLexer(lexer)
        editor.set_calculation_font(lexer.default_font)

        editor.setCaretForegroundColor(QColor(lexer.theme.caret))
        editor.setCaretLineVisible(True)
        editor.setCaretLineBackgroundColor(QColor(lexer.theme.highlight))
        editor.setCaretWidth(8)
        #editor.setMarginsBackgroundColor(QColor("#ff404040"))
        editor.setFont(lexer.default_font)
        editor.setExtraAscent(self.theme.line_pad_top)
        editor.setExtraDescent(self.theme.line_pad_bottom)

        # give it a good size
        editor.setMinimumWidth(QFontMetrics(editor.lexer().default_font).width('M' * 80))
        return editor

    def make_search_results_editor(self):
        editor = ZettelkastenScintilla(editor_type='searchresults')
        editor.setUtf8(True)             # Set encoding to UTF-8

        editor.setLexer(None)
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

        theme = Theme(f'{base_dir()}/themes/search_results.json')

        lexer = ZkMdLexer(editor, theme, highlight_saved_searches=False, show_block_quotes=False)
        editor.setLexer(lexer)
        editor.set_calculation_font(lexer.default_font)

        editor.setCaretForegroundColor(QColor(lexer.theme.caret))
        editor.setCaretLineVisible(True)
        editor.setCaretLineBackgroundColor(QColor(lexer.theme.highlight))
        editor.setCaretWidth(8)
        #editor.setMarginsBackgroundColor(QColor("#ff404040"))
        editor.setFont(lexer.default_font)
        editor.setExtraAscent(theme.line_pad_top)
        editor.setExtraDescent(theme.line_pad_bottom)

        editor.setMinimumWidth(self.recommended_editor_width(editor))
        editor.setMinimumWidth(QFontMetrics(editor.lexer().default_font).width('M' * 80))
        editor.setMaximumWidth(800)
        return editor

    def make_saved_searches_editor(self):
        editor = ZettelkastenScintilla(editor_type='savedsearches')
        editor.setUtf8(True)             # Set encoding to UTF-8

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

        theme = Theme(f'{base_dir()}/themes/saved_searches.json')

        lexer = ZkMdLexer(editor, theme, highlight_saved_searches=True, show_block_quotes=False)
        editor.setLexer(lexer)
        editor.set_calculation_font(lexer.default_font)

        editor.setCaretForegroundColor(QColor(lexer.theme.caret))
        editor.setCaretLineVisible(True)
        editor.setCaretLineBackgroundColor(QColor(lexer.theme.highlight))
        editor.setCaretWidth(8)
        #editor.setMarginsBackgroundColor(QColor("#ff404040"))
        editor.setFont(lexer.default_font)
        editor.setExtraAscent(theme.line_pad_top)
        editor.setExtraDescent(theme.line_pad_bottom)

        editor.setMinimumWidth(self.recommended_editor_width(editor))
        editor.setMinimumWidth(QFontMetrics(editor.lexer().default_font).width('M' * 80) + 20 + 12)
        editor.setMaximumWidth(1024)
        return editor

    def closeEvent(self, event):
        editor_list = [self.qtabs.widget(i) for i in range(self.qtabs.count())]
        for editor in editor_list:
            if editor.isModified():
                msg = "You have unsaved changes. Quit anyway?"
                buttonReply = QMessageBox.question(self, 'Unsaved Changes', msg, QMessageBox.Yes | QMessageBox.No,
                                                   QMessageBox.No)
                if buttonReply == QMessageBox.Yes:
                    pass
                else:
                    event.ignore()
                break

