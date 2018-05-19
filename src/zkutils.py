# stuff that didn't make it anywhere else
import re
import sys
import os
import subprocess


evil_fn_chars_re = re.compile('[\\/:"*?<>|]+')
def sanitize_filename(filename):
    """
    Dis-allow characters not allowed on all platforms
    This is so you can't save '*' which doesn't work on Windows
    which prevents ZK portability.
    """
    return evil_fn_chars_re.sub('-', filename)
    
def split_search_terms(search_string):
    """
    Split a search-spec (for find in files) into tuples:
    (posneg, string)
    posneg: True: must be contained, False must not be contained
    string: what must (not) be contained
    """
    in_quotes = False
    in_neg = False
    pos = 0
    str_len = len(search_string)
    results = []
    current_snippet = ''
    while pos < str_len:
        if search_string[pos:].startswith('""'):
            in_quotes = not in_quotes
            if not in_quotes:
                # finish this snippet
                if current_snippet:
                    results.append((in_neg, current_snippet))
                in_neg = False
                current_snippet = ''
            pos += 2
        elif search_string[pos:].startswith('!!') and not in_quotes and not current_snippet:
            in_neg = True
            pos += 2
        elif search_string[pos] in (' ', '\t') and not in_quotes:
            # push current snippet
            if current_snippet:
                results.append((in_neg, current_snippet))
            in_neg = False
            current_snippet = ''
            pos += 1
        else:
            current_snippet += search_string[pos]
            pos += 1
    if current_snippet:
        results.append((in_neg, current_snippet))
    return [(not in_neg, s) for in_neg, s in results]


def open_hyperlink(hyperlink):
    if sys.platform == 'darwin':
        subprocess.call(['open', hyperlink])
    elif sys.platform == 'win32':
        os.startfile(hyperlink)
    else:
        # assume linux
        subprocess.call(('LD_LIBRARY_PATH="" ; xdg-open  ' + hyperlink), shell=True)

if __name__ == '__main__':
    line = 'hello !!""new world!!!"" this !! is awesome!! is!!n\'t !!it??'
    print(line)
    print('    \n'.join([str(x) for x in split_search_terms(line)]))