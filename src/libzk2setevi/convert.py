#!/usr/bin/env python3
# -*- coding: utf8 -*-

from .zkutils import *
from .bibstuff import Autobib
import os
from collections import defaultdict
import markdown as md
import json
import shutil
import struct
import imghdr
from pygments import highlight
from pygments.lexers import guess_lexer
from pygments.formatters.html import HtmlFormatter
import pypandoc
import pymmd
from datetime import datetime


pymmd.load_mmd()

def pandoc_markdown(text):
    return pypandoc.convert_text(text, 'html', format='md', extra_args=['--mathjax', '--highlight-style=tango'])


def mmd_markdown(text):
    return pymmd.convert(text, ext=pymmd.SNIPPET)


def native_markdown(text):
    return md.markdown(text)

mmd_markdown('pyinstaller')

available_parsers = {'basic': native_markdown, 'pandoc': pandoc_markdown, 'mmd': mmd_markdown}


def progress_callback(counter, count, msg):
    print('\r{:4d} / {:4d} [{:3d}%] {}'.format(counter, count, int(counter / count * 100), msg), end='', flush=True)


def finish_callback():
    print()


class Zk2Setevi:
    def __init__(self, home, project=None, out_folder=None, bibfile=None, extension='.md', linkstyle='double',
                 parser=None, max_img_width=320, progress_callback=progress_callback, finish_callback=finish_callback,
                 base_url='', timestamp_from = '00000000000000', timestamp_until='22221231235900',
                 white_tags=None, black_tags=None):
        if project is None:
            raise RuntimeError('no project')
        if out_folder is None:
            raise RuntimeError('no output folder')
        self.project = project
        self.home = home
        os.makedirs(out_folder, exist_ok=True)
        self.out_folder = out_folder
        self.img_folder_rel = 'imgs'
        self.img_folder = os.path.join(out_folder, self.img_folder_rel)
        self.base_url = base_url
        if self.base_url.endswith('/'):
            self.base_url = self.base_url[:-1]

        self.timestamp_from = self.parse_timestamp(timestamp_from)
        self.timestamp_until = self.parse_timestamp(timestamp_until)
        self.white_tags = white_tags.replace('\'', '').replace('"', '').split()
        self.black_tags = black_tags.replace('\'', '').replace('"', '').split()

        os.makedirs(self.img_folder, exist_ok=True)
        self.extension = extension
        self.linkstyle = linkstyle
        self.max_img_width = max_img_width
        self.progress_callback = progress_callback
        self.finish_callback = finish_callback

        if parser is None:
            parser = 'basic'
        self.parser = parser
        if parser in available_parsers:
            self.markdown = available_parsers[parser]
            print('Using parser `{}`'.format(parser))
        else:
            print('Parser `{}` is not available; reverting back to basic!'.format(parser))
            self.markdown = available_parsers['basic']
            self.parser = 'basic'

        if linkstyle not in ['single', 'double', '§']:
            linkstyle = 'double'
        if linkstyle == 'double':
            self.link_prefix = '[['
            self.link_postfix = ']]'
        elif linkstyle == 'single':
            self.link_prefix = '['
            self.link_postfix = ']'
        else:
            self.link_prefix = '§'
            self.link_postfix = ''

        self.bibfile = bibfile
        if bibfile is None:
            # try to find it in the ZK folder
            self.bibfile = Autobib.look_for_bibfile(self.project.folder)
        self.bib_citekeys = []
        self.note_tags = {}
        self.tag_notes = defaultdict(set)
        self.note_titles = {}
        self.citing_notes = defaultdict(set)
        self.json_note_ids = {}
        self.json_tag_ids = {}
        self.json_citekey_ids = {}
        self.json_id_counter = -1
        self.json_nodes = []

        self.vertical_layout = True

    @staticmethod
    def parse_timestamp(timestamp_str):
        dt = None
        input_len = len(timestamp_str)
        timestamp_str = timestamp_str[:14]
        if input_len < 14:
            timestamp_str += '0' * (14 - input_len)
        try:
            dt = datetime.strptime(timestamp_str, '%Y%m%d%H%M%S')
        except ValueError:
            pass
        return dt

    def next_id(self):
        self.json_id_counter += 1
        return self.json_id_counter

    def get_all_notes(self):
        """
        Return all files with extension in folder.
        """
        return self.project.get_all_note_files()

    def find_all_notes_all_tags(self):
        """
        Manual implementation to get a dict mapping note_ids to tags
        and tags to note ids. Also record note titles.
        Added Filtering based on date range and tag black / whitelists
        """
        # manual implementation
        for filn in self.get_all_notes():
            note_id = self.get_note_id_of_file(filn)
            if not note_id:
                continue
            # date range check
            note_dt = self.parse_timestamp(note_id)
            if note_dt < self.timestamp_from or note_dt > self.timestamp_until:
                continue

            note_id, title = os.path.basename(filn).split(' ', 1)
            note_filn = self.project.note_file_by_id(note_id)
            title = title.replace(self.extension, '')
            if not note_filn:
                continue


            tags, citekeys = self.extract_tags_and_citekeys(note_filn)

            # tag whitelist
            if self.white_tags:
                whitelisted = [tag for tag in tags if tag in self.white_tags]
                if not whitelisted:
                    continue

            # tag blacklist
            if self.black_tags:
                blacklisted = [tag for tag in tags if tag in self.black_tags]
                if blacklisted:
                    continue

            # survived all filters!
            self.note_titles[note_id] = title
            self.json_note_ids[note_id] = self.next_id()
            if tags:
                self.note_tags[note_id] = tags
                for tag in tags:
                    self.tag_notes[tag].add(note_id)

            for citekey in citekeys:
                self.citing_notes[citekey].add(note_id)

        # now that we know all tags:
        for tag in sorted(self.tag_notes.keys()):
            self.json_tag_ids[tag] = self.next_id()

    def load_bibfile(self):
        if self.bibfile is None:
            return
        self.bib_citekeys = list(Autobib.extract_all_entries(self.bibfile).keys())

    def lazy_gen_citation(self, citekey):
        ck_text = '<div style="color: green"><i>(' + citekey + ')</i></div>'
        if self.bibfile is None:
            if citekey not in self.json_citekey_ids:
                node_id = self.create_text_node(ck_text, raw=True)
                self.json_citekey_ids[citekey] = node_id
        else:
            if citekey not in self.json_citekey_ids:
                d = Autobib.create_bibliography('@' + citekey, self.bibfile, p_citekeys=self.bib_citekeys)
                bib_node_id = self.create_text_node(self.markdown(d[citekey]), raw=True)
                # now create linked node to bib
                ck_node_id = self.next_id()
                rel_id = self.create_relationship_node(ck_node_id, bib_node_id)
                rel_ids = [rel_id]

                # create node that, when unfolded, links to all other citing notes
                notelinks_node_id = self.create_text_node('<div style="background-color: lightgray; color: purple; '
                                                          'font-size: 12px;">&nbsp; <b>Citing:</b> &nbsp;</div>',
                                                          raw=True)
                rel_id = self.create_relationship_node(ck_node_id, notelinks_node_id)
                rel_ids.append(rel_id)
                for citing_note_id in self.citing_notes[citekey]:
                    rel_id = self.create_relationship_node(ck_node_id, self.json_note_ids[citing_note_id])
                    rel_ids.append(rel_id)

                self.json_nodes.append({
                    'dataNodeId': ck_node_id,
                    'name': ck_text,
                    'classAttr': 'SimpleDataNode',
                    'relationships': rel_ids
                })
                self.json_citekey_ids[citekey] = ck_node_id
        return self.json_citekey_ids[citekey]

    @staticmethod
    def cut_after_note_id(text):
        """
        Tries to find the 12/14 digit note ID (at beginning) in text.
        """
        note_ids = re.findall('[0-9.]{12,18}', text)
        if note_ids:
            return note_ids[0]

    def get_note_id_of_file(self, filn):
        """
        Return the note id of the file named filn or None.
        """
        if filn.endswith(self.extension):
            # we have a markdown file
            note_id = self.cut_after_note_id(os.path.basename(filn))
            if note_id:
                if os.path.basename(filn).startswith(note_id):
                    return note_id

    def note_file_by_id(self, note_id):
        """
        Find the file for note_id.
        """
        return self.project.note_file_by_id(note_id)

    def extract_tags_and_citekeys(self, file):
        """
        Extract #tags from file.
        Returns all words starting with `#`.
        To be precise, it returns everything that matches RE_TAGS_PY.
        """
        tags = set()
        full_p = file
        with open(full_p, mode='r', encoding='utf-8') as f:
            text = f.read()
            for line in text.split('\n'):
                line = line.strip()
                for tag in re.findall(ZkConstants.RE_TAGS_PY, line):
                    tags.add(tag[0])
        citekeys = Autobib.find_citations(text, self.bib_citekeys)
        return tags, citekeys

    @staticmethod
    def split_into_paragraphs(text):
        paras = []
        in_code_block = False

        current_para = ''
        for line in text.split('\n'):
            if not line:
                if not in_code_block:
                    paras.append(current_para)
                    current_para = ''
                    continue
            if line.startswith('~~~') or line.startswith('```'):
                line = line.replace('~~~', '```')
                in_code_block = not in_code_block
            current_para += line + '\n'
        if current_para.strip():
            paras.append(current_para)
        return paras

    def handle_local_imgs(self, text):
        """Check for local images and try to copy them to imgs/"""
        new_text = text
        for pre, path, post, opt in ZkConstants.Img_Matcher.findall(text):
            if not path.startswith('http'):
                source_path = os.path.join(self.project.folder, path)
                if os.path.exists(source_path):
                    dest_path = os.path.join(self.img_folder, os.path.basename(path))
                    shutil.copy2(source_path, dest_path)
                    # scale img wide
                    size = self.get_image_size(dest_path)
                    if not size:
                        print('\nError: unknown image format:', source_path)
                        continue

                    dest_rel_path = os.path.join(self.img_folder_rel, os.path.basename(path))
                    if self.base_url:
                        dest_rel_path = '{}/{}/{}'.format(self.base_url, self.img_folder_rel, os.path.basename(path))
                        dest_path = dest_rel_path

                    w, h = size
                    max_width = self.max_img_width
                    if w > max_width:
                        m = max_width / w
                        h *= m
                        w = max_width
                        h = int(h)

                    # now replace link
                    orig_markdown = pre + path + post + opt
                    alt_text = re.findall('(\[.*\])', pre)
                    if alt_text:
                        alt_text = alt_text[0]
                    else:
                        alt_text = ''
                    dest_markdown = '<a href="{}" target="_blank"><img src="{}" alt="{}" style="max-width:100%;"' \
                                    ' max-height="50%"><p>{}</p></a>'.format(dest_rel_path, dest_path, alt_text,
                                                                             alt_text[1:-1])
                    new_text = new_text.replace(orig_markdown, dest_markdown)
        return new_text

    @staticmethod
    def get_image_size(img):
        """
        Determine the image type of img and return its size.
        """
        with open(img, 'rb') as f:
            head = f.read(24)
            if len(head) != 24:
                return
            if imghdr.what(img) == 'png':
                check = struct.unpack('>i', head[4:8])[0]
                if check != 0x0d0a1a0a:
                    return
                width, height = struct.unpack('>ii', head[16:24])
            elif imghdr.what(img) == 'gif':
                width, height = struct.unpack('<HH', head[6:10])
            elif imghdr.what(img) == 'jpeg':
                try:
                    f.seek(0)  # Read 0xff next
                    size = 2
                    ftype = 0
                    while not 0xc0 <= ftype <= 0xcf:
                        f.seek(size, 1)
                        byte = f.read(1)
                        while ord(byte) == 0xff:
                            byte = f.read(1)
                        ftype = ord(byte)
                        size = struct.unpack('>H', f.read(2))[0] - 2
                    # SOFn block
                    f.seek(1, 1)  # skip precision byte.
                    height, width = struct.unpack('>HH', f.read(4))
                except Exception:
                    return
            else:
                return
            return width, height

    def code_highlight(self, para):
        first_line = para.split('\n', 1)[0]
        first_line = '#!' + first_line.replace('`', '')
        lexer = guess_lexer(first_line)
        formatter = HtmlFormatter(linenos=False, cssclass="highlight")
        code = '\n'.join(para.split('\n')[1:-2])
        html = '<div id="scoped-content"><style type="text/css">' + formatter.get_style_defs('.highlight') + '</style>'
        html += highlight(code, lexer, formatter)
        html += '</div>'
        return html

    def create_nodes_from_note(self, noteid):
        """
        Note links after paragraph
        """
        filn = self.note_file_by_id(note_id=noteid)
        if not filn:
            return None
        node_id = self.json_note_ids[noteid]

        with open(filn, mode='r', encoding='utf-8', errors='ignore') as f:
            whole_text = f.read()
            whole_text = self.handle_local_imgs(whole_text)
            paras = self.split_into_paragraphs(whole_text)

        rel_ids = []
        if noteid in self.note_tags:
            # append a separator
            para_id = self.create_text_node('<div style="background-color: lightgray; color: purple; font-size: 12px;">'
                                            '&nbsp; <b>Tags:</b> &nbsp;</div>', raw=True)
            rel_ids.append(self.create_relationship_node(node_id, para_id))
            for tag in self.note_tags[noteid]:
                tag_id = self.json_tag_ids[tag]
                rel_id = self.create_relationship_node(node_id, tag_id)
                rel_ids.append(rel_id)

            if not self.vertical_layout:
                # append a separator
                para_id = self.create_text_node('<div style="  color: purple"> &nbsp; <b></b> &nbsp;'
                                                + '&nbsp;' * 60 + '</div>', raw=True)
                rel_ids.append(self.create_relationship_node(node_id, para_id))

        for para in paras:
            if para == '':
                continue
            para_rel_ids = []
            linked_note_ids = ZkConstants.Link_Matcher.findall(para)
            linked_note_ids = [l[1] for l in linked_note_ids]
            is_code_block = False
            if para.startswith('```'):
                para = self.code_highlight(para)
                is_code_block = True
            para_id = self.create_text_node(para, raw=is_code_block)
            rel_ids.append(self.create_relationship_node(node_id, para_id))
            if linked_note_ids:
                # append a separator
                para_id = self.create_text_node('<div style="background-color: lightgray; color: purple; font-size: '
                                                '12px;">&nbsp; <b>Links:</b> &nbsp;</div>', raw=True)
                rel_ids.append(self.create_relationship_node(node_id, para_id))
            for note_id in [self.cut_after_note_id(x) for x in linked_note_ids]:
                if note_id not in self.json_note_ids:
                    continue
                rel_id = self.create_note_link_node(note_id, para_id)
                rel_ids.append(rel_id)

            if linked_note_ids:
                    # append a separator
                    if self.vertical_layout:
                        para_id = self.create_text_node('<div style="background-color: lightgray; color: purple; font-size:3px">&nbsp;'
                                                        ' &nbsp;</div>', raw=True)
                    else:
                        para_id = self.create_text_node('<div style="background-color: lightgray; color: purple">&nbsp;'
                                                        ' <b>▪</b> &nbsp;</div>', raw=True)
                    rel_ids.append(self.create_relationship_node(node_id, para_id))

            if is_code_block:
                # no citekeys in raw html
                continue

            citekeys = Autobib.find_citations(para, self.bib_citekeys)

            if citekeys:
                # append a separator
                # para_id = self.create_text_node(' &nbsp; &nbsp;')
                para_id = self.create_text_node('<div style="background-color: lightgray; color: purple; font-size: '
                                                '12px;">&nbsp; <b>Cited:</b> &nbsp;</div>', raw=True)
                rel_ids.append(self.create_relationship_node(node_id, para_id))
            for citekey in citekeys:
                ck_node_id = self.lazy_gen_citation(citekey)
                rel_id = self.create_relationship_node(node_id, ck_node_id)
                rel_ids.append(rel_id)
            if citekeys:
                # append a separator
                if self.vertical_layout:
                    para_id = self.create_text_node(
                        '<div style="background-color: lightgray; color: purple; font-size:3px">&nbsp;'
                        ' &nbsp;</div>', raw=True)
                else:
                    para_id = self.create_text_node('<div style="background-color: lightgray; color: purple">&nbsp;'
                                                    ' <b>▪</b> &nbsp;</div>', raw=True)
                rel_ids.append(self.create_relationship_node(node_id, para_id))

        # embed the chunks into a note node
        self.json_nodes.append({
            'dataNodeId': node_id,
            'name': '<div style="color: blue">[' + self.note_titles[noteid] + ']</div>',
            'classAttr': 'SimpleDataNode',
            'relationships': rel_ids
        })

    def create_text_node(self, text, raw=False):
        node_id = self.next_id()
        if not raw:
            text = self.markdown(text)
        self.json_nodes.append({
            'dataNodeId': node_id,
            'name': text,
            'classAttr': 'SimpleDataNode',
            'relationships': []
        })
        return node_id

    def create_note_link_node(self, to_noteid, from_nodeid):
        to_id = self.json_note_ids[to_noteid]
        rel_id = self.create_relationship_node(from_nodeid, to_id)
        return rel_id

    def create_relationship_node(self, from_id, to_id):
        node_id = self.next_id()
        self.json_nodes.append({
            'dataNodeId': node_id,
            'classAttr': 'HasDetail',
            'from': from_id,
            'to': to_id
        })
        return node_id

    def create_all_tags_node(self):
        # also create all tag notes
        node_id = self.next_id()
        rel_ids = []

        num_tags = len(self.tag_notes.keys())
        i = 0

        for tag in sorted(self.tag_notes.keys()):
            i += 1
            self.progress_callback(i, num_tags, 'Processing tag     {}'.format(tag))
            note_ids = self.tag_notes[tag]
            tag_node = self.json_tag_ids[tag]
            tag_rel_ids = []
            for note_id in note_ids:
                rel_id = self.create_relationship_node(tag_node, self.json_note_ids[note_id])
                tag_rel_ids.append(rel_id)
            self.json_nodes.append({
                'dataNodeId': tag_node,
                'name': '<div style="color: purple">' + tag + '</div>',
                'classAttr': 'SimpleDataNode',
                'relationships': tag_rel_ids
            })
            rel_id = self.create_relationship_node(node_id, tag_node)
            rel_ids.append(rel_id)
        self.json_nodes.append({
            'dataNodeId': node_id,
            'name': '<div style="color: purple">#tags</div>',
            'classAttr': 'SimpleDataNode',
            'relationships': rel_ids
        })
        self.finish_callback()
        return node_id

    def create_all_notes_node(self):
        json_note_ids = sorted(list(self.json_note_ids.keys()))
        node_id = self.next_id()
        rel_node_ids = []

        for note_id in json_note_ids:
            rel_id = self.create_note_link_node(note_id, node_id)
            rel_node_ids.append(rel_id)
        self.json_nodes.append({
            'dataNodeId': node_id,
            'name': '<div style="color: blue">[notes]</div>',
            'classAttr': 'SimpleDataNode',
            'relationships': rel_node_ids
        })
        return node_id

    def create_all_citations_node(self):

        citekeys = sorted(self.bib_citekeys)
        node_id = self.next_id()
        rel_ids = []

        num_ck = len(citekeys)
        i = 0
        citekey = '(None)'
        for citekey in citekeys:
            i += 1
            if citekey in self.citing_notes:
                self.progress_callback(i, num_ck, 'Processing citekey {}'.format(citekey))
                rel_id = self.create_relationship_node(node_id, self.json_citekey_ids[citekey])
                rel_ids.append(rel_id)
        # make sure we report 100%
        if num_ck:
            self.progress_callback(i, num_ck, 'Processing citekey {}'.format(citekey))

        self.json_nodes.append({
            'dataNodeId': node_id,
            'name': '<div style="color: green">@citations</div>',
            'classAttr': 'SimpleDataNode',
            'relationships': rel_ids
        })
        self.finish_callback()
        return node_id

    def create_root_node(self):
        n_id = self.create_all_notes_node()
        t_id = self.create_all_tags_node()
        c_id = self.create_all_citations_node()

        root_id = self.next_id()
        rel_ids = [self.create_relationship_node(root_id, t_id),
                   self.create_relationship_node(root_id, n_id),
                   self.create_relationship_node(root_id, c_id)]
        self.json_nodes.append({
            'dataNodeId': root_id,
            'name': 'Zettelkasten',
            'classAttr': 'SimpleDataNode',
            'relationships': rel_ids
        })
        return root_id

    def create_all_nodes(self):
        num_notes = len(self.note_titles.keys())
        i = 0
        fmt = 'Processing note    {} {}                              '
        for note_id in sorted(self.note_titles.keys()):
            i += 1
            nice_title = self.note_titles[note_id]
            if len(nice_title) > 30:
                nice_title = nice_title[:27] + '...'
            self.progress_callback(i, num_notes, fmt.format(note_id, nice_title))
            self.create_nodes_from_note(note_id)
        self.finish_callback()
        root_id = self.create_root_node()
        return root_id

    def create_json(self):
        root_id = self.create_all_nodes()
        json_dict = {
            'listOfAllDataNodes': self.json_nodes,
            'rootNode': root_id
        }
        json_s = json.dumps(json_dict)
        if False:
            with open(os.path.join(self.out_folder, 'out.json'), mode='w', encoding='utf-8') as f:
                f.write(json_s)
        return json_s

    def create_html(self):
        self.load_bibfile()
        self.find_all_notes_all_tags()

        json_s = self.create_json()
        with open(os.path.join(self.home, 'data', 'setevi-template.html'), mode='r', encoding='utf-8',
                  errors='ignore') as f:
            lines = f.readlines()
        output_lines = []
        for line in lines:
            if '/*GENERATED JSON*/' in line:
                line = line.replace('/*GENERATED JSON*/', json_s)
            output_lines.append(line)

        with open(os.path.join(self.out_folder, 'index.html'), mode='w', encoding='utf-8') as f:
            for line in output_lines:
                f.write(line)
