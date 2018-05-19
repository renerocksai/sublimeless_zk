from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import os

class OpenNotesPanel(QListWidget):
    file_clicked = pyqtSignal(str)
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.filn2path = {}
        self.itemClicked.connect(self.item_clicked)
    
    def clear(self):
        super().clear()
        self.filn2path = {}

    def add_note_filn(self, filn):
        basename = os.path.basename(filn)
        self.filn2path[basename] = filn
        self.addItem(basename)
        self.sortItems()

    def remove_note_filn(self, filn):
        basename = os.path.basename(filn)
        for i in range(self.count()):
            item = self.item(i)
            if item.text() == basename:
                self.takeItem(i)
                break
        self.filn2path = {k: v for k, v in self.filn2path.items() if k != basename}

    def item_clicked(self, item):
        basename = item.text()
        if basename in self.filn2path:
            self.file_clicked.emit(self.filn2path[basename])
        