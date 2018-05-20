import re

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont
from PyQt5.Qsci import *
from split_regions import CascadingStyleRegions
from settings import get_settings
KeyboardModifiers = int


class ZkMdLexer(QsciLexerCustom):

    note_id_clicked = pyqtSignal(str, bool, bool, bool)
    tag_clicked = pyqtSignal(str, bool, bool, bool)
    search_spec_clicked = pyqtSignal(str, bool, bool, bool)
    create_link_from_title_clicked = pyqtSignal(str, bool, bool, bool, int, int)
    cite_key_clicked = pyqtSignal(str, bool, bool, bool)
    hyperlink_clicked = pyqtSignal(str)


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
        self.headings = []
        self.settings = get_settings()
        self.double_brackets = self.settings.get('double_brackets', True)
        editor = self.parent()
        editor.indicatorClicked.connect(self.on_click_indicator)
        self.setAutoIndentStyle(0) # we are block based --> use blockLookback
        self.apply_theme()

    def apply_theme(self, new_theme = None):
        if new_theme is not None:
            self.theme = new_theme
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
            font_size = default_size
            try:
                font_size = int(current_style['size'])
            except ValueError:
                print('illegal size in', current_style)
                pass
            self.setFont(QFont(current_style['face'], font_size, weight=weight, italic=italic), styleid)
            self.setEolFill(True, styleid)

        # indicators for clickable links
        self.indicator_id_noteid = 0
        self.indicator_id_tag = 1
        self.indicator_id_search_spec = 2
        self.indicator_id_only_notetitle = 3
        self.indicator_id_citekey = 4
        self.indicator_id_hyperlink = 5
        self.num_indicators = 6
        editor = self.parent()
        editor.indicatorDefine(QsciScintilla.PlainIndicator, self.indicator_id_noteid)
        editor.indicatorDefine(QsciScintilla.PlainIndicator, self.indicator_id_tag)
        editor.indicatorDefine(QsciScintilla.FullBoxIndicator, self.indicator_id_search_spec)
        editor.indicatorDefine(QsciScintilla.PlainIndicator, self.indicator_id_only_notetitle)
        editor.indicatorDefine(QsciScintilla.PlainIndicator, self.indicator_id_citekey)
        editor.indicatorDefine(QsciScintilla.PlainIndicator, self.indicator_id_hyperlink)

        editor.setIndicatorForegroundColor(QColor(self.theme.style_infos['zettel.link']['color']), self.indicator_id_noteid)
        editor.setIndicatorForegroundColor(QColor(self.theme.style_infos['tag']['color']), self.indicator_id_tag)
        #editor.setIndicatorForegroundColor(QColor(self.theme.style_infos['search.spec']['color']), self.indicator_id_search_spec)
        editor.setIndicatorForegroundColor(QColor('#1f268bd2'), self.indicator_id_search_spec)
        editor.setIndicatorForegroundColor(QColor(self.theme.style_infos['zettel.link']['color']), self.indicator_id_only_notetitle)
        editor.setIndicatorForegroundColor(QColor(self.theme.style_infos['citekey']['color']), self.indicator_id_citekey)
        editor.setIndicatorForegroundColor(QColor(self.theme.style_infos['link.url']['color']), self.indicator_id_hyperlink)
        

    def blockLookback(self):
        """
        if autoindentstyle == 0 (block based):
            how many lines to look up backwards to determine the indent level
        """
        return 1

    def get_headings(self):
        """
        Return ordered list of headings in document as
        tuple (line_string, heading_level, start_pos, end_pos)
        """
        return self.headings

    def clear_indicators(self):
        editor = self.parent()
        num_bytes = editor.length()
        for i in range(self.num_indicators):
            editor.SendScintilla(QsciScintilla.SCI_SETINDICATORCURRENT, i)
            editor.SendScintilla(QsciScintilla.SCI_INDICATORCLEARRANGE, 0, num_bytes)

    def make_clickable(self, startpos, length, indicator_id):
        # Tell the editor which indicator-style to use
        # (pass it the indicator-style ID number)
        editor = self.parent()
        text = editor.text()

        editor.SendScintilla(QsciScintilla.SCI_SETINDICATORCURRENT, indicator_id)
        # Assign a value to the text
        b_start = len(bytearray(text[:startpos], 'utf-8').decode('ascii', errors='replace'))
        b_length = len(bytearray(text[startpos:startpos + length], 'utf-8').decode('ascii', errors='replace'))

        editor.SendScintilla(QsciScintilla.SCI_SETINDICATORVALUE, startpos)
        # Now apply the indicator-style on the chosen text
        editor.SendScintilla(QsciScintilla.SCI_INDICATORFILLRANGE, b_start, b_length)

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
        hyperlink_pos = self.parent().SendScintilla(QsciScintilla.SCI_INDICATORVALUEAT, self.indicator_id_hyperlink, position)

        if search_spec_pos:
            # get until end of line
            search_spec = self.parent().text()[search_spec_pos:].split('\n', 1)[0]
            # emit note clicked signal
            self.search_spec_clicked.emit(search_spec, ctrl, alt, shift)
            #print('search spec clicked:', search_spec)
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
        elif hyperlink_pos:
            p = re.compile('.*?\)')
            match = p.match(self.parent().text()[hyperlink_pos:hyperlink_pos + 200])
            if match:
                hyperlink = match.group()[:-1]
                self.hyperlink_clicked.emit(hyperlink)


    def language(self):
        return "MardownZettelkasten"

    def description(self, style):
        if style in self.id2stylename:
            return self.id2stylename[style]
        else:
            return ''

    def styleText(self, start, end):
        self.clear_indicators()
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

            p = re.compile(r'(:\s+)(true|false|[0-9]+)')
            for match in p.finditer(text):
                a = match.start(2)
                b = match.end(2)
                # print(match.group(2))
                regions.append((a, b, match.group(2), 'footnote'))
                # consume
                # print(match.groups() , match.group())
                # erase including colon
                text = text[:match.start(1)] + 'x' * len(match.group()) + text[b:]

            p = re.compile(r':\s*(.*),\s*$', flags=re.MULTILINE)
            for match in p.finditer(text):
                # print(match.groups())
                a = match.start(1)
                b = match.end(1)
                regions.append((a, b, match.group(1), 'tag'))

            self.apply_regions(regions, text)
            return

        ### non-inline

        # only for search spec area: search specs:
        if self.highlight_saved_searches:

            p = re.compile(r'(^.+?: )([ \t]*)([^\n]+?)$', flags=re.MULTILINE)    # don't capture the newline! we don't want to highlight till EOL
            p_sub = re.compile(r'(=\w+?\(.*?\)\s*?)?{sortby:\s*?(id|title|refcount|mtime|history)\s*?(,\s*?order:\s*?(asc|desc))?\s*?}')
            for match in p.finditer(text):
                #print(match.groups())
                a1 = match.start(1)
                a2 = match.start(3)
                b = match.end()

                regions.append((a1, a2, match.group(1) + match.group(2), 'search.name'))
                # only style if the function is not the whole spec
                #   because that will be done later
                if not p_sub.match(match.group(3)):
                    regions.append((a2, b, match.group(3), 'search.spec'))

                # make clickable
                self.make_clickable(a2, len(match.group(3)), self.indicator_id_search_spec)

            # special instructions
            for match in p_sub.finditer(text):
                #print('search code:', match.group())
                a = match.start()
                b = match.end()
                regions.append((a, b, match.group(), 'search.code'))
            


        # tags in comments (but not in code blocks)
        # hence, consume code blocks first
        # fenced code blocks
        p = re.compile(r'(\n[ \t]*\n)(```)(.|\n)*?(\n```\n)')
        for match in p.finditer(text):
            #print('fenced', match.groups())
            a = match.start() + 1
            a2 = match.start(2) # just the ````
            b = match.end()
            regions.append((a2, b, 'nop', 'code.fenced'))
            # above: nop will be replaced by the CSR anyway
            # consume
            text = text[:a] + 'x' * (len(match.group()) - 1) + text[b:]


        # headings
        self.headings = []
        p = re.compile('^(#{1,6})(.+)$', flags=re.MULTILINE)
        for match in p.finditer(text):
            #print('heading', match.groups())
            a = match.start()
            b = match.end()
            n = match.group(1).count('#')
            regions.append((a, a + len(match.group(1)), match.group(1), 'h.symbol'))
            regions.append((a + len(match.group(1)), b, match.group(2), f'h{n}.text'))
            self.headings.append((match.group(), n, a, b))

        # quotes
        p = re.compile('^(>)(.+)$', flags=re.MULTILINE)
        for match in p.finditer(text):
            a = match.start()
            b = match.end()
            regions.append((a, a + len(match.group(1)), match.group(1), 'quote.symbol'))
            regions.append((a + len(match.group(1)), b+1, match.group(2)+'\n', 'quote.text'))

        no_blocks_in = []
        # list unordered
        p = re.compile(r'^( {4}|\t)*([\*-])([ \t]+[^\n]+?)$', flags=re.MULTILINE)
        cont_line_re = re.compile(r'(^[ \t]+)([^-\* \t])([^\n]*)$', flags=re.MULTILINE)

        for match in p.finditer(text):
            print(match.group())
            print(match.groups())
            a = match.start()
            b = match.end()
            a1 = match.start()
            b1 = match.end(1)
            a2 = match.start(2)
            b2 = match.end(2)
            a3 = match.start(3)
            b3 = match.end(3)

            if match.start(1) < 0:
                # we are at the outmost level, so a1 = -1
                a1 = match.start()
            else:
                # we are at an inner level
                # --> check if we are a continuation
                if not no_blocks_in:
                    # skip this, as it is not a continuation
                    continue
                prev_item_start, prev_item_end = no_blocks_in[-1]
                if a1 - prev_item_end >= 2:
                    continue
            # now look for continuation lines:
            #    (lines that start with an indentation > len_symbol)
            len_symbol = b2 - a1
            keep_looking = True
            while keep_looking:
                cont_text = text[b + 1:]
                cont_match = cont_line_re.match(cont_text)
                if not cont_match:
                    break
                if len(cont_match.group(1)) < len_symbol - 1:
                    break
                b += cont_match.end() + 1

            no_blocks_in.append((a, b))
            symbol = match.group()[:len_symbol]
            nosymbol = match.group()[len_symbol:]
            regions.append((a, a + len_symbol, symbol, 'list.symbol'))
            regions.append((a + len_symbol, b, nosymbol, 'list.unordered'))
            # consume the symbol
            sym_start = a1
            sym_end = b2
            text = text[:sym_start] + 'B' * len_symbol + text[sym_end:] 

        # list ordered
        p = re.compile(r'^( {4}|\t)*([0-9\.]+?\.)([ \t]+[^\n]+)$', flags=re.MULTILINE)
        for match in p.finditer(text):
            #print('ordered', match.groups())
            a = match.start()
            b = match.end()
            a1 = match.start()
            b1 = match.end(1)
            a2 = match.start(2)
            b2 = match.end(2)
            a3 = match.start(3)
            b3 = match.end(3)

            if match.start(1) < 0:
                # we are at the outmost level
                a1 = match.start()
            else:
                # we are at an inner level
                # --> check if we are a continuation
                if not no_blocks_in:
                    # skip this, as it is not a continuation
                    continue
                prev_item_start, prev_item_end = no_blocks_in[-1]
                if a1 - prev_item_end >= 2:
                    continue
            # now look for continuation lines:
            #    (lines that start with an indentation > len_symbol)
            len_symbol = b2 - a1
            keep_looking = True
            while keep_looking:
                cont_text = text[b + 1:]
                cont_match = cont_line_re.match(cont_text)
                if not cont_match:
                    break
                if len(cont_match.group(1)) < len_symbol - 1:
                    break
                b += cont_match.end() + 1

            no_blocks_in.append((a, b))
            symbol = match.group()[:len_symbol]
            nosymbol = match.group()[len_symbol:]
            regions.append((a, a + len_symbol, symbol, 'list.symbol'))
            regions.append((a + len(nosymbol), b, nosymbol, 'list.ordered'))

        # indented code blocks
        ### NEED TO STYLE THE \n at the end!!!
        if self.show_block_quotes:
            p = re.compile(r'(\n[ \t]*\n)(( {4}|\t)+[^\n]*?\n)+')
            pos = 0
            while True:
                match = p.search(text, pos)
                if not match:
                    break
                a = match.start(1) + 1
                a2 = match.start(2)
                b = match.end()
                # don't block-quote list-sub-items
                skip_this = False
                for no_a, no_b in no_blocks_in:
                    if a >= no_a and b <= no_b + 1:
                        skip_this = True
                if skip_this:
                    pos = b - 1
                    continue
                regions.append((a + len(match.group(1)) - 1, b, match.group(2)[:-1], 'code.fenced'))
                # above: match.group(2) only captures the last match. this is OK here, since the text will be ignored here and CSR will figure the real text out later, based on the indices
                # consume
                text = text[:a] + 'x' * (len(match.group()) - 2) + text[b - 1:]
                pos = b - 1

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
            self.make_clickable(gstarts[3], len(gtexts[3]), self.indicator_id_hyperlink)

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
            self.make_clickable(gstarts[3], len(gtexts[3]), self.indicator_id_hyperlink)

        # bolditalic
        p = re.compile(r'(\*{3}|_{3})(?!\s)([^\n]+?)(?<!\s)(\1)')
        for match in p.finditer(text):
            # print('bolditalic', match.groups(), match.start())
            a = match.start()
            b = match.end()
            regions.append((a, a + 3, match.group(1), 'text.bolditalic.symbol'))
            regions.append((a + 3, b - 3, match.group(2), 'text.bolditalic.text'))
            regions.append((b - 3, b, match.group(3), 'text.bolditalic.symbol'))
            # consume
            text = text[:a] + 'I' * len(match.group()) + text[b:]

        # bold
        p = re.compile(r'(\*{2}|_{2})(?!\s)([^\n]+?)(?<!\s)(\1)')
        for match in p.finditer(text):
            # print('bold', match.groups(), match.start())
            a = match.start(1)
            b = match.end(3)
            regions.append((a, a + 2, match.group(1), 'text.bold.symbol'))
            regions.append((a + 2, b - 2, match.group(2), 'text.bold.text'))
            regions.append((b - 2, b, match.group(3), 'text.bold.symbol'))
            # consume
            text = text[:a] + 'b' * len(match.group()) + text[b:]

        # italic
        p = re.compile(r'(\*{1}|_{1})(?!\s)([^\n]+?)(?<!\s)(\1)')
        for match in p.finditer(text):
            # print('italic', match.groups(), match.start(), f'|{match.group()}|')
            a = match.start(1)
            b = match.end(3)
            regions.append((a, a + 1, match.group(1), 'text.italic.symbol'))
            regions.append((a + 1, b - 1, match.group(2), 'text.italic.text'))
            regions.append((b - 1, b, match.group(3), 'text.italic.symbol'))
            # consume
            text = text[:a] + 'i' * len(match.group()) + text[b:]

        # comments
        p = re.compile(r'(<!--)(.|\n)*?(-->)')
        for match in p.finditer(text):
            # print('comment', match.groups(), match.group())
            a = match.start(1)
            b = match.end(3)
            regions.append((a, b, match.group(), 'comment'))
            # consume
            # print(match.groups() , match.group())
            text = text[:a] + 'x' * len(match.group()) + text[b:]

        # zettel links without noteid -> create note
        p = re.compile(r'([\[]?\[)([^]\n]*)(\][\]]?)')
        for match in p.finditer(text):
            if self.double_brackets:
                if match.group(1) == '[':
                    continue
            #print('create zettel', match.group())
            regions.append((match.start(), match.end(), match.group(), 'zettel.link'))
            # make clickable
            self.make_clickable(match.start(2), len(match.group(2)), self.indicator_id_only_notetitle)

        self.apply_regions(regions, orig_text)

    def apply_regions(self, regions, text):
        # sort and split regions
        regions = [r for r in regions if r[0] < r[1]] # filter out empty regions
        csr = CascadingStyleRegions(text)
        regions = csr.apply_regions(regions)
        style_regions = []
        # now translate regions to byte arrays
        current_pos = 0
        for region in regions:
            region_start = region[0]
            region_end = region[1]
            region_text = region[2]
            region_style = region[3]

            match_b = len(bytearray(region_text, 'utf-8'))
            match = region_end - region_start
            style_regions.append((match_b, region_style))
            current_pos += match
        for num_chars, style in style_regions:
            self.setStyling(num_chars, self.style2id[style])
    ''''''
