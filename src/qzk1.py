import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.Qsci import *
from imagescintilla import ImageScintilla
from PyQt5.Qsci import QsciLexerMarkdown



myCodeSample = r"""

# 201710311421 The rise of the machines
tags = ##AI #world-domination

Machines are becoming more and more intelligent and powerful.
This might reach a point where they might develop a consciensce of their own.
As a consequence, they might turn evil and try to kill us all ............... [[201711181437]]

<!-- References: -->
[201710270000] Capsule Networks show potential to surpass Convolutional Neural Networks.
[201710290256] Single-Pixel attacks on image classifiers.


## This plugin highlights #tags even in headings
Not just in normal text like in #this line.

## It highlights links to other notes [201711010120] even in headings
<--- The bookmark symbol in the gutter  might help to spot references like the one in this paragraph more easily. [[201710230000]]. This feature[^footnoote] can be turned off via the settings file.

**Note:** We support both double [[201710291021]]
                      and single  [201711010117]  bracket style note-links!
                      As well as old school §201711010120 links

[^footnoote]: Another feature: syntax coloring for MarkDown footnote references!
""".replace("\n", "\r\n")


class CustomMainWindow(QMainWindow):
    def __init__(self):
        super(CustomMainWindow, self).__init__()

        # Window setup
        # --------------

        # 1. Define the geometry of the main window
        self.setGeometry(300, 300, 800, 400)
        self.setWindowTitle("QScintilla Test")

        # 2. Create frame and layout
        self.__frm = QFrame(self)
        self.__frm.setStyleSheet("QWidget { background-color: #ffeaeaea }")
        self.__lyt = QVBoxLayout()
        self.__frm.setLayout(self.__lyt)
        self.setCentralWidget(self.__frm)
        self.__myFont = QFont("Consolas", 14, weight=QFont.Bold)
        self.__myFont.setPointSize(14)

        # 3. Place a button
        self.__btn = QPushButton("Qsci")
        self.__btn.setFixedWidth(50)
        self.__btn.setFixedHeight(50)
        self.__btn.clicked.connect(self.__btn_action)
        self.__btn.setFont(self.__myFont)
        self.__lyt.addWidget(self.__btn)

        # QScintilla editor setup
        # ------------------------



        # 1. Make instance of ImageScintilla class
        # (instead of QsciScintilla)
        self.__editor = ImageScintilla()
        self.__lexer = QsciLexerMarkdown(self.__editor)
        self.__editor.setText(myCodeSample)
        self.__editor.setLexer(self.__lexer)
        self.__editor.setUtf8(True)  # Set encoding to UTF-8
        self.__editor.setFont(self.__myFont)  # Can be overridden by lexer
        self.__editor.setWrapMode(ImageScintilla.WrapWord)
        self.__editor.setWrapIndentMode(ImageScintilla.WrapIndentSame)


        # 2. Image tests
        self.__editor.set_calculation_font(self.__myFont)

        img = [None, None, None, None]
        img[0] = self.__editor.add_image("qscintilla_logo.png", (19, 4),  (30, 30))
        img[1] = self.__editor.add_image("qscintilla_logo.png", (35, 21), (90, 75))
        img[2] = self.__editor.add_image("exco_logo.png",       (53, 25), (85, 85))
        img[3] = self.__editor.add_image("qscintilla_logo.png", (55, 30), (60, 60))
        self.__editor.delete_image(img[3])

        # 3. Add editor to layout
        self.__lyt.addWidget(self.__editor)

        self.show()

    ''''''

    def __btn_action(self):
        print("Hello World!")

    ''''''


''' End Class '''

if __name__ == '__main__':
    app = QApplication(sys.argv)
    QApplication.setStyle(QStyleFactory.create('Fusion'))
    myGUI = CustomMainWindow()

    sys.exit(app.exec_())

''''''
