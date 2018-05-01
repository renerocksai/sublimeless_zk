# -*- coding: utf-8 -*-

import os
import glob
import re
from subprocess import Popen, PIPE
from collections import defaultdict
import traceback
from bibtexparser.customization import convert_to_unicode


class Autobib:
    """
    Static class to group all auto-bibliography functions.
    """
    citekey_matcher = re.compile('^@.*{([^,]*)[,]?')
    author_matcher = re.compile(r'^\s*author\s*=\s*(.*)', re.IGNORECASE)
    editor_matcher = re.compile(r'^\s*editor\s*=\s*(.*)', re.IGNORECASE)
    title_matcher = re.compile(r'^\s*title\s*=\s*(.*)', re.IGNORECASE)
    year_matcher = re.compile(r'^\s*year\s*=\s*(.*)', re.IGNORECASE)

    citekey_stops = r"[@',\#}{~%\[\]\s]"

    @staticmethod
    def look_for_bibfile(project):
        """
        Look for a bib file in the view's folder.
        If no bib file there, then query the setting.
        """
        folder = project.folder
        if folder:
            pattern = os.path.join(folder, '*.bib')
            bibs = glob.glob(pattern)
            if bibs:
                print('Using local', bibs[0])
                return bibs[0]
        # try the setting
        bibfile = project.settings.get('bibfile', None)
        if bibfile:
            if os.path.exists(bibfile):
                print('Using global', bibfile)
                return bibfile
            else:
                print('bibfile not found:', bibfile)
                return None

    @staticmethod
    def extract_all_citekeys(bibfile):
        """
        Parse the bibfile and return all citekeys.
        """
        citekeys = set()
        if not os.path.exists(bibfile):
            print('bibfile not found:', bibfile)
            return []
        with open(bibfile, mode='r', encoding='utf-8') as f:
            for line in f:
                match = Autobib.citekey_matcher.findall(line)
                if not match:
                    continue
                citekeys.add(match[0])
        return citekeys

    @staticmethod
    def extract_all_entries(bibfile):
        """
        Return dict: {citekey: {title, authors, year}}
        """
        entries = defaultdict(lambda: defaultdict(str))
        if not os.path.exists(bibfile):
            print('bibfile not found:', bibfile)
            return {}
        with open(bibfile, mode='r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.endswith(','):
                    line = line[:-1]
                match = Autobib.citekey_matcher.findall(line)
                if match:
                    current_citekey = match[0]
                    continue
                match = Autobib.author_matcher.findall(line)
                if match:
                    authors = match[0]
                    authors = convert_to_unicode({'author': authors})['author']
                    authors = Autobib.parse_authors(authors)
                    entries[current_citekey]['authors'] = authors
                    continue
                match = Autobib.editor_matcher.findall(line)
                if match:
                    editors = match[0]
                    editors = convert_to_unicode({'editor': editors})['editor']
                    editors = Autobib.parse_authors(editors)
                    entries[current_citekey]['editors'] = authors
                    continue
                match = Autobib.title_matcher.findall(line)
                if match:
                    title = match[0]
                    title = convert_to_unicode({'title': title})['title']
                    title = Autobib.remove_latex_commands(title)
                    entries[current_citekey]['title'] = title
                    continue
                match = Autobib.year_matcher.findall(line)
                if match:
                    year = match[0]
                    year = Autobib.remove_latex_commands(year)
                    entries[current_citekey]['year'] = year
                    continue
        return entries

    @staticmethod
    def parse_authors(line):
        line = Autobib.remove_latex_commands(line)
        authors = line.split(' and')
        author_tuples = []
        for author in authors:
            first = ''
            last = author.strip()
            if ',' in author:
                last, first = [x.strip() for x in author.split(',')][:2]
            author_tuples.append((last, first))
        if len(author_tuples) > 2:
            authors = '{} et al.'.format(author_tuples[0][0])  # last et al
        else:
            authors = ' & '.join(x[0] for x in author_tuples)
        return authors

    @staticmethod
    def remove_latex_commands(s):
        """
        Simple function to remove any LaTeX commands or brackets from the string,
        replacing it with its contents.
        """
        chars = []
        FOUND_SLASH = False

        for c in s:
            if c == '{':
                # i.e., we are entering the contents of the command
                if FOUND_SLASH:
                    FOUND_SLASH = False
            elif c == '}':
                pass
            elif c == '\\':
                FOUND_SLASH = True
            elif not FOUND_SLASH:
                chars.append(c)
            elif c.isspace():
                FOUND_SLASH = False

        return ''.join(chars)

    @staticmethod
    def find_citations(text, citekeys):
        """
        Find all mentioned citekeys in text
        """
        citekey_stops = r"[@',\#}{~%\[\]\s]"
        citekeys_re = [re.escape('@' + citekey) for citekey in citekeys]
        citekeys_re.extend([re.escape('[#' + citekey) for citekey in citekeys])
        citekeys_re = [ckre + citekey_stops for ckre in citekeys_re]
        finder = re.compile('|'.join(citekeys_re))
        founds_raw = finder.findall(text)
        founds = []
        for citekey in founds_raw:
            if citekey.startswith('[#'):
                citekey = citekey[1:]
            founds.append(citekey[:-1])
        founds = set(founds)
        return founds

    @staticmethod
    def create_bibliography(text, bibfile, pandoc='pandoc'):
        """
        Create a bibliography for all citations in text in form of a dictionary.
        """
        citekeys = Autobib.extract_all_citekeys(bibfile)
        if not citekeys:
            return {}
        citekeys = Autobib.find_citations(text, citekeys)
        citekey2bib = {}
        for citekey in citekeys:
            pandoc_input = citekey.replace('#', '@', 1)
            pandoc_out = Autobib.run(pandoc, bibfile, pandoc_input)
            citation, bib = Autobib.parse_pandoc_out(pandoc_out)
            citekey2bib[citekey] = bib
        return citekey2bib

    @staticmethod
    def parse_pandoc_out(pandoc_out):
        """
        Splits pandoc output into citation and bib part
        """
        #print('pandoc_out:', repr(pandoc_out))
        pdsplit = pandoc_out.split('\n\n')
        citation = '(no citation generated)'
        bib =  '(no bib generated)'
        if len(pdsplit) >= 1:
            citation = pdsplit[0]
        if len(pdsplit) >= 2:
            bib = pdsplit[1]
        citation = citation.replace('\n', ' ')
        bib = bib.replace('\n', ' ')
        return citation, bib

    @staticmethod
    def run(pandoc_bin, bibfile, stdin):
        stdout = ''
        stderr = ''
        try:
            args = [pandoc_bin, '-t', 'plain',
                    f'--filter',
                    f'{os.path.join(os.path.dirname(pandoc_bin), "pandoc-citeproc")}',
                    '--bibliography', bibfile]
            # using universal_newlines here gets us into decoding troubles as the
            # encoding then is guessed and can be ascii which can't deal with
            # unicode characters. hence, we handle \r ourselves
            p = Popen(args, stdin=PIPE, stdout=PIPE, stderr=PIPE)
            stdout, stderr = p.communicate(bytes(stdin, 'utf-8'))
            # make me windows-safe
            stdout = stdout.decode('utf-8', errors='ignore').replace('\r', '')
            stderr = stderr.decode('utf-8', errors='ignore').replace('\r', '')
            # print('pandoc says:', stderr)
        except FileNotFoundError:
            print(f'Pandoc executable ({pandoc_bin}) not found')
            Autobib.log_exception(args, True)
        except:
            Autobib.log_exception(args, True)
        return stdout

    @staticmethod
    def log_exception(arg, exception=False):
        with open('/tmp/sublimeless_zk-exception.txt', 'a', encoding='utf-8', errors='ignore') as f:
            f.write(f'{arg}\n')
            if exception:
                f.write(traceback.format_exc())
            f.flush()
