from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


class InputPanel(QDialog):
    def __init__(self, title, label, defaulttext):
        super(InputPanel, self).__init__()
        self._text = ''
        self.setObjectName("self")
        self.setWindowTitle(title)
        hlay = QHBoxLayout(self)
        hlay.addWidget(QLabel(label))
        self.line_edit = QLineEdit()
        self.line_edit.setText(defaulttext)
        hlay.addWidget(self.line_edit)
        self.setLayout(hlay)
        self.setMinimumWidth(600)
        self.bt_ok = QPushButton("OK")
        hlay.addWidget(self.bt_ok)
        self.bt_ok.clicked.connect(self._ok_clicked)

    def _ok_clicked(self):
        self._text = self.line_edit.text()
        self.done(1)

    def text(self):
        return self._text


def show_input_panel(title, label, defaulttext):
    ip = InputPanel(title, label, defaulttext)
    ret = ip.exec_()
    if ret:
        return ip.text()
    else:
        return None


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    QApplication.setStyle(QStyleFactory.create('Fusion'))
    gui = QMainWindow()
    gui.setFocus()
    gui.show()
    show_input_panel('Title', 'Label', 'Default')
    sys.exit(app.exec_())

