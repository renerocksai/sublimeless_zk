from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


class FindRefcountDlg(QDialog):

    def __init__(self, parent):
        super().__init__(parent=parent)
        self._min = 0
        self._max = 0

        self.setWindowTitle('Find notes with references')
        vlay = QVBoxLayout()
        hlaymin = QHBoxLayout()
        lblmin = QLabel('Minimum number of references')
        self.spinmin = QSpinBox()
        self.spinmin.setMaximum(1000000)
        hlaymin.addWidget(lblmin)
        hlaymin.addWidget(self.spinmin)

        hlaymax = QHBoxLayout()
        lblmax = QLabel('Maximum number of references')
        self.spinmax = QSpinBox()
        self.spinmax.setMaximum(1000000)
        self.spinmax.setMinimum(1)
        self.spinmax.setValue(1000)
        hlaymax.addWidget(lblmax)
        hlaymax.addWidget(self.spinmax)

        hlaybt = QHBoxLayout()
        self.okbt = QPushButton('OK')
        self.cancelbt = QPushButton('Cancel')
        hlaybt.addWidget(self.cancelbt)
        hlaybt.addWidget(self.okbt)
           
        vlay.addLayout(hlaymin)
        vlay.addLayout(hlaymax)
        vlay.addLayout(hlaybt)
        self.setLayout(vlay)
        self.setMinimumWidth(600)

        self.setStyleSheet("""
            QDialog {
                    background: #80d0d0;
                    }

        """)
        self.okbt.clicked.connect(self.ok_clicked)
        self.okbt.setAutoDefault(True)
        self.cancelbt.clicked.connect(self.cancel_clicked)
        self.cancelbt.setAutoDefault(False)

    def get_min_max(self):
        return (self._min, self._max)

    def ok_clicked(self):
        self._min = self.spinmin.value()
        self._max = self.spinmax.value()
        self.accept()
    
    def cancel_clicked(self):
        self.reject()


def show_find_refcount_dlg(parent):
    dlg = FindRefcountDlg(parent)
    if parent:
        dlg.move(parent.rect().center() - dlg.rect().center())
    ret = dlg.exec_()
    if ret:
        return dlg.get_min_max()
    else:
        return None, None


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    QApplication.setStyle(QStyleFactory.create('Fusion'))
    gui = QMainWindow()
    gui.setFocus()
    gui.show()
    print(show_find_refcount_dlg(gui))
    sys.exit(app.exec_())

