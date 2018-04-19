import jstyleson as json
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.Qsci import *
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QObject, pyqtSignal

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
    settings_saved = pyqtSignal()
    settings_discarded = pyqtSignal()

    def __init__(self, theme, settings_filn):
        super().__init__()
        self.theme = theme
        self.settings_filn = settings_filn
        self.editor = None
        self.lexer = None
        self.initUI()

    def initUI(self):
        vlay = QVBoxLayout(self)

        self.editor = ZettelkastenScintilla()
        self.editor.setUtf8(True)  # Set encoding to UTF-8
        txt = get_settings(self.settings_filn, raw=True)
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

        self.editor.setCaretForegroundColor(QColor(self.lexer.theme.caret))
        self.editor.setCaretLineVisible(True)
        self.editor.setCaretLineBackgroundColor(QColor(self.lexer.theme.highlight))
        self.editor.setCaretWidth(8)

        self.editor.setFont(self.lexer.default_font)
        self.editor.setExtraAscent(self.theme.line_pad_top)
        self.editor.setExtraDescent(self.theme.line_pad_bottom)

        # give it a good size
        self.editor.setMinimumWidth(QFontMetrics(self.editor.lexer().default_font).width('M' * 80))

        vlay.addWidget(self.editor)
        hlay = QHBoxLayout()
        self.btsave = QPushButton('Save')
        self.btcancel = QPushButton('Discard')
        hlay.addWidget(self.btsave)
        hlay.addWidget(self.btcancel)
        vlay.addLayout(hlay)
        self.setLayout(vlay)

        self.btsave.clicked.connect(self.save_clicked)
        self.btcancel.clicked.connect(self.discard_clicked)

    def save_clicked(self):
        with open(self.settings_filn, mode='w', encoding='utf-8', errors='ignore') as f:
            f.write(self.editor.text())
            self.settings_saved.emit()

    def discard_clicked(self):
        self.settings_discarded.emit()
