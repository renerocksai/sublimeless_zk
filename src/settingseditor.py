from PyQt5.QtGui import *
from PyQt5.Qsci import *

from zkscintilla import ZettelkastenScintilla
from zkmdlexer import ZkMdLexer



def SettingsEditor(theme, settings_filn, editor_type=None):
    if editor_type is None:
        editor_type = 'settings'
    editor = ZettelkastenScintilla(document_filn=settings_filn, editor_type=editor_type)

    editor.setUtf8(True)  # Set encoding to UTF-8
    txt = f'Unable to load file {settings_filn}'
    with open(settings_filn, mode='r', encoding='utf-8', errors='ignore') as f:
        txt = f.read()
    editor.setText(txt)  # 'myCodeSample' is a string containing some C-code
    editor.setLexer(None)  # We install lexer later
    # editor.setFont(self._myFont)    # Gets overridden by lexer later on

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
    editor.setMarginWidth(0, "")
    editor.setMarginWidth(1, "")
    editor.setMarginsForegroundColor(QColor("#ff888888"))

    lexer = ZkMdLexer(editor, theme, highlight_saved_searches=False, show_block_quotes=False,
                      settings_mode=True)
    editor.setLexer(lexer)
    editor.set_calculation_font(lexer.default_font)

    editor.setCaretForegroundColor(QColor(lexer.theme.caret))
    editor.setCaretLineVisible(True)
    editor.setCaretLineBackgroundColor(QColor(lexer.theme.highlight))
    editor.setCaretWidth(8)

    editor.setFont(lexer.default_font)
    # editor.setExtraAscent(theme.line_pad_top)
    # editor.setExtraDescent(theme.line_pad_bottom)
    return editor

