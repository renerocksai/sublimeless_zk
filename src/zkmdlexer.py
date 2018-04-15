import re

from PyQt5.QtGui import QColor, QFont
from PyQt5.Qsci import *
from themes import Theme
from split_regions import split_regions


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
            self.setEolFill(True, styleid)

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
        orig_text = text

        regions = []

        ### non-inline

        # tags in comments (but not in code blocks)
        # code blocks
        p = re.compile(r'(```)(.|\n)*?(```)')
        for match in p.finditer(text):
            a = match.start(1)
            b = match.end(3)
            regions.append((a, b+1, match.group() + '\n', 'code.fenced'))
            # consume
            print(match.groups() , match.group())
            text = text[:a] + 'x' * (len(match.group())) + text[b:]

        # tags
        # todo: implement tags

        # comments
        p = re.compile(r'(<!--)(.|\n)*?(-->)')
        for match in p.finditer(text):
            a = match.start(1)
            b = match.end(3)
            regions.append((a, b, match.group(), 'comment'))
            # consume
            print(match.groups() , match.group())
            text = text[:a] + 'x' * len(match.group()) + text[b:]


        # headings
        p = re.compile('^(#{1,6})(.+)$', flags=re.MULTILINE)
        for match in p.finditer(text):
            a = match.start()
            b = match.end()
            n = match.group(1).count('#')
            regions.append((a, a + len(match.group(1)), match.group(1), 'h.symbol'))
            regions.append((a + len(match.group(1)), b+1, match.group(2)+'\n', f'h{n}.text'))

        # quotes
        p = re.compile('^(>)(.+)$', flags=re.MULTILINE)
        for match in p.finditer(text):
            a = match.start()
            b = match.end()
            regions.append((a, a + len(match.group(1)), match.group(1), 'quote.symbol'))
            regions.append((a + len(match.group(1)), b+1, match.group(2)+'\n', 'quote.text'))

        # block quotes
        ### NEED TO STYLE THE \n !!!
        p = re.compile(r'^( {4})+(.+$)', flags=re.MULTILINE)
        for match in p.finditer(text):
            a = match.start()
            b = match.end()
            regions.append((a, a + len(match.group(1)), match.group(1), 'code.fenced'))
            regions.append((a + len(match.group(1)), b+1, match.group(2) + '\n', 'code.fenced'))
            # +1 to also style the \n

        # list unordered
        p = re.compile(r'^(( {4})*[\*-]\s)(.+)$', flags=re.MULTILINE)
        for match in p.finditer(text):
            a = match.start()
            b = match.end()
            regions.append((a, a + len(match.group(1)), match.group(1), 'list.symbol'))
            regions.append((a + len(match.group(1)), b, match.group(3), 'list.unordered'))

        # list ordered
        p = re.compile(r'^(( {4})*[0-9]+\.\s)(.+)$', flags=re.MULTILINE)
        for match in p.finditer(text):
            a = match.start()
            b = match.end()
            regions.append((a, a + len(match.group(1)), match.group(1), 'list.symbol'))
            regions.append((a + len(match.group(1)), b, match.group(3), 'list.ordered'))


        ### inline markup

        p = re.compile(r'([`]{1})(?!\s)(.+?)(?<!\s)(\1)')
        for match in p.finditer(text):
            a = match.start()
            b = match.end()
            regions.append((a, a + 1, match.group(1), 'code'))
            regions.append((a + 1, b - 1, match.group(2), 'code'))
            regions.append((b - 1, b, match.group(3), 'code'))
            # consume
            text = text[:a] + 'x' * len(match.group()) + text[b:]


        # zettel links
        p = re.compile(r'([\[]?\[)([0-9.]{12,18})([^]]*)(\][\]]?)')
        for match in p.finditer(text):
            regions.append((match.start(), match.end(), match.group(), 'zettel.link'))

        # citekeys for pandoc
        # also hackish for mmd
        p = re.compile(r'(\[[a-zA-Z:\.\s]*)(@|#)([^]]*)(\])')
        for match in p.finditer(text):
            a = match.start()
            a2 = a + len(match.group(1))
            a3 = a2 + len(match.group(2))
            a4 = a3 + len(match.group(3))
            b = match.end()
            b1 = a2
            b2 = a2 + len(match.group(2))
            b3 = b2 + len(match.group(3))
            regions.append((a, b1, match.group(1), 'default'))
            regions.append((a2, b2, match.group(2), 'citekey'))
            regions.append((a3, b3, match.group(3), 'citekey'))
            regions.append((a4, b, match.group(4), 'default'))
            # consume
            text = text[:a] + 'x' * len(match.group()) + text[b:]

        # footnotes
        p = re.compile(r'(\[)(\^)([^]]+)(\])')
        for match in p.finditer(text):
            print('footnote', match.group())
            a = match.start()
            a2 = a + len(match.group(1))
            a3 = a2 + len(match.group(2))
            a4 = a3 + len(match.group(3))
            b = match.end()
            b1 = a2
            b2 = a2 + len(match.group(2))
            b3 = b2 + len(match.group(3))
            regions.append((a, b1, match.group(1), 'default'))
            regions.append((a2, b2, match.group(2), 'footnote'))
            regions.append((a3, b3, match.group(3), 'footnote'))
            regions.append((a4, b, match.group(4), 'default'))
            # consume
            text = text[:a] + 'x' * len(match.group()) + text[b:]

        # todo begin:
        # * link normal
        # * link image
        # todo end


        # bolditalic
        p = re.compile(r'([\*_]{3})(?!\s)(.+?)(?<!\s)(\1)')
        for match in p.finditer(text):
            a = match.start()
            b = match.end()
            regions.append((a, a + 3, match.group(1), 'text.bolditalic.symbol'))
            regions.append((a + 3, b - 3, match.group(2), 'text.bolditalic.text'))
            regions.append((b - 3, b, match.group(3), 'text.bolditalic.symbol'))
            # consume
            text = text[:a] + 'x' * len(match.group()) + text[b:]

        # bold
        p = re.compile(r'([\*_]{2})(?!\s)(.+?)(?<!\s)(\1)')
        for match in p.finditer(text):
            a = match.start(1)
            b = match.end(3)
            regions.append((a, a + 2, match.group(1), 'text.bold.symbol'))
            regions.append((a + 2, b - 2, match.group(2), 'text.bold.text'))
            regions.append((b - 2, b, match.group(3), 'text.bold.symbol'))
            # consume
            text = text[:a] + 'x' * len(match.group()) + text[b:]

        # italic
        p = re.compile(r'([\*_]{1})(?!\s)(.+?)(?<!\s)(\1)')
        for match in p.finditer(text):
            a = match.start(1)
            b = match.end(3)
            regions.append((a, a + 1, match.group(1), 'text.italic.symbol'))
            regions.append((a + 1, b - 1, match.group(2), 'text.italic.text'))
            regions.append((b - 1, b, match.group(3), 'text.italic.symbol'))
            # consume
            text = text[:a] + 'x' * len(match.group()) + text[b:]


        # todo: sort and split regions
        # layering
        #    --> most important ones last
        regions.sort(key=lambda items: items[0])
        did_replace = True
        while did_replace:
            did_replace, regions = split_regions(regions)

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
            if previous_style_nr == 29:
                multiline_comm_flag = True
            ###
        ###
        # 4.2 Style the text in a loop
        for i, token in enumerate(token_list):
            if multiline_comm_flag:
                self.setStyling(token[1], 29)
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