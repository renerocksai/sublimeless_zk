import os
import json

class Theme:
    def __init__(self, theme_file):
        self.style_infos = {}
        self.style2id = {}
        self.id2stylename = {}
        self.caret = None
        self.font_info = {}
        self.hightlight = None
        self.selection = None
        self.line_pad_bottom = 3
        self.line_pad_top = 3

        self.load_theme(theme_file)
        for styleid, style in enumerate(self.style_infos):
            self.style2id[style] = styleid
            self.id2stylename[styleid] = style

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
        theme_d = {}
        if not os.path.exists(theme_file):
            pass
        with open(theme_file, 'rt') as f:
            try:
                theme_d = json.load(f)
            except:
                print('ERROR loading', theme_file)

        # now fill in the blanks
        self.theme_d = theme_d
        background = theme_d.get('background', "#fffdf6e3")
        foreground = theme_d.get('foreground', "#ff657b83")

        self.highlight = theme_d.get('linehighlight', "#3F3D3812")
        self.line_pad_bottom = theme_d.get('line_padding_bottom', self.line_pad_bottom)
        self.line_pad_top = theme_d.get('line_padding_top', self.line_pad_bottom)
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
