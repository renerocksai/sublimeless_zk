import re
import os
from collections import defaultdict
from subprocess import Popen, PIPE
import glob


class Autobib:
    """
    Static class to group all auto-bibliography functions.
    """
    citekey_matcher = re.compile('^@.*{([^,]*)[,]?')
    author_matcher = re.compile(r'^\s*author\s*=\s*(.*)', re.IGNORECASE)
    title_matcher = re.compile(r'^\s*title\s*=\s*(.*)', re.IGNORECASE)
    year_matcher = re.compile(r'^\s*year\s*=\s*(.*)', re.IGNORECASE)

    @staticmethod
    def look_for_bibfile(folder):
        if folder:
            pattern = os.path.join(folder, '*.bib')
            bibs = glob.glob(pattern)
            if bibs:
                print('Using local', bibs[0])
                return bibs[0]

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
        current_citekey = None
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
                    authors = Autobib.parse_authors(authors)
                    entries[current_citekey]['authors'] = authors
                    continue
                match = Autobib.title_matcher.findall(line)
                if match:
                    title = match[0]
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
        authors = line.split('and')
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
        citekeys_re = [re.escape('@' + citekey) for citekey in citekeys]
        citekeys_re.extend([re.escape('[#' + citekey) for citekey in citekeys])
        founds_raw = re.findall('|'.join(list(citekeys_re)), text)
        founds = []
        for citekey in founds_raw:
            if not citekey:
                # empty strings if no citekeys
                continue
            if citekey.startswith('[#'):
                citekey = citekey[2:]
            else:
                citekey = citekey[1:]
            founds.append(citekey)
        return set(founds)

    @staticmethod
    def create_bibliography(text, bibfile, p_citekeys=None, pandoc='pandoc'):
        """
        Create a bibliography for all citations in text in form of a dictionary.
        """
        if p_citekeys is not None:
            citekeys = p_citekeys
        else:
            citekeys = Autobib.extract_all_citekeys(bibfile)
        if not citekeys:
            return {}
        citekeys = Autobib.find_citations(text, citekeys)
        citekey2bib = {}
        for citekey in citekeys:
            pandoc_input = '@' + citekey
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
        bib = '(no bib generated)'
        if len(pdsplit) >= 1:
            citation = pdsplit[0]
        if len(pdsplit) >= 2:
            bib = pdsplit[1]
        citation = citation.replace('\n', ' ')
        bib = bib.replace('\n', ' ')
        return citation, bib

    @staticmethod
    def run(pandoc_bin, bibfile, stdin):
        args = [pandoc_bin, '-t', 'plain', '--bibliography', bibfile]
        # using universal_newlines here gets us into decoding troubles as the
        # encoding then is guessed and can be ascii which can't deal with
        # unicode characters. hence, we handle \r ourselves
        p = Popen(args, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate(bytes(stdin, 'utf-8'))
        # make me windows-safe
        stdout = stdout.decode('utf-8', errors='ignore').replace('\r', '')
        stderr = stderr.decode('utf-8', errors='ignore').replace('\r', '')
        # print('pandoc says:', stderr)
        return stdout
