import jstyleson as json
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.Qsci import *
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QObject

from zkscintilla import ZettelkastenScintilla
from zkmdlexer import ZkMdLexer


def get_settings(filn='../settings_default.json', raw=False):
    with open(filn,
              mode='r', encoding='utf-8', errors='ignore') as f:
        txt = f.read()
        if raw:
            return txt
        else:
            return json.loads(txt)


class SettingsEditor(QWidget):
    def __init__(self, theme):
        super().__init__()
        self.theme = theme
        self.editor = None
        self.lexer = None
        self.initUI()

    def initUI(self):
        vlay = QVBoxLayout(self)

        self.editor = ZettelkastenScintilla()
        self.editor.setUtf8(True)  # Set encoding to UTF-8
        txt = get_settings(raw=True)
        self.editor.setText(txt)  # 'myCodeSample' is a string containing some C-code
        self.editor.setLexer(None)  # We install self.lexer later
        # self.editor.setFont(self._myFont)    # Gets overridden by self.lexer later on

        self.editor.setWrapMode(QsciScintilla.WrapWord)
        self.editor.setWrapVisualFlags(QsciScintilla.WrapFlagByText)
        self.editor.setWrapIndentMode(QsciScintilla.WrapIndentIndented)

        self.editor.setEolMode(QsciScintilla.EolUnix)
        self.editor.setEolVisibility(False)

        self.editor.setIndentationsUseTabs(False)
        self.editor.setTabWidth(4)
        self.editor.setIndentationGuides(True)
        self.editor.setTabIndents(True)
        self.editor.setAutoIndent(True)

        self.editor.setMarginType(0, QsciScintilla.SymbolMargin)
        self.editor.setMarginWidth(0, "0000")
        self.editor.setMarginWidth(1, "0000")
        self.editor.setMarginsForegroundColor(QColor("#ff888888"))

        self.lexer = ZkMdLexer(self.editor, self.theme, highlight_saved_searches=False, show_block_quotes=False, settings_mode=True)
        self.editor.setLexer(self.lexer)
        self.editor.set_calculation_font(self.lexer.default_font)

        # 4. Caret
        # ---------
        self.editor.setCaretForegroundColor(QColor(self.lexer.theme.caret))
        self.editor.setCaretLineVisible(True)
        self.editor.setCaretLineBackgroundColor(QColor(self.lexer.theme.highlight))
        self.editor.setCaretWidth(8)
        # self.editor.setMarginsBackgroundColor(QColor("#ff404040"))
        self.editor.setFont(self.lexer.default_font)
        self.editor.setExtraAscent(self.theme.line_pad_top)
        self.editor.setExtraDescent(self.theme.line_pad_bottom)

        # give it a good size
        self.editor.setMinimumWidth(QFontMetrics(self.editor.lexer().default_font).width('M' * 80))

        vlay.addWidget(self.editor)
        hlay = QHBoxLayout()
        btsave = QPushButton('Save')
        btcancel = QPushButton('Discard')
        hlay.addWidget(btsave)
        hlay.addWidget(btcancel)
        vlay.addLayout(hlay)
        self.setLayout(vlay)
