import re

from PyQt5.QtGui import QColor, QFont
from PyQt5.Qsci import *
from split_regions import split_regions


class ZkMdLexer(QsciLexerCustom):
    def __init__(self, parent, theme):
        super(ZkMdLexer, self).__init__(parent)
        self.theme = theme
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
                                   weight=weight, italic=italic,
                                   )
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

    def description(self, style):
        if style in self.id2stylename:
            return self.id2stylename[style]
        else:
            return ''

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

        # images
        p = re.compile(r'(!\[)(.*)(\]\()(.*)(\))(\s*\{)?([^\}]*)(\})?')
        '''
            '1': meta.image.inline.markdown punctuation.definition.image.begin.markdown
            '2': meta.image.inline.description.markdown
            '3': meta.image.inline.markdown punctuation.definition.metadata.begin.markdown
            '4': meta.image.inline.markdown markup.underline.link.image.markdown
            '5': meta.image.inline.markdown punctuation.definition.metadata.end.markdown
            '6': meta.image.inline.markdown punctuation.definition.imageattr.begin.markdown
            '7': meta.image.inline.markdown.imageattr
            '8': meta.image.inline.markdown punctuation.definition.imageattr.end.markdown
        '''
        for match in p.finditer(text):
            print('img', match.groups())
            a = match.start()
            gstarts = []
            gstops = []
            gtexts = []
            qstart = a
            for gindex in range(8):
                gstarts.append(qstart)
                gtext = match.group(gindex + 1)
                if gtext is None:
                    gtext = ''
                gtexts.append(gtext)
                qstart += len(gtext)
                gstops.append(qstart)
            b = match.end()
            regions.append((gstarts[0], gstops[0], gtexts[0], 'default'))
            regions.append((gstarts[1], gstops[1], gtexts[1], 'link.caption'))
            regions.append((gstarts[2], gstops[2], gtexts[2], 'default'))
            regions.append((gstarts[3], gstops[3], gtexts[3], 'link.url'))
            regions.append((gstarts[4], gstops[4], gtexts[4], 'default'))
            if gtexts[5] and gtexts[6] and gtexts[7]:
                regions.append((gstarts[5], gstops[5], gtexts[5], 'link.attr'))
                regions.append((gstarts[6], gstops[6], gtexts[6], 'link.attr'))
                regions.append((gstarts[7], gstops[7], gtexts[7], 'link.attr'))
            # consume
            text = text[:a] + 'x' * len(match.group()) + text[b:]

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

        # sort and split regions
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
    ''''''
