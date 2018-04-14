# -*- coding: utf-8 -*-
import os
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.Qsci import *
import re
import json

class MyLexer(QsciLexerCustom):
    def __init__(self, parent, theme_file):
        super(MyLexer, self).__init__(parent)
        self.style_infos = {}
        self.style2id = {}
        self.id2stylename = {}
        self.font_info = {}
        self.caret = None
        self.hightlight = None
        self.selection = None
        self.load_theme(theme_file)
        for styleid, style in enumerate(self.style_infos):
            self.style2id[style] = styleid
            self.id2stylename[styleid] = style

        # Default text settings
        # ----------------------
        self.setDefaultColor(QColor(self.style_infos['default']['color']))
        self.setDefaultPaper(QColor(self.style_infos['default']['background']))
        weight = QFont.Normal
        italic = False
        if self.font_info['style'] == 'bold':
            weight = QFont.Bold
        elif self.font_info['style'] == 'italic':
            italic = True
        elif self.font_info['style'] == 'bolditalic':
            italic = True
            weight = QFont.Bold
        self.default_font =  QFont(self.font_info['face'], self.font_info['size'], weight=weight, italic=italic)
        self.setDefaultFont(self.default_font)

        default_weight = weight
        default_italic = italic
        default_font = self.font_info['face']
        default_size = self.font_info['size']

        for styleid, style in enumerate(self.style_infos):
            print(f'Initializing style {styleid:02d} : {style:22} : {self.style_infos[style]}')
            self.style2id[style] = styleid
            self.id2stylename[styleid] = style
            weight = default_weight
            italic = default_italic
            current_style = self.style_infos[style]
            if ['style'] == 'bold':
                weight = QFont.Bold
            elif current_style['style'] == 'italic':
                italic = True
            elif current_style['style'] == 'bolditalic':
                italic = True
                weight = QFont.Bold
            elif current_style['style'] == 'normal':
                italic = False
                weight = QFont.Normal
            self.setColor(QColor(current_style['color']), styleid)
            self.setPaper(QColor(current_style['background']), styleid)
            self.setFont(QFont(default_font, default_size, weight=weight, italic=italic), styleid)
            if styleid > 64:
                break

    ''''''

    def get_style(self, d, key):
        ret = d.get(key, {})
        ret['color'] = ret.get('color', self.style_infos['default']['color'])
        ret['background'] = ret.get('background', self.style_infos['default']['background'])
        ret['style'] = ret.get('style', self.style_infos['default']['style'])
        return ret

    def get_symbol_text(self, d, key):
        themed = d.get(key, {})
        for item in 'symbol', 'text':
            dd = self.get_style(themed, item)
            themed[item] = dd
        return themed

    def get_theme_style(self, style):
        self.style_infos[style] = self.get_style(self.theme_d, style)

    def get_theme_symbol_text(self, style):
        ret = self.get_symbol_text(self.theme_d, style)
        self.style_infos[style + '.' + 'symbol'] = ret['symbol']
        self.style_infos[style + '.' + 'text'] = ret['text']

    def load_theme(self, theme_file):
        if not os.path.exists(theme_file):
            return False
        with open(theme_file, 'rt') as f:
            theme_d = json.load(f)

        # now fill in the blanks
        self.theme_d = theme_d
        background = theme_d.get('background', "#fffdf6e3")
        foreground = theme_d.get('foreground', "#ff657b83")

        self.highlight = theme_d.get('linehighlight', "#3F3D3812")
        self.selection = theme_d.get('selection', {})
        self.selection['background'] = self.selection.get('background', '#ffd33682')
        self.selection['foreground'] = self.selection.get('foreground', '#fffdf6e3')
        self.caret = theme_d.get('caret', "#ff6ec3dc")

        font = theme_d.get('font', {})
        font['face'] = font.get('face', 'Ubuntu Mono')
        font['size'] = font.get('size', 16)
        font['style'] = font.get('style', 'normal')
        self.font_info = font
        self.style_infos['default'] = {
            'color': foreground,
            'background': background,
            'style': font['style']
        }

        for style in 'text.italic', 'text.bold', 'text.bolditalic', 'quote':
            self.get_theme_symbol_text(style)
        self.get_theme_style('h.symbol')
        for i in range(6):
            hname = f'h{i+1}.text'
            self.get_theme_style(hname)
        for style in ('code.fenced', 'code', 'list.symbol', 'list.unordered',
                      'list.ordered', 'tag', 'citekey', 'zettel.link', 'comment',
                      'footnote'):
            self.get_theme_style(style)

        link_dict = theme_d.get('link', {})
        self.style_infos['link.caption'] = self.get_style(link_dict, 'title')
        self.style_infos['link.url'] = self.get_style(link_dict, 'url')
        self.style_infos['link.attr'] = self.get_style(link_dict, 'attr')

        ### if code fenced is style 32, its background color will be displayed
        ### at the end of the text line.
        ### Aaaah: https://www.scintilla.org/MyScintillaDoc.html#Styling
        ###   The standard Scintilla settings divide the 8 style bits available for
        ###   each character into 5 bits (0 to 4 = styles 0 to 31) that set a style
        ###   and three bits (5 to 7) that define indicators. You can change the
        ###   balance between styles and indicators with SCI_SETSTYLEBITS
        ### --> we better not use more than 31 styles


    def language(self):
        return "MardownZettelkasten"
    ''''''

    def description(self, style):
        if style in self.id2stylename:
            return self.id2stylename[style]
        else:
            return ''
    ''''''

    def styleText3(self, start, end):
        self.startStyling(start)
        text = self.parent().text()[start:end]
        self.setStyling(end-start, self.style2id['default'])

    def styleText(self, start, end):
        self.startStyling(0)
        text = bytearray(self.parent().text(), "utf-8").decode("utf-8")
        p = re.compile(r'([\[]?\[)([0-9.]{12,18})([^]]*)(\][\]]?)')
        regions = []
        for match in p.finditer(text):
            regions.append((match.start(), match.end(), match.group()))
            print(match.group())

        style_regions = []
        # now translate regions to byte arrays
        current_pos = 0
        for region in regions:
            gap = region[0] - current_pos
            gap_b = len(bytearray(text[current_pos:region[0]], 'utf-8'))
            if gap_b > 0:
                style_regions.append((gap_b, 'default'))
            match_b = len(bytearray(region[2], 'utf-8'))
            match = region[1] - region[0]
            style_regions.append((match_b, 'zettel.link'))
            current_pos += gap + match
        gap = len(text) - current_pos
        if gap > 0:
            gap_b = len(bytearray(text[current_pos:], 'utf-8'))
            style_regions.append((gap_b, 'default'))
        print(start, end)

        for num_chars, style in style_regions:
            self.setStyling(num_chars, self.style2id[style])

    def styleText2(self, start, end):
        # 1. Initialize the styling procedure
        # ------------------------------------
        self.startStyling(start)

        # 2. Slice out a part from the text
        # ----------------------------------
        text = self.parent().text()[start:end]

        # 3. Tokenize the text
        # ---------------------
        p = re.compile(r"-->|<!--|\s+|\w+|\W")

        # 'token_list' is a list of tuples: (token_name, token_len)
        token_list = [ (token, len(bytearray(token, "utf-8"))) for token in p.findall(text)]

        # 4. Style the text
        # ------------------
        # 4.1 Check if multiline comment
        multiline_comm_flag = False
        editor = self.parent()
        if start > 0:
            previous_style_nr = editor.SendScintilla(editor.SCI_GETSTYLEAT, start - 1)
            if previous_style_nr == 3:
                multiline_comm_flag = True
            ###
        ###
        # 4.2 Style the text in a loop
        for i, token in enumerate(token_list):
            if multiline_comm_flag:
                self.setStyling(token[1], 3)
                if token[0] == "-->":
                    multiline_comm_flag = False
                ###
            ###
            else:
                if token[0] in ["for", "while", "return", "int", "include"]:
                    # Red style
                    self.setStyling(token[1], 1)

                elif token[0] in ["(", ")", "{", "}", "[", "]", "#"]:
                    # Blue style
                    self.setStyling(token[1], 2)

                elif token[0] == "<!--":
                    multiline_comm_flag = True
                    self.setStyling(token[1], 3)

                else:
                    # Default style
                    self.setStyling(token[1], self.style2id['default'])
                ###
            ###
        ###

    ''''''

''' end Class '''


class CustomMainWindow(QMainWindow):
    def __init__(self):
        super(CustomMainWindow, self).__init__()

        # -------------------------------- #
        #           Window setup           #
        # -------------------------------- #

        # 1. Define the geometry of the main window
        # ------------------------------------------
        self.setGeometry(300, 300, 800, 400)
        self.setWindowTitle("QScintilla Test")

        # 2. Create frame and layout
        # ---------------------------
        self._frm = QFrame(self)
        self._frm.setStyleSheet("QWidget { background-color: #ffeaeaea }")
        self._lyt = QVBoxLayout()
        self._frm.setLayout(self._lyt)
        self.setCentralWidget(self._frm)
        self._myFont = QFont()
        self._myFont.setPointSize(14)

        # 3. Place a button
        # ------------------
        self._btn = QPushButton("Qsci")
        self._btn.setFixedWidth(50)
        self._btn.setFixedHeight(50)
        self._btn.clicked.connect(self._btn_action)
        self._btn.setFont(self._myFont)
        self._lyt.addWidget(self._btn)

        # -------------------------------- #
        #     QScintilla editor setup      #
        # -------------------------------- #

        # ! Make instance of QSciScintilla class!
        # ----------------------------------------
        self._editor = QsciScintilla()
        self._editor.setUtf8(True)             # Set encoding to UTF-8
        with open('zettelkasten/201803100758 P.md', mode='r', encoding='utf-8', errors='ignore') as f:
            txt = f.read()
        self._editor.setText(txt)     # 'myCodeSample' is a string containing some C-code
        self._editor.setLexer(None)            # We install lexer later
        #self._editor.setFont(self._myFont)    # Gets overridden by lexer later on

        # 1. Text wrapping
        # -----------------
        self._editor.setWrapMode(QsciScintilla.WrapWord)
        self._editor.setWrapVisualFlags(QsciScintilla.WrapFlagByText)
        self._editor.setWrapIndentMode(QsciScintilla.WrapIndentIndented)

        # 2. End-of-line mode
        # --------------------
        self._editor.setEolMode(QsciScintilla.EolWindows)
        self._editor.setEolVisibility(False)

        # 3. Indentation
        # ---------------
        self._editor.setIndentationsUseTabs(False)
        self._editor.setTabWidth(4)
        self._editor.setIndentationGuides(True)
        self._editor.setTabIndents(True)
        self._editor.setAutoIndent(True)


        # 5. Margins
        # -----------
        # Margin 0 = Line nr margin
        #self._editor.setMarginType(0, QsciScintilla.NumberMargin)
        self._editor.setMarginType(0, QsciScintilla.SymbolMargin)
        self._editor.setMarginWidth(0, "0000")
        self._editor.setMarginWidth(1, "0000")
        self._editor.setMarginsForegroundColor(QColor("#ff888888"))

        # -------------------------------- #
        #          Install lexer           #
        # -------------------------------- #
        if True:
            self._lexer = MyLexer(self._editor, 'theme.json')
            self._editor.setLexer(self._lexer)

        # 4. Caret
        # ---------
        self._editor.setCaretForegroundColor(QColor(self._lexer.caret))
        self._editor.setCaretLineVisible(True)
        self._editor.setCaretLineBackgroundColor(QColor(self._lexer.highlight))
        self._editor.setCaretWidth(8)
        #self._editor.setMarginsBackgroundColor(QColor("#ff404040"))
        self._editor.setFont(self._lexer.default_font)

        # ! Add editor to layout !
        # -------------------------
        self._lyt.addWidget(self._editor)
        self.show()

    ''''''

    def _btn_action(self):
        print("Hello World!")
    ''''''

''' End Class '''

if __name__ == '__main__':
    app = QApplication(sys.argv)
    QApplication.setStyle(QStyleFactory.create('Fusion'))
    myGUI = CustomMainWindow()

    sys.exit(app.exec_())

''''''
