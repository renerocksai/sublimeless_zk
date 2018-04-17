# -*- coding: utf-8 -*-
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.Qsci import *
from PyQt5.QtCore import Qt

from imagescintilla import ImageScintilla
from zkmdlexer import ZkMdLexer
from themes import Theme

''' end Class '''


class CustomMainWindow(QMainWindow):
    def __init__(self, theme):
        super(CustomMainWindow, self).__init__()

        # load theme
        self.theme = theme
        # -------------------------------- #
        #           Window setup           #
        # -------------------------------- #

        # 1. Define the geometry of the main window
        # ------------------------------------------
        self.setGeometry(300, 200, 800, 600)
        self.setWindowTitle("QScintilla Test")

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
        self._editor = ImageScintilla()
        self._editor.setUtf8(True)             # Set encoding to UTF-8
        with open('../zettelkasten/201804141018 testnote.md',
                  mode='r', encoding='utf-8', errors='ignore') as f:
            txt = f.read()
        self._editor.setText(txt)     # 'myCodeSample' is a string containing some C-code
        self._editor.setLexer(None)            # We install lexer later
        #self._editor.setFont(self._myFont)    # Gets overridden by lexer later on

        # 1. Text wrapping
        # -----------------
        self._editor.setWrapMode(QsciScintilla.WrapWord)
        self._editor.setWrapVisualFlags(QsciScintilla.WrapFlagByText)
        self._editor.setWrapIndentMode(QsciScintilla.WrapIndentIndented)

        # 2. End-of-line mode
        # --------------------
        self._editor.setEolMode(QsciScintilla.EolUnix)
        self._editor.setEolVisibility(False)

        # 3. Indentation
        # ---------------
        self._editor.setIndentationsUseTabs(False)
        self._editor.setTabWidth(4)
        self._editor.setIndentationGuides(True)
        self._editor.setTabIndents(True)
        self._editor.setAutoIndent(True)


        # 5. Margins
        # -----------
        # Margin 0 = Line nr margin
        #self._editor.setMarginType(0, QsciScintilla.NumberMargin)
        self._editor.setMarginType(0, QsciScintilla.SymbolMargin)
        self._editor.setMarginWidth(0, "0000")
        self._editor.setMarginWidth(1, "0000")
        self._editor.setMarginsForegroundColor(QColor("#ff888888"))

        # -------------------------------- #
        #          Install lexer           #
        # -------------------------------- #
        self._lexer = ZkMdLexer(self._editor, self.theme, highlight_saved_searches=False)
        self._editor.setLexer(self._lexer)
        self._editor.set_calculation_font(self._lexer.default_font)

        # 4. Caret
        # ---------
        self._editor.setCaretForegroundColor(QColor(self._lexer.theme.caret))
        self._editor.setCaretLineVisible(True)
        self._editor.setCaretLineBackgroundColor(QColor(self._lexer.theme.highlight))
        self._editor.setCaretWidth(8)
        #self._editor.setMarginsBackgroundColor(QColor("#ff404040"))
        self._editor.setFont(self._lexer.default_font)
        self._editor.setExtraAscent(self.theme.line_pad_top)
        self._editor.setExtraDescent(self.theme.line_pad_bottom)

        # connect zettelkasten signals
        self._lexer.tag_clicked.connect(self.clicked_tag)
        self._lexer.note_id_clicked.connect(self.clicked_noteid)

        # ! Add editor to layout !
        # -------------------------
        tabba = QTabWidget()
        # Set up the tabs
        # tabba.tabCloseRequested.connect(self.tab.removeTab)
        # tabba.tabCloseRequested.connect(self.lessTabs)

        mainsplit = QSplitter()
        mainsplit.setOrientation(Qt.Horizontal)
        subsplit = QSplitter()
        subsplit.addWidget(self.make_search_results_editor())
        subsplit.addWidget(QLabel('world'))
        subsplit.setOrientation(Qt.Vertical)
        mainsplit.addWidget(tabba)
        mainsplit.addWidget(subsplit)

        tabba.setMovable(True)
        tabba.setDocumentMode(True)
        self._lyt.addWidget(mainsplit)
        self.setUnifiedTitleAndToolBarOnMac(True)
        tabba.addTab(self._editor, '201804141018 testnote.md')
        tabba.setTabsClosable(True)
        self.show()

    ''''''

    def _btn_action(self):
        print("Hello World!")
    ''''''

    def clicked_noteid(self, noteid, ctrl, alt, shift):
        print('noteid', noteid, ctrl, alt, shift)

    def clicked_tag(self, tag, ctrl, alt, shift):
        print('tag', tag)

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
        editor.setMarginWidth(0, "00")
        editor.setMarginWidth(1, "00")
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

        # connect zettelkasten signals
        lexer.tag_clicked.connect(self.clicked_tag)
        lexer.note_id_clicked.connect(self.clicked_noteid)
        editor.setMinimumWidth(460)
        editor.setMaximumWidth(800)
        return editor

    def on_search_results_changed(self):
        pass

''' End Class '''

if __name__ == '__main__':
    app = QApplication(sys.argv)
    QApplication.setStyle(QStyleFactory.create('Fusion'))
    theme = Theme('../themes/solarized_light.json')
    myGUI = CustomMainWindow(theme)

    sys.exit(app.exec_())

''''''
