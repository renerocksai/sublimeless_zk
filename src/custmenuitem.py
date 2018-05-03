"""
A custom menu item to show sortcuts that are not QShortcuts
"""

from PyQt5.QtWidgets import QAction



class CustomMenuItemAction(QAction):
    def __init__(self, menutext, parent):
        super().__init__(menutext, parent)
        self.menutext = menutext

    def setShortcut(self, shortcut):
        self.setText(f'{self.text()}        {shortcut}')

    def setShortcuts(self, shortcuts):
        self.setText(f'{self.text()}    {" or ".join(shortcuts)}')

