import re

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont
from PyQt5.Qsci import *
from split_regions import split_regions

KeyboardModifiers = int

class ZkMdLexer(QsciLexerCustom):

    note_id_clicked = pyqtSignal(str, bool, bool, bool)
    tag_clicked = pyqtSignal(str, bool, bool, bool)
    search_spec_clicked = pyqtSignal(str, bool, bool, bool)
    create_link_from_title_clicked = pyqtSignal(str, bool, bool, bool, int, int)
    cite_key_clicked = pyqtSignal(str, bool, bool, bool)

    def __init__(self, parent, theme, highlight_saved_searches=False, show_block_quotes=True,
                 settings_mode=False):
        super(ZkMdLexer, self).__init__(parent)
        self.theme = theme
        self.style_infos = {}
        self.style2id = {}
        self.id2stylename = {}
        self.highlight_saved_searches = highlight_saved_searches
        self.show_block_quotes = show_block_quotes
        self.settings_mode = settings_mode

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
            #print(f'Initializing style {styleid:02d} : {style:22} : '
            #      f'{self.theme.style_infos[style]}')
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

        # indicators for clickable links
        self.indicator_id_noteid = 0
        self.indicator_id_tag = 1
        self.indicator_id_search_spec = 2
        self.indicator_id_only_notetitle = 3
        self.indicator_id_citekey = 4
        editor = self.parent()
        editor.indicatorDefine(QsciScintilla.PlainIndicator, self.indicator_id_noteid)
        editor.indicatorDefine(QsciScintilla.PlainIndicator, self.indicator_id_tag)
        editor.indicatorDefine(QsciScintilla.PlainIndicator, self.indicator_id_search_spec)
        editor.indicatorDefine(QsciScintilla.PlainIndicator, self.indicator_id_only_notetitle)
        editor.indicatorDefine(QsciScintilla.PlainIndicator, self.indicator_id_citekey)

        editor.indicatorClicked.connect(self.on_click_indicator)
        editor.setIndicatorForegroundColor(QColor(self.theme.style_infos['zettel.link']['color']), self.indicator_id_noteid)
        editor.setIndicatorForegroundColor(QColor(self.theme.style_infos['tag']['color']), self.indicator_id_tag)
        editor.setIndicatorForegroundColor(QColor(self.theme.style_infos['search.spec']['color']), self.indicator_id_search_spec)
        editor.setIndicatorForegroundColor(QColor(self.theme.style_infos['zettel.link']['color']), self.indicator_id_only_notetitle)
        editor.setIndicatorForegroundColor(QColor(self.theme.style_infos['citekey']['color']), self.indicator_id_citekey)

    def make_clickable(self, startpos, length, indicator_id):
        # Tell the editor which indicator-style to use
        # (pass it the indicator-style ID number)
        editor = self.parent()
        editor.SendScintilla(QsciScintilla.SCI_SETINDICATORCURRENT, indicator_id)
        # Assign a value to the text
        editor.SendScintilla(QsciScintilla.SCI_SETINDICATORVALUE, startpos)
        # Now apply the indicator-style on the chosen text
        editor.SendScintilla(QsciScintilla.SCI_INDICATORFILLRANGE, startpos, length)

    def on_click_indicator(self, line, index, keys):
        #print('click', line, index, type(keys))
        position = self.parent().positionFromLineIndex(line, index)
        alt = bool(keys & Qt.AltModifier)
        shift = bool(keys & Qt.ShiftModifier)
        ctrl = bool(keys & Qt.ControlModifier)

        tag_pos = self.parent().SendScintilla(QsciScintilla.SCI_INDICATORVALUEAT, self.indicator_id_tag, position)
        noteid_pos = self.parent().SendScintilla(QsciScintilla.SCI_INDICATORVALUEAT, self.indicator_id_noteid, position)
        search_spec_pos = self.parent().SendScintilla(QsciScintilla.SCI_INDICATORVALUEAT, self.indicator_id_search_spec, position)
        only_notetitle_pos = self.parent().SendScintilla(QsciScintilla.SCI_INDICATORVALUEAT, self.indicator_id_only_notetitle, position)
        citekey_pos = self.parent().SendScintilla(QsciScintilla.SCI_INDICATORVALUEAT, self.indicator_id_citekey, position)

        if search_spec_pos:
            # get until end of line
            search_spec = self.parent().text()[search_spec_pos:].split('\n', 1)[0]
            # emit note clicked signal
            self.search_spec_clicked.emit(search_spec, ctrl, alt, shift)
            print('search spec clicked:', search_spec)
        elif noteid_pos:
            p = re.compile(r'([0-9.]{12,18})')
            match = p.match(self.parent().text()[noteid_pos:noteid_pos + 20])
            if match:
                note_id = match.group(1)
                # emit note clicked signal
                self.note_id_clicked.emit(note_id, ctrl, alt, shift)
        elif tag_pos:
            p = re.compile(r'(#+([^#\W]|[-§]|:[a-zA-Z0-9])+)')
            match = p.match(self.parent().text()[tag_pos:tag_pos + 100])
            if match:
                tag = match.group(1)
                # emit tag clicked signal
                self.tag_clicked.emit(tag, ctrl, alt, shift)
        elif only_notetitle_pos:
            p = re.compile(r'([^]\n]*)(\][\]]?)')
            match = p.match(self.parent().text()[only_notetitle_pos:only_notetitle_pos + 100])
            if match:
                link_title = match.group(1)
                self.create_link_from_title_clicked.emit(link_title, ctrl, alt, shift, only_notetitle_pos, len(link_title))
        elif citekey_pos:
            p = re.compile(r'([a-zA-Z:\.\s]*)(@|#)([^]\n]*)(\])')
            match = p.match(self.parent().text()[citekey_pos:citekey_pos + 100])
            if match:
                citekey = match.group()[:-1]
                # emit tag clicked signal
                self.cite_key_clicked.emit(citekey, ctrl, alt, shift)


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

        if self.settings_mode:
            # comments
            p = re.compile(r'(//)(.*)$', flags=re.MULTILINE)
            for match in p.finditer(text):
                a = match.start(1)
                b = match.end(2)
                regions.append((a, b, match.group(1) + match.group(2), 'comment'))
                # consume
                # print(match.groups() , match.group())
                text = text[:a] + 'x' * len(match.group(1) + match.group(2)) + text[b:]

            p = re.compile(r':\s*(.*),$', flags=re.MULTILINE)
            for match in p.finditer(text):
                # print(match.groups())
                a = match.start(1)
                b = match.end(1)
                regions.append((a, b, match.group(1), 'tag'))

            p = re.compile(r'(true|false|[0-9]+)')
            for match in p.finditer(text):
                a = match.start(1)
                b = match.end(1)
                regions.append((a, b, match.group(), 'footnote'))
                # consume
                # print(match.groups() , match.group())
                text = text[:a] + 'x' * len(match.group()) + text[b:]
            self.apply_regions(regions, text)
            return

        ### non-inline

        # only for search spec area: search specs:
        if self.highlight_saved_searches:
            p = re.compile(r'(^.+?:)([ \t]*)([^\n]+)$', flags=re.MULTILINE)    # don't capture the newline! we don't want to highlight till EOL
            for match in p.finditer(text):
                # print(match.groups())
                a1 = match.start(1)
                a2 = match.start(3)
                b = match.end()
                regions.append((a1, a2, match.group(1)+match.group(2), 'search.name'))
                regions.append((a2, b, match.group(3), 'search.spec'))
                # make clickable
                self.make_clickable(a2, len(match.group(3)), self.indicator_id_search_spec)

        # tags in comments (but not in code blocks)
        # hence, consume code blocks first
        # code blocks
        p = re.compile(r'(```)(.|\n)*?(```)')
        for match in p.finditer(text):
            a = match.start(1)
            b = match.end(3)
            regions.append((a, b+1, match.group() + '\n', 'code.fenced'))
            # consume
            text = text[:a] + 'x' * (len(match.group())) + text[b:]


        # headings
        p = re.compile('^(#{1,6})(.+)$', flags=re.MULTILINE)
        for match in p.finditer(text):
            #print('heading', match.groups())
            a = match.start()
            b = match.end()
            n = match.group(1).count('#')
            regions.append((a, a + len(match.group(1)), match.group(1), 'h.symbol'))
            regions.append((a + len(match.group(1)), b, match.group(2), f'h{n}.text'))

        # quotes
        p = re.compile('^(>)(.+)$', flags=re.MULTILINE)
        for match in p.finditer(text):
            a = match.start()
            b = match.end()
            regions.append((a, a + len(match.group(1)), match.group(1), 'quote.symbol'))
            regions.append((a + len(match.group(1)), b+1, match.group(2)+'\n', 'quote.text'))

        # block quotes
        ### NEED TO STYLE THE \n !!!
        if self.show_block_quotes:
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

        # tags
        p = re.compile(r'([ \t])(#+([^#\W]|[-§]|:[a-zA-Z0-9])+)')
        for match in p.finditer(text):
            #print('tag', match.groups())
            a = match.start(2)
            b = match.end(3)
            regions.append((a, b, match.group(2), 'tag'))
            # consume
            text = text[:a] + 'x' * (len(match.group(2))) + text[b:]
            # make clickable
            self.make_clickable(a, len(match.group(2)), self.indicator_id_tag)

        # inline code
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
        p = re.compile(r'([\[]?\[)([0-9.]{12,18})([^]\n]*)(\][\]]?)')
        for match in p.finditer(text):
            # print('zettel', match.group())
            a = match.start()
            b = match.end()
            regions.append((match.start(), match.end(), match.group(), 'zettel.link'))
            # make clickable
            self.make_clickable(match.start(2), len(match.group(2)), self.indicator_id_noteid)
            # consume
            text = text[:a] + 'x' * len(match.group()) + text[b:]

        # citekeys for pandoc
        # also hackish for mmd
        p = re.compile(r'(\[[a-zA-Z:\.\s]*)(@|#)([^]\n]*)(\])')
        for match in p.finditer(text):
            #print('citekey', match.group())
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
            # make clickable
            self.make_clickable(a+1, len(match.group(1)) - 1 + len(match.group(2)) + len(match.group(3)), self.indicator_id_citekey)

        # footnotes
        p = re.compile(r'(\[)(\^)([^]\n]+)(\])')
        for match in p.finditer(text):
            #print('footnote', match.group())
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

        # images
        p = re.compile(r'(!\[)([^\n]*)(\]\()([^\n]*)(\))(\s*\{)?([^\}\n]*)(\})?')
        for match in p.finditer(text):
            #print('image', match.group())
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
            b = gstops[4]
            replace_str = ''.join(gtexts[:5])
            if gtexts[5] and gtexts[6] and gtexts[7]:
                regions.append((gstarts[5], gstops[5], gtexts[5], 'link.attr'))
                regions.append((gstarts[6], gstops[6], gtexts[6], 'link.attr'))
                regions.append((gstarts[7], gstops[7], gtexts[7], 'link.attr'))
                b = gstops[7]
                replace_str = ''.join(gtexts)
            # consume
            text = text[:a] + 'x' * len(replace_str) + text[b:]

        # links
        p = re.compile(r'(\[)([^\n]*)(\]\()([^\n]*)(\))(\s*\{)?([^\}\n]*)(\})?')
        for match in p.finditer(text):
            a = match.start()
            #print('link', match.group(), match.groups())
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
            b = gstops[4]
            replace_str = ''.join(gtexts[:5])
            if gtexts[5] and gtexts[6] and gtexts[7]:
                regions.append((gstarts[5], gstops[5], gtexts[5], 'link.attr'))
                regions.append((gstarts[6], gstops[6], gtexts[6], 'link.attr'))
                regions.append((gstarts[7], gstops[7], gtexts[7], 'link.attr'))
                b = gstops[7]
                replace_str = ''.join(gtexts)
            # consume
            text = text[:a] + 'x' * len(replace_str) + text[b:]

        # bolditalic
        p = re.compile(r'([\*_]{3})(?!\s)([^\n]+?)(?<!\s)(\1)')
        for match in p.finditer(text):
            a = match.start()
            b = match.end()
            regions.append((a, a + 3, match.group(1), 'text.bolditalic.symbol'))
            regions.append((a + 3, b - 3, match.group(2), 'text.bolditalic.text'))
            regions.append((b - 3, b, match.group(3), 'text.bolditalic.symbol'))
            # consume
            text = text[:a] + 'x' * len(match.group()) + text[b:]

        # bold
        p = re.compile(r'([\*_]{2})(?!\s)([^\n]+?)(?<!\s)(\1)')
        for match in p.finditer(text):
            a = match.start(1)
            b = match.end(3)
            regions.append((a, a + 2, match.group(1), 'text.bold.symbol'))
            regions.append((a + 2, b - 2, match.group(2), 'text.bold.text'))
            regions.append((b - 2, b, match.group(3), 'text.bold.symbol'))
            # consume
            text = text[:a] + 'x' * len(match.group()) + text[b:]

        # italic
        p = re.compile(r'([\*_]{1})(?!\s)([^\n]+?)(?<!\s)(\1)')
        for match in p.finditer(text):
            a = match.start(1)
            b = match.end(3)
            regions.append((a, a + 1, match.group(1), 'text.italic.symbol'))
            regions.append((a + 1, b - 1, match.group(2), 'text.italic.text'))
            regions.append((b - 1, b, match.group(3), 'text.italic.symbol'))
            # consume
            text = text[:a] + 'x' * len(match.group()) + text[b:]

        # comments
        p = re.compile(r'(<!--)(.|\n)*?(-->)')
        for match in p.finditer(text):
            a = match.start(1)
            b = match.end(3)
            regions.append((a, b, match.group(), 'comment'))
            # consume
            # print(match.groups() , match.group())
            text = text[:a] + 'x' * len(match.group()) + text[b:]

        # zettel links without noteid -> create note
        p = re.compile(r'([\[]?\[)([^]\n]*)(\][\]]?)')
        for match in p.finditer(text):
            #print('create zettel', match.group())
            regions.append((match.start(), match.end(), match.group(), 'zettel.link'))
            # make clickable
            self.make_clickable(match.start(2), len(match.group(2)), self.indicator_id_only_notetitle)

        self.apply_regions(regions, text)

    def apply_regions(self, regions, text):
        # sort and split regions
        # layering
        #    --> most important ones last
        regions = [r for r in regions if r[0] < r[1]]    # filter out impty regions
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

        for num_chars, style in style_regions:
            if num_chars > 0:
                self.setStyling(num_chars, self.style2id[style])
    ''''''
