from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


class InputPanel(QDialog):
    def __init__(self, parent, label, defaulttext):
        super(InputPanel, self).__init__(parent=parent)

        self.setWindowFlags(Qt.FramelessWindowHint)
        self._text = ''
        self.setObjectName("self")
        hlay = QHBoxLayout(self)
        hlay.addWidget(QLabel(label))
        self.line_edit = QLineEdit()
        self.line_edit.setText(defaulttext)
        hlay.addWidget(self.line_edit)
        self.setLayout(hlay)
        self.setMinimumWidth(600)
        self.line_edit.returnPressed.connect(self._ok_clicked)
        self.line_edit.setFocus()

        self.setStyleSheet("""
            QLineEdit{ background-color: #ffffff; }
            InputPanel { background: #f0f0f0; }
            QLabel{ background: #d08080; }
            QDialog {
                    background: #d08080;
                    }

        """)

    def _ok_clicked(self):
        self._text = self.line_edit.text()
        self.done(1)

    def text(self):
        return self._text


def show_input_panel(parent, label, defaulttext):
    ip = InputPanel(parent, label, defaulttext)
    if parent:
        ip.move(parent.rect().center() - ip.rect().center())
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
    show_input_panel(gui, 'Label', 'Default')
    sys.exit(app.exec_())

