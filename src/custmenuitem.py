"""
A custom menu item to show sortcuts that are not QShortcuts
"""

from PyQt5.QtWidgets import QAction
from PyQt5.Qt import QFont, QFontMetrics


def makelongenough(text, w=20, p=False, font=None):
    compare_text = 'M' * w
    if font is None:
        font = QFont('Helvetica', 8)
    m = QFontMetrics(font)
    target_width = m.width(compare_text)
    while m.width(text) <= target_width:
        a = m.width(text)
        if p:
            return text
            text = ' ' + text
        else:
            text += ' '
    return text

class CustomMenuItemAction(QAction):
    def __init__(self, menutext, parent):
        super().__init__(menutext, parent)
        self.menutext = menutext
        self.gui = parent.gui

    def setShortcut(self, shortcut):
        self.setText(f'{makelongenough(self.text(), font=self.gui.font())}{makelongenough(shortcut, 8, True, font=self.gui.font())}  ')

    def setShortcuts(self, shortcuts):
        self.setText(f'{makelongenough(self.text(), font=self.gui.font())}{makelongenough(" or ".join(shortcuts), 8, True, font=self.gui.font())}  ')

