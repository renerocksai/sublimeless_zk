import sys
import os
from PyQt5.Qt import QUrl, Qt, pyqtSignal
from PyQt5.QtWidgets import QWidget, QLabel, QLineEdit, QPushButton, QHBoxLayout, QVBoxLayout, QSplitter, QFrame, QProgressBar, QApplication, QComboBox, QFileDialog, QMessageBox, QDialog
from PyQt5.QtWebEngineWidgets import QWebEngineView as QWebView
from libzk2setevi.convert import Zk2Setevi
import traceback
from subprocess import Popen, PIPE

from autobib import Autobib


# fix path on macos
if sys.platform == 'darwin':
    p = Popen('bash -l -c \'echo $PATH\'', stdout=PIPE, shell=True)
    stdout, stderr = p.communicate()
    stdout = stdout.decode('utf-8', errors='ignore')
    os.environ['PATH'] = stdout


class Semantic_ZK(QWidget):
    close_clicked = pyqtSignal()

    def __init__(self, project):
        super().__init__()
        self.linkstyle_list = ['single', 'double']
        self.parser_list = ['basic', 'mmd', 'pandoc']
        self.project = project
        main_split = QSplitter(Qt.Horizontal)

        # Left Side
        left_widget = QWidget()
        left_vlay = QVBoxLayout()
        left_widget.setLayout(left_vlay)

        # ZK Folder
        zk_lbl_folder = QLabel('ZK Folder')
        zk_hlay = QHBoxLayout()
        zk_ed_folder = QLineEdit('(please select)')
        zk_ed_folder.setStyleSheet('color:#14148c')
        zk_bt_folder = QPushButton('...')
        zk_bt_folder.setFixedWidth(100)
        zk_hlay.addWidget(zk_ed_folder)
        zk_hlay.addWidget(zk_bt_folder)
        #
        # hide it
        #
        # left_vlay.addWidget(zk_lbl_folder)
        # left_vlay.addLayout(zk_hlay)

        # Output Folder
        out_lbl_folder = QLabel('Output Folder')
        out_hlay = QHBoxLayout()
        out_ed_folder = QLineEdit('(please select)')
        out_ed_folder.setStyleSheet('color:#14148c')
        out_bt_folder = QPushButton('...')
        out_bt_folder.setFixedWidth(100)
        out_hlay.addWidget(out_ed_folder)
        out_hlay.addWidget(out_bt_folder)
        left_vlay.addWidget(out_lbl_folder)
        left_vlay.addLayout(out_hlay)

        # Bib File
        bib_lbl = QLabel('Bib File')
        bib_hlay = QHBoxLayout()
        bib_ed = QLineEdit('(auto)')
        bib_ed.setStyleSheet('color:#14148c')
        bib_bt = QPushButton('...')
        bib_bt.setFixedWidth(100)
        bib_hlay.addWidget(bib_ed)
        bib_hlay.addWidget(bib_bt)
        #
        # hide it
        #
        #left_vlay.addWidget(bib_lbl)
        #left_vlay.addLayout(bib_hlay)

        # Extension
        ext_hlay = QHBoxLayout()
        ext_lbl = QLabel('Markdown Extension')
        ext_ed = QLineEdit('.md')
        ext_ed.setFixedWidth(100)
        ext_hlay.addWidget(ext_lbl)
        ext_hlay.addWidget(ext_ed)
        # hidden left_vlay.addLayout(ext_hlay)

        # Link Style
        lstyle_hlay = QHBoxLayout()
        lstyle_lbl = QLabel('Link Style')
        lstyle_choice = QComboBox()
        lstyle_choice.addItems(self.linkstyle_list)
        lstyle_choice.setFixedWidth(100)
        lstyle_choice.setCurrentIndex(1)
        lstyle_hlay.addWidget(lstyle_lbl)
        lstyle_hlay.addStretch(1)
        lstyle_hlay.addWidget(lstyle_choice)
        # hidden left_vlay.addLayout(lstyle_hlay)

        # Parser
        parser_hlay = QHBoxLayout()
        parser_lbl = QLabel('Parser')
        parser_choice = QComboBox()
        parser_choice.addItems(self.parser_list)
        parser_choice.setFixedWidth(100)
        parser_choice.setCurrentIndex(1)
        parser_hlay.addWidget(parser_lbl)
        parser_hlay.addStretch(1)
        parser_hlay.addWidget(parser_choice)
        left_vlay.addLayout(parser_hlay)

        # Separator
        sep = self.hline()
        left_vlay.addStretch(1)
        left_vlay.addWidget(sep)

        # remote URL
        baseurl_lbl = QLabel('Optional remote URL:')
        baseurl_ed = QLineEdit()
        baseurl_ed.setStyleSheet('color:#14148c')
        left_vlay.addWidget(baseurl_lbl)
        left_vlay.addWidget(baseurl_ed)

        # Separator
        sep = self.hline()
        left_vlay.addStretch(1)
        left_vlay.addWidget(sep)

        # FILTERS:
        lbl_filter = QLabel('<u>Note filters:</u>')
        left_vlay.addWidget(lbl_filter)
        from_hlay = QHBoxLayout()
        from_lbl = QLabel('from timestamp:')
        from_ed = QLineEdit('19000101')
        from_ed.setStyleSheet('color:#14148c')

        from_hlay.addWidget(from_lbl)
        from_hlay.addStretch(1)
        from_hlay.addWidget(from_ed)
        left_vlay.addLayout(from_hlay)

        to_hlay = QHBoxLayout()
        to_lbl = QLabel('to timestamp:')
        to_ed = QLineEdit('22001231')
        to_ed.setStyleSheet('color:#14148c')
        to_hlay.addWidget(to_lbl)
        to_hlay.addStretch(1)
        to_hlay.addWidget(to_ed)
        left_vlay.addLayout(to_hlay)

        tagwhite_hlay = QHBoxLayout()
        tagwhite_lbl = QLabel('<pre>Only Tags :</pre>')
        tagwhite_ed = QLineEdit('')
        tagwhite_ed.setStyleSheet('color: #328930')
        tagwhite_hlay.addWidget(tagwhite_lbl)
        tagwhite_hlay.addWidget(tagwhite_ed)
        left_vlay.addLayout(tagwhite_hlay)

        tagblack_hlay = QHBoxLayout()
        tagblack_lbl = QLabel('<pre>Never Tags:</pre>')
        tagblack_ed = QLineEdit('')
        tagblack_ed.setStyleSheet('color: #b40000')
        tagblack_hlay.addWidget(tagblack_lbl)
        tagblack_hlay.addWidget(tagblack_ed)
        left_vlay.addLayout(tagblack_hlay)

        # Separator
        sep = self.hline()
        left_vlay.addWidget(sep)


        # Progress
        progress_hlay = QHBoxLayout()
        progress_lbl = QLabel('Progress')
        progress_prg = QProgressBar()
        progress_hlay.addWidget(progress_lbl)
        progress_hlay.addWidget(progress_prg)
        left_vlay.addLayout(progress_hlay)

        # Info
        info_hlay = QHBoxLayout()
        info_lbl = QLabel('Info:')
        info_txt = QLabel()
        info_hlay.addWidget(info_lbl)
        info_hlay.addWidget(info_txt)
        info_hlay.addStretch(1)
        left_vlay.addLayout(info_hlay)

        # Convert Button
        convert_bt = QPushButton('Convert!')
        left_vlay.addWidget(convert_bt)
        close_bt = QPushButton('Close')
        left_vlay.addWidget(close_bt)
        close_bt.clicked.connect(self.on_close_clicked)

        # HTML view
        self.html_view = QWebView()
        self.html_view.setHtml('<center><h2>Preview</h2></center>')

        # Add to splitter
        main_split.addWidget(left_widget)
        main_split.addWidget(self.html_view)

        # Add to self
        lay_all = QHBoxLayout()
        lay_all.addWidget(main_split)
        self.setLayout(lay_all)

        # What to keep?
        self.info_txt = info_txt
        self.progressbar = progress_prg
        self.ed_zk_folder = zk_ed_folder
        self.ed_output_folder = out_ed_folder
        self.ed_bibfile = bib_ed
        self.ed_extension = ext_ed
        self.sel_linkstyle = lstyle_choice
        self.sel_parser = parser_choice
        self.ed_baseurl = baseurl_ed
        self.ed_from = from_ed
        self.ed_to = to_ed
        self.ed_tagblack = tagblack_ed
        self.ed_tagwhite = tagwhite_ed

        # Connections
        convert_bt.clicked.connect(self.on_convert_clicked)
        zk_bt_folder.clicked.connect(self.on_zk_folder_clicked)
        out_bt_folder.clicked.connect(self.on_output_folder_clicked)
        bib_bt.clicked.connect(self.on_bibfile_clicked)

    @staticmethod
    def check_tags(text):
        errors = []
        for tag in text.split():
            if not tag.startswith('#'):
                errors.append('<b>{}</b> does not seem to be a tag!'.format(tag))
            if tag.endswith(','):
                errors.append('<b>{}</b> ends with a comma!'.format(tag))
        return errors

    def on_convert_clicked(self):
        bibfile = None
        error_lines = []
        if os.path.exists(self.ed_bibfile.text()):
            bibfile = self.ed_bibfile.text()
        if not os.path.exists(self.ed_zk_folder.text()):
            error_lines.append('The Zettelkasten folder is invalid')
        if not os.path.exists(self.ed_output_folder.text()):
            error_lines.append('The output folder is invalid')
        extension = self.ed_extension.text()
        if extension:
            if not extension.startswith('.'):
                error_lines.append('The markdown extension does not start with a dot')
            bad_chars = []
            invalid_chars = '*?/\\:'
            for char in extension:
                if char in invalid_chars:
                    bad_chars.append(char)
            for char in bad_chars:
                error_lines.append('The markdown extension contains a ' + char)
        else:
            error_lines.append('The markdown extension is empty')

        # now check the filters:
        ts_from = self.ed_from.text()
        if Zk2Setevi.parse_timestamp(ts_from) is None:
            error_lines.append('The FROM timestamp seems incorrect: <b>' + ts_from + '</b>')

        ts_to = self.ed_to.text()
        if Zk2Setevi.parse_timestamp(ts_to) is None:
            error_lines.append('The TO timestamp seems incorrect: <b>' + ts_to + '</b>')

        tags_white = self.ed_tagwhite.text()
        errors = self.check_tags(tags_white)
        for error in errors:
            error_lines.append('In ONLY tags: ' + error)

        tags_black = self.ed_tagblack.text()
        errors = self.check_tags(tags_black)
        for error in errors:
            error_lines.append('In TO tags: ' + error)

        if error_lines:
            mb = QMessageBox()
            mb.setIcon(QMessageBox.Critical)
            mb.setWindowTitle('Invalid settings')
            mb.setText('Some of the settings are invalid:')
            error_lines[0] = ' * ' + error_lines[0]
            mb.setInformativeText('<p>' + '<br> * '.join(error_lines)+ '</p>')
            mb.setTextFormat(Qt.RichText)
            mb.setStandardButtons(QMessageBox.Ok)
            mb.exec_()
            return

        # everything ok
        zk_folder = self.ed_zk_folder.text()
        output_folder = self.ed_output_folder.text()
        linkstyle = self.linkstyle_list[self.sel_linkstyle.currentIndex()]
        parser = self.parser_list[self.sel_parser.currentIndex()]
        baseurl = self.ed_baseurl.text()

        # try to find out our home
        if getattr(sys, 'frozen', False):
            # we are running in a bundle
            if sys.platform == 'darwin':
                # cx_freeze
                bundle_dir = os.path.dirname(sys.executable)
            else:
                # pyinstaller
                bundle_dir = sys._MEIPASS
        else:
            # we are running in a normal Python environment
            bundle_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
        try:
            converter = Zk2Setevi(home=bundle_dir, project=self.project, out_folder=output_folder,
                                  bibfile=bibfile, extension=extension,
                                  linkstyle=linkstyle, parser=parser,
                                  progress_callback=self.progress_callback, finish_callback=self.finish_callback,
                                  base_url=baseurl, timestamp_from=ts_from, timestamp_until=ts_to, white_tags=tags_white,
                                  black_tags=tags_black)
            converter.create_html()
            url = 'file:///' + output_folder + '/index.html'
            qurl = QUrl(url)
            self.html_view.load(qurl)
        except Exception as e:
            mb = QMessageBox()
            mb.setIcon(QMessageBox.Critical)
            mb.setWindowTitle('Error')
            mb.setText('Exception caught:')
            mb.setDetailedText(str(e) + '\n' + traceback.format_exc())
            mb.setStandardButtons(QMessageBox.Ok)
            mb.exec_()

    def on_zk_folder_clicked(self):
        file = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        if file:
            self.ed_zk_folder.setText(file)

    def on_output_folder_clicked(self):
        file = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        if file:
            self.ed_output_folder.setText(file)

    def on_bibfile_clicked(self):
        file, _ = QFileDialog.getOpenFileName(self, 'Open file', '', "Bibliography files (*.bib)")
        if file:
            self.ed_bibfile.setText(file)

    def progress_callback(self, counter, count, msg):
        percent = int(counter / count * 100)
        self.progressbar.setValue(percent)
        self.info_txt.setText(msg)

    def finish_callback(self):
        self.progressbar.setValue(100)
        self.info_txt.setText('Finished!')

    @staticmethod
    def hline():
        h = QFrame()
        h.setFrameShape(QFrame.HLine)
        h.setFrameShadow(QFrame.Sunken)
        return h

    def on_close_clicked(self):
        self.close_clicked.emit()

class SemanticZKDialog(QDialog):
    def __init__(self, parent, title, project):
        super(SemanticZKDialog, self).__init__(parent=parent)
        self.setObjectName('SemanticZKDlg')
        self.setWindowTitle(title)
        hlay = QHBoxLayout()
        self.convert_widget = Semantic_ZK(project)
        self.convert_widget.ed_zk_folder.setText(project.folder)
        bibfile = Autobib.look_for_bibfile(project)
        if bibfile:
            self.convert_widget.ed_bibfile.setText(bibfile)
        settings = project.settings
        extension = settings.get('markdown_extension', '.md')
        self.convert_widget.ed_extension.setText(extension)
        double_brackets = settings.get('double_brackets', True)
        double_index = self.convert_widget.sel_linkstyle.findText('double')
        single_index = self.convert_widget.sel_linkstyle.findText('single')
        if double_brackets:
            sel_index = double_index
        else:
            sel_index = single_index

        if sel_index < 0:
            sel_index = 0
        self.convert_widget.sel_linkstyle.setCurrentIndex(sel_index)

        hlay.addWidget(self.convert_widget)
        self.convert_widget.close_clicked.connect(self.on_close_clicked)
        self.setLayout(hlay)

    def on_close_clicked(self):
        self.done(1)




if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainwindow = Semantic_ZK()
    mainwindow.setWindowTitle('Semantic ZK')
    mainwindow.show()
    mainwindow.setFocus()
    app.exec_()


