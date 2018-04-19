from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

class PopUpDLG(QDialog):
    def __init__(self, title, label, defaulttext):
        super(PopUpDLG, self).__init__()
        self.setObjectName("self")
        self.setWindowTitle(title)
        hlay = QHBoxLayout(self)
        hlay.addWidget(QLabel(label))
        self.line_edit = QLineEdit()
        self.line_edit.setText(defaulttext)
        hlay.addWidget(self.line_edit)
        self.setLayout(hlay)

#        self.resize(200, 71)
#        self.setMinimumSize(QSize(200, 71))
#        self.setMaximumSize(QSize(200, 71))
#        self.setContextMenuPolicy(Qt.NoContextMenu)
#        icon = QtGui.QIcon()
#        icon.addPixmap(QtGui.QPixmap("Icons/Plus-32.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
#        self.setWindowIcon(icon)

