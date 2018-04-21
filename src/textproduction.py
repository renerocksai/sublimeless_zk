import os
from operator import itemgetter
import re


class TextProduction:
    """
    Static class grouping functions for text production from overview notes.
    """
    Link_Matcher = re.compile('(\[+|§)([0-9.]{12,18})(\]+|.?)')

    @staticmethod
    def read_full_note(note_id, project):
        """
        Return contents of note with ID note_id.
        """
        note_file = project.note_file_by_id(note_id)
        if not note_file:
            return None, None
        with open(note_file, mode='r', encoding='utf-8') as f:
            return note_file, f.read()

    @staticmethod
    def embed_note(note_id, project, link_prefix, link_postfix):
        """
        Put the contents of a note into a comment block.
        """
        result_lines = []
        extension = project.settings.get('markdown_extension')
        note_file, content = TextProduction.read_full_note(note_id, project)
        footer = '<!-- (End of note ' + note_id + ') -->'
        if not content:
            header = '<!-- Note not found: ' + note_id + ' -->'
            result_lines.append(header)
        else:
            filename = os.path.basename(note_file).replace(extension, '')
            filename = filename.split(' ', 1)[1]
            header = link_prefix + note_id + link_postfix + ' ' + filename
            header = '<!-- !    ' + header + '    -->'
            result_lines.append(header)
            result_lines.extend(content.split('\n'))
            result_lines.append(footer)
        return result_lines

    @staticmethod
    def expand_links(text, project, replace_lines=False):
        """
        Expand all note-links in text, replacing their lines by note contents.
        """
        result_lines = []
        for line in text.split('\n'):
            link_results = TextProduction.Link_Matcher.findall(line)
            if link_results:
                if not replace_lines:
                    result_lines.append(line)
                for pre, note_id, post in link_results:
                    result_lines.extend(TextProduction.embed_note(note_id,
                                                                  project, pre, post))
            else:
                result_lines.append(line)
        return '\n'.join(result_lines)

    @staticmethod
    def refresh_result(text, project):
        """
        Refresh the result of expand_links with current contents of referenced
        notes.
        """
        result_lines = []
        state = 'default'
        note_id = pre = post = None
        folder = project.folder
        extension = project.settings.get('markdown_extension')
        for line in text.split('\n'):
            if state == 'skip_lines':
                if not line.startswith('<!-- (End of note'):
                    continue
                # insert note
                result_lines.extend(TextProduction.embed_note(note_id, folder,
                    extension, pre, post))
                state = 'default'
                continue

            if line.startswith('<!-- !'):
                # get note id
                note_links = TextProduction.Link_Matcher.findall(line)
                if note_links:
                    pre, note_id, post = note_links[0]
                    state = 'skip_lines'
            else:
                result_lines.append(line)
        return '\n'.join(result_lines)

    @staticmethod
    def expand_link_in(editor, project):
        """
        Expand note-link under cursor inside the current editor
        """

        link_type, link = project.get_link_under_cursor(editor)

        if link_type == 'note_id':
            # we're in a link, so expand it
            pre, post = project.get_link_pre_postfix()
            result_lines = TextProduction.embed_note(link, project, pre, post)
            result_lines.append('')   # append a newline for empty line after exp.
            line_number, index = editor.getCursorPosition()
            # advance to next line
            line_number += 1
            prefix = ''
            if line_number >= editor.lines():
                prefix = '\n'
            editor.setSelection(line_number, 0, line_number, 0)
            editor.replaceSelectedText(prefix + '\n'.join(result_lines))
