import re

from PyQt5.QtGui import QColor, QFont
from PyQt5.Qsci import *
from themes import Theme

class ZkMdLexer(QsciLexerCustom):
    def __init__(self, parent, theme_file):
        super(ZkMdLexer, self).__init__(parent)
        self.theme = Theme(theme_file)
        self.style_infos = {}
        self.style2id = {}
        self.id2stylename = {}

        # Default text settings
        # ----------------------
        self.setDefaultColor(QColor(self.theme.style_infos['default']['color']))
        self.setDefaultPaper(QColor(self.theme.style_infos['default']['background']))
        weight = QFont.Normal
        italic = False
        if self.theme.font_info['style'] == 'bold':
            weight = QFont.Bold
        elif self.theme.font_info['style'] == 'italic':
            italic = True
        elif self.theme.font_info['style'] == 'bolditalic':
            italic = True
            weight = QFont.Bold
        self.default_font =  QFont(self.theme.font_info['face'],
                                   self.theme.font_info['size'],
                                   weight=weight, italic=italic)
        self.setDefaultFont(self.default_font)

        default_weight = weight
        default_italic = italic
        default_font = self.theme.font_info['face']
        default_size = self.theme.font_info['size']

        for styleid, style in enumerate(self.theme.style_infos):
            print(f'Initializing style {styleid:02d} : {style:22} : '
                  f'{self.theme.style_infos[style]}')
            self.style2id[style] = styleid
            self.id2stylename[styleid] = style
            weight = default_weight
            italic = default_italic
            current_style = self.theme.style_infos[style]
            if current_style['style'] == 'bold':
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

    ''''''

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
        regions = []

        p = re.compile(r'(\*\*|__)([^\s].*?[^\s])(\1)')
        for match in p.finditer(text):
            regions.append((match.start(), match.start() + 2, match.group(1), 'text.bold.symbol'))
            regions.append((match.start() + 2, match.end() - 2, match.group(2), 'text.bold.text'))
            regions.append((match.end() - 2, match.end(), match.group(3), 'text.bold.symbol'))

        # zettel links
        p = re.compile(r'([\[]?\[)([0-9.]{12,18})([^]]*)(\][\]]?)')
        for match in p.finditer(text):
            regions.append((match.start(), match.end(), match.group(), 'zettel.link'))

        # todo: sort and flatten? regions
        # maybe flattening is not necessary by cunning layering
        #    --> most important ones last
        regions.sort(key=lambda items: items[0])

        # todo: handle multi line comments

        style_regions = []
        # now translate regions to byte arrays
        # and fill gaps with default style
        current_pos = 0
        for region in regions:
            region_start = region[0]
            region_end = region[1]
            region_text = region[2]
            region_style = region[3]
            gap = region_start - current_pos
            gap_b = len(bytearray(text[current_pos:region_start], 'utf-8'))
            if gap_b > 0:
                style_regions.append((gap_b, 'default'))
            match_b = len(bytearray(region_text, 'utf-8'))
            match = region_end - region_start
            style_regions.append((match_b, region_style))
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