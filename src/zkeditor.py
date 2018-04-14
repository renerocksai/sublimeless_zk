# -*- coding: utf-8 -*-
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.Qsci import *

from zkmdlexer import ZkMdLexer

''' end Class '''


class CustomMainWindow(QMainWindow):
    def __init__(self):
        super(CustomMainWindow, self).__init__()

        # -------------------------------- #
        #           Window setup           #
        # -------------------------------- #

        # 1. Define the geometry of the main window
        # ------------------------------------------
        self.setGeometry(300, 300, 800, 400)
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
        self._lyt.addWidget(self._btn)

        # -------------------------------- #
        #     QScintilla editor setup      #
        # -------------------------------- #

        # ! Make instance of QSciScintilla class!
        # ----------------------------------------
        self._editor = QsciScintilla()
        self._editor.setUtf8(True)             # Set encoding to UTF-8
        with open('../zettelkasten/201803100758 P.md', mode='r', encoding='utf-8', errors='ignore') as f:
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
        self._editor.setEolMode(QsciScintilla.EolWindows)
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
        if True:
            self._lexer = ZkMdLexer(self._editor, '../theme.json')
            self._editor.setLexer(self._lexer)

        # 4. Caret
        # ---------
        self._editor.setCaretForegroundColor(QColor(self._lexer.theme.caret))
        self._editor.setCaretLineVisible(True)
        self._editor.setCaretLineBackgroundColor(QColor(self._lexer.theme.highlight))
        self._editor.setCaretWidth(8)
        #self._editor.setMarginsBackgroundColor(QColor("#ff404040"))
        self._editor.setFont(self._lexer.default_font)

        # ! Add editor to layout !
        # -------------------------
        self._lyt.addWidget(self._editor)
        self.show()

    ''''''

    def _btn_action(self):
        print("Hello World!")
    ''''''

''' End Class '''

if __name__ == '__main__':
    app = QApplication(sys.argv)
    QApplication.setStyle(QStyleFactory.create('Fusion'))
    myGUI = CustomMainWindow()

    sys.exit(app.exec_())

''''''
