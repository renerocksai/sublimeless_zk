from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from fuzzyfinder import fuzzyfinder


def fuzzymatch(string, stringlist):
    pass

class PanelInputLine(QLineEdit):
    down_pressed = pyqtSignal()
    up_pressed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet('background-color:#ffffff')

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        key = event.key()
        if key == Qt.Key_Down:
            self.down_pressed.emit()
        elif key == Qt.Key_Up:
            self.up_pressed.emit()


class FuzzySearchPanel(QWidget):
    item_selected = pyqtSignal(str, str)    # key, value
    close_requested = pyqtSignal()

    def __init__(self, parent=None, item_dict=None, max_items=20):
        super().__init__(parent)
        self.max_items = max_items
        self.setObjectName("FuzzySearchPanel")
        self.item_dict = item_dict    #    { show_as: associated_value }
        if self.item_dict is None:
            self.item_dict = {}

        self.fuzzy_items = list(self.item_dict.keys())[:max_items]
        self.initUI()

    def initUI(self):
        vlay = QVBoxLayout()
        self.input_line = PanelInputLine()
        self.list_box = QListWidget()
        for i in range(self.max_items):
            self.list_box.insertItem(i, '')
        vlay.addWidget(self.input_line)
        vlay.addWidget(self.list_box)
        self.update_listbox()
        self.setLayout(vlay)
        self.setMinimumWidth(600)
        self.list_box.setAlternatingRowColors(True)

        # style
        self.setStyleSheet(""" QListWidget:item:selected{
                                    background: lightblue;
                                    border: 1px solid #6a6ea9;
                                }
                                QListWidget{
                                    background: #f0f0f0;
                                    show-decoration-selected: 1;                                
                                }
                                QListWidget::item:alternate {
                                    background: #E0E0E0;
                                }    
                                QLineEdit {
                                background-color: #ffffff;
                                }             
                                """
                           )

        # connections
        self.input_line.textChanged.connect(self.text_changed)
        self.input_line.returnPressed.connect(self.return_pressed)
        self.input_line.down_pressed.connect(self.down_pressed)
        self.input_line.up_pressed.connect(self.up_pressed)
        self.list_box.itemDoubleClicked.connect(self.item_doubleclicked)
        self.list_box.installEventFilter(self)
        self.input_line.setFocus()

    def update_listbox(self):
        for i in range(self.max_items):
            item = self.list_box.item(i)
            if i < len(self.fuzzy_items):
                item.setHidden(False)
                item.setText(self.fuzzy_items[i])
            else:
                item.setHidden(True)
        self.list_box.setCurrentRow(0)

    def text_changed(self):
        search_string = self.input_line.text()
        if search_string:
            self.fuzzy_items = list(fuzzyfinder(search_string, self.item_dict.keys()))[:self.max_items]
        else:
            self.fuzzy_items = list(self.item_dict.keys())[:self.max_items]
        self.update_listbox()

    def up_pressed(self):
        row = self.list_box.currentRow()
        if row > 0:
            self.list_box.setCurrentRow(row - 1)

    def down_pressed(self):
        row = self.list_box.currentRow()
        if row < len(self.fuzzy_items):
            self.list_box.setCurrentRow(row + 1)

    def return_pressed(self):
        if len(self.fuzzy_items) > 0:
            row = self.list_box.currentRow()
            key = self.fuzzy_items[row]
            value = self.item_dict[key]
            self.item_selected.emit(key, value)


    def item_doubleclicked(self):
        row = self.list_box.currentRow()
        key = self.fuzzy_items[row]
        value = self.item_dict[key]
        self.item_selected.emit(key, value)
    
    def eventFilter(self, watched, event):
        if event.type() == QEvent.KeyPress and event.matches(QKeySequence.InsertParagraphSeparator):
            return_pressed()
            return True
        else:
            return QWidget.eventFilter(self, watched, event)


class FuzzySearchDialog(QDialog):
    def __init__(self, parent, title, item_dict, max_items=20):
        super(FuzzySearchDialog, self).__init__(parent=parent)
        self.setObjectName("self")
        self.setWindowTitle(title)
        hlay = QHBoxLayout()
        self.panel = FuzzySearchPanel(item_dict=item_dict, max_items=max_items)
        hlay.addWidget(self.panel)
        self.setLayout(hlay)

        self.panel.close_requested.connect(self.cancel)
        self.panel.item_selected.connect(self.item_selected)
        self.value = None
        self.panel.input_line.setFocus()
        # style
        self.setStyleSheet(""" QDialog {
                                    background: #ffffff;
                                }
                                """
                           )

    def item_selected(self, key, value):
        self.value = (key, value)
        self.done(1)

    def cancel(self):
        self.done(0)


def show_fuzzy_panel(parent, title, item_dict, max_items=50, longlines=False, manylines=False):
    dlg = FuzzySearchDialog(parent, title, item_dict, max_items)
    if parent:
        pass
        #dlg.move(parent.rect().center() - dlg.rect().center())
    if longlines:
        dlg.setMinimumWidth(1024)
    if manylines:
        dlg.setMinimumHeight(400)
    ret = dlg.exec_()
    if ret:
        return dlg.value
    else:
        return None, None
