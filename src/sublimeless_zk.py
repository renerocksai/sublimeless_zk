# -*- coding: utf-8 -*-
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.Qsci import *
from PyQt5.QtCore import Qt

from themes import Theme
from mainwindow import MainWindow

class Sublimeless_Zk:
    def __init__(self):
        self.gui = None

    def connect_signals(self):
        self.gui.lexer.tag_clicked.connect(self.clicked_tag)
        self.gui.lexer.note_id_clicked.connect(self.clicked_noteid)
        self.gui.search_results_editor.lexer().tag_clicked.connect(self.clicked_tag)
        self.gui.search_results_editor.lexer().note_id_clicked.connect(self.clicked_tag)
        self.gui.saved_searches_editor.lexer().tag_clicked.connect(self.clicked_tag)
        self.gui.saved_searches_editor.lexer().note_id_clicked.connect(self.clicked_tag)
        self.gui.qtabs.tabCloseRequested.connect(self.gui.qtabs.removeTab)
        self.gui.qtabs.tabCloseRequested.connect(self.lessTabs)

    def run(self):
        app = QApplication(sys.argv)
        QApplication.setStyle(QStyleFactory.create('Fusion'))
        theme = Theme('../themes/solarized_light.json')
        self.gui = MainWindow(theme)
        self.connect_signals()
        sys.exit(app.exec_())

    #
    # SLOTS
    #
    def clicked_noteid(self, noteid, ctrl, alt, shift):
        print('noteid', noteid, ctrl, alt, shift)

    def clicked_tag(self, tag, ctrl, alt, shift):
        print('tag', tag)

    def lessTabs(self):
        pass

if __name__ == '__main__':
    Sublimeless_Zk().run()


