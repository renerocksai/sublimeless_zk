import os
import re
import datetime

from settings import get_settings


class Project:
    def __init__(self, project_folder):
        self.folder = project_folder
        self.bibfile = None
        self.tags = set()
        self.notes = {}         # noteid : path
        self.settings = None
        self.reload_settings()
        self.refresh_notes()

    def get_saved_searches_filn(self):
        return os.path.join(self.folder, '.saved_searches.zks')

    def get_search_results_filn(self):
        return os.path.join(self.folder, '.search_results.zkr')

    def reload_settings(self):
        self.settings = get_settings()

    def get_note_id_of_file(self, filn):
        """
        Return the note id of the file named filn or None.
        """
        settings = self.settings
        extension = settings.get('markdown_extension', '.md')
        if filn.endswith(extension):
            # we have a markdown file
            note_id = self.cut_after_note_id(os.path.basename(filn))
            if note_id:
                if os.path.basename(filn).startswith(note_id):
                    return note_id

    def get_note_id_and_title_of(self, editor):
        """
        Return the note id  and title of the given view.
        """
        filn = editor.file_name
        origin_id = None
        origin_title = None
        if filn:
            origin_id = self.get_note_id_of_file(filn)
            origin_title = ''
            if origin_id:
                # split off title and replace extension
                origin_title = filn.rsplit(origin_id)[1].strip().rsplit('.')[0]
        return origin_id, origin_title

    def timestamp(self):
        if self.settings.get('seconds_in_id', False):
            return '{:%Y%m%d%H%M%S}'.format(datetime.datetime.now())
        else:
            return '{:%Y%m%d%H%M}'.format(datetime.datetime.now())

    @staticmethod
    def cut_after_note_id(text):
        """
        Tries to find the 12/14 digit note ID (at beginning) in text.
        """
        note_ids = re.findall('[0-9.]{12,18}', text)
        if note_ids:
            return note_ids[0]

    def get_link_pre_postfix(self):
        settings = self.settings
        link_prefix = '[['
        link_postfix = ']]'
        if not settings.get('double_brackets', True):
            link_prefix = '['
            link_postfix = ']'
        return link_prefix, link_postfix

    def refresh_notes(self):
        extension = self.settings.get('markdown_extension', '.md')
        candidates = []
        for root, dirs, files in os.walk(self.folder):
            candidates.extend([os.path.join(root, f) for f in files if f.endswith(extension)])
        self.notes = {}
        for candidate in candidates:
            note_id = self.cut_after_note_id(candidate)
            if note_id:
                self.notes[note_id] = candidate

    def note_template_handle_date_spec(self, template, note_id):
        if self.settings.get('seconds_in_id', False):
            timestamp = datetime.datetime.strptime(note_id, '%Y%m%d%H%M%S')
        else:
            timestamp = datetime.datetime.strptime(note_id, '%Y%m%d%H%M')
        # now handle the format string(s)
        new_template = template
        for pre, fmt, post in re.findall('({timestamp:\s*)([^\}]*)(})', template):
            spec = pre + fmt + post
            new_template = new_template.replace(spec, timestamp.strftime(fmt))
        return new_template

    def create_note(self, filn, title, origin_id=None, origin_title=None, body=None):
        note_id = os.path.basename(filn).split()[0]
        params = {
                    'title': title,
                    'file': os.path.basename(filn),
                    'path': os.path.dirname(filn),
                    'id': note_id,
                    'origin_id': origin_id,
                    'origin_title': origin_title,
                    # don't break legacy
                    'origin': origin_id,
                  }
        settings = get_settings()
        format_str = settings.get('new_note_template', '')
        if not format_str:
            format_str = u'# {title}\ntags = \n\n'
        else:
            format_str = self.note_template_handle_date_spec(format_str, note_id)
        with open(filn, mode='w', encoding='utf-8') as f:
            f.write(format_str.format(**params))
            if body is not None:
                f.write('\n' + body)
        ''''''
