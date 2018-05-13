import re
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import *
from PyQt5.Qsci import *
from PyQt5.QtGui import *


class FindInputLine(QTextEdit):
    enter_pressed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet('background-color:#ffffff')

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Return or key == Qt.Key_Enter:
            self.enter_pressed.emit()
        else:
            super().keyPressEvent(event)


class FindDlg(QDialog):
    def __init__(self, parent=None, qtabs=None):
        QDialog.__init__(self, parent, Qt.WindowStaysOnTopHint)
        self.parent = parent
        self.initUI()
        self.qtabs = qtabs

    def initUI(self):
        self.re = False
        self.cs = None
        self.wo = None

        findButton = QPushButton("Find",self)
        findButton.clicked.connect(self.find)

        replaceButton = QPushButton("Replace",self)
        replaceButton.clicked.connect(self.replace)


        allButton = QPushButton("Replace all",self)
        allButton.clicked.connect(self.replaceAll)


        self.findField = FindInputLine(self)
        self.findField.setMaximumHeight(40)

        self.caseSens = QCheckBox("Case sensitive",self)
        if self.caseSens.isChecked():
            self.cs = True
        else:
            self.cs = False


        self.wholeWords = QCheckBox("Whole words",self)
        if self.wholeWords.isChecked():
            self.wo = True
        else:
            self.wo = False


        self.normalRadio = QRadioButton("Normal",self)
        self.normalRadio.toggled.connect(self.normalMode)
        self.normalRadio.setChecked(True)

        # Regular Expression Mode - radio button
        self.regexRadio = QRadioButton("RegEx",self)
        self.regexRadio.toggled.connect(self.regexMode)

        self.replaceField = FindInputLine(self)
        self.replaceField.setMaximumHeight(40)

        optionsLabel = QLabel("Options: ",self)

        layout = QGridLayout()

        layout.addWidget(self.findField,1,0,1,4)
        layout.addWidget(self.normalRadio,2,2)
        layout.addWidget(self.regexRadio,2,3)
        layout.addWidget(findButton,2,0,1,2)
        layout.addWidget(self.replaceField,3,0,1,4)
        layout.addWidget(replaceButton,4,0,1,2)
        layout.addWidget(allButton,4,2,1,2)

        spacer = QWidget(self)
        spacer.setFixedSize(0,10)
        layout.addWidget(spacer,5,0)

        layout.addWidget(optionsLabel,6,0)
        layout.addWidget(self.caseSens,6,1)
        layout.addWidget(self.wholeWords,6,2)

        self.setGeometry(300,300,360,250)
        self.setWindowTitle("Find / Replace")
        self.setLayout(layout)
        self.findField.setFocus(True)

        self.findField.enter_pressed.connect(self.find)
        self.replaceField.enter_pressed.connect(self.replace)

    def getCurrentEditor(self):
        return self.qtabs.currentWidget()

    def regexMode(self):
        # Uncheck and then disable case sensitive/whole words in regex mode
        self.caseSens.setChecked(False)
        self.wholeWords.setChecked(False)

        self.caseSens.setEnabled(False)
        self.wholeWords.setEnabled(False)

        self.re = True

    def normalMode(self):
        # Enable case sensitive/whole words
        self.caseSens.setEnabled(True)
        self.wholeWords.setEnabled(True)

        self.re = False

    def find(self):
        # Get the text to find
        self.expr = self.findField.toPlainText()
        # Use QScintilla's built in find method for this
        editor = self.getCurrentEditor()
        if editor:
            editor.findFirst(self.expr, self.re, self.cs, self.wo, True)

    def replace(self):
        self.replaceStr = self.replaceField.toPlainText()
        editor = self.getCurrentEditor()
        if editor:
            self.find()
            editor.replace(self.replaceStr)

    def replaceAll(self):
        self.replaceStr = self.replaceField.toPlainText()
        editor = self.getCurrentEditor()
        if editor:
            self.find()
            while editor.findNext():
                editor.findNext()
                editor.replace(self.replaceStr)
