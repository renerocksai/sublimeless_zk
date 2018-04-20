from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from fuzzywuzzy import process


class FuzzySearchPanel(QWidget):
    item_selected = pyqtSignal(str, str)    # key, value
    close_requested = pyqtSignal()

    def __init__(self, parent=None, item_dict=None, max_items=20):
        super().__init__(parent)
        self.max_items = max_items

        self.item_dict = item_dict    #    { show_as: associated_value }
        if self.item_dict is None:
            self.item_dict = {}

        self.fuzzy_items = list(self.item_dict.keys())[:max_items]
        self.initUI()

    def initUI(self):
        vlay = QVBoxLayout()
        self.input_line = QLineEdit()
        self.list_box = QListWidget()
        for i in range(self.max_items):
            self.list_box.insertItem(i, '')
        vlay.addWidget(self.input_line)
        vlay.addWidget(self.list_box)
        self.update_listbox()
        self.setLayout(vlay)
        self.setMinimumWidth(600)
        self.list_box.setAlternatingRowColors(False)

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
                                """
                           )

        # connections
        self.input_line.textChanged.connect(self.text_changed)

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
            fuzzy_results = process.extract(search_string, self.item_dict.keys(), limit=self.max_items)
            fuzzy_results = [f for f in fuzzy_results if f[1] > 40]
            self.fuzzy_items = [f[0] for f in fuzzy_results]
        else:
            self.fuzzy_items = list(self.item_dict.keys())[:self.max_items]
        self.update_listbox()

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Enter or key == Qt.Key_Return:
            # todo fire signal
            row = self.list_box.currentRow()
            key = self.fuzzy_items[row]
            value = self.item_dict[key]
            self.item_selected.emit(key, value)
        elif key == Qt.Key_Down:
            row = self.list_box.currentRow()
            if row < len(self.fuzzy_items):
                self.list_box.setCurrentRow(row + 1)
        elif key == Qt.Key_Up:
            row = self.list_box.currentRow()
            if row > 0:
                self.list_box.setCurrentRow(row - 1)
        elif key == Qt.Key_Escape:
            # emit abort signal
            self.close_requested.emit()


def show_fuzzy_panel(title, fuzzy_list):

    pass


if __name__ == '__main__':
    fuzzy_list = ['0 - techbeacon artikel.md', "1 - Why your execs don't get agile and what you can do about it.md", '2 - WHY THE COMMAND-AND-CONTROL MINDSET IS KILLING your company.md', '201710230000 Passwortstaerke, neu.md', '201710240000 PictureScan Vortrag, Umgestaltung.md', '201710240001 Projektfunding, Silicon Valley.md', '201710250000 Rene Schallner, Kurz-CV.md', '201710270000 PictureScan Validierung, Klarstellung.md', '201710290256 Projektmanagement führt zu Mittelmaß.md', '201710291010 Projekt, Definition.md', '201710291021 Erwartungen ans Projektmanagement für Forschungsprojekte.md', '201710291024 Wozu Projektmanagement in der Forschung.md', '201710291125 Größtes Risiko beim Projekt-Risiko-Management wird oft übersehen.md', '201710291143 Agiles Projektmanagement ist nur bedingt eine Verbesserung und führt ebenso zu Mittelmaß.md', '201710291203 Mangelndes Domänenwissen bei der Projektplanung ergibt unrealistische Pläne.md', '201710291205 Forschungsprojekte können keine Projekte sein.md', '201710292024 Das Problem der Unplanbarkeit.md', '201710301904 Feedback Gespraech mit Andreas ueber Picture-Scan-Validierung.md', '201710311153 Der überwiegende Großteil aller Software-Projekte scheitern.md', '201710311421 The rise of the machines.md', '201711010117 Forschen bedeutet lernen.md', '201711010120 Forschen ist ein nichtlinearer Prozess.md', '201711010123 Lernen laesst sich nicht projektmanagen.md', '201711010146 Falsche Annahmen des klassischen Projektmanagements.md', '201711010148 Belege fuer Versagen des klassischen Projektmanagements.md', '201711010150 Engagement ist wichtig fuer Motivation und Firmenerfolg.md', '201711010311 Negative Langzeitfolgen durch Plankonformität.md', '201711010411 Adaptive Forschungs-Roadmaps statt Projektmanagement als Lösung.md', '201711010413 Predictable Efficiency.md', '201711010415 Predictability killt Lernen und Innovation.md', '201711010419 Periodische Reports zum Stand der Forschung.md', '201711010441 Projektmanagement bestraft Prozess-Verbesserung.md', '201711010451 Sind Dead-Lines wichtig.md', '201711010534 Alte Best Practices sind überholt.md', '201711010542 Product Thinking.md', '201711012155 SublimeText coole Settings fuer Line Spacing etc.md', '201711061636 Caros Babykarte.md', '201711160847 Berlin an Caro.md', '201711181437 AI is going to kill us all.md', '201711211903 Marburg an Caro.md', '201711221310 Weiterentwicklung Markeninteraktionen.md', '201712070552 Caro Auto-Reply.md', '201712071307 Kaffee und Team Meeting.md', '201712291100 Proposal Bewertung von generierten Marken-Interaktions-beschreibenden Sätzen.md', '201801121045 citation sentiment paper.md', '201802011252 caro report lienhart treffen.md', '201803100758 P.md', '201804081103 Differences to the Archive.md', '201804120224 Why I developed Sublime_ZK.md', 'P - like P-Management.md']

    if False:
        search = 'test'
        ret = ['* {} : {}'.format(x[1], x[0]) for x in process.extract(search, fuzzy_list, limit=5)]
        print('\n'.join(ret))
    else:
        import sys

        item_dict = {f: f.split()[0] for f in fuzzy_list}
        print(item_dict)

        app = QApplication(sys.argv)
        QApplication.setStyle(QStyleFactory.create('Fusion'))
        gui = QMainWindow()
        fuz = FuzzySearchPanel(gui, item_dict)
        gui.setCentralWidget(fuz)
        gui.setFocus()
        gui.show()
        ret = show_fuzzy_panel('Title', fuzzy_list)
        print(ret)
        sys.exit(app.exec_())

