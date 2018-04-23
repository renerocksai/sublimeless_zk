import jstyleson as json
from pathlib import Path
import os
import shutil
import sys

settings_filn = os.path.join(Path.home(), 'sublimeless_zk-settings.json')


def base_dir():
    if getattr(sys, 'frozen', False):
        # frozen
        base_dir = os.path.dirname(sys.executable)
    else:
        # unfrozen
        base_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..')
    return base_dir


def get_settings(raw=False):
    if not os.path.exists(settings_filn):
        # copy template
        src_path = os.path.join(base_dir(), 'sublimeless_zk-settings.json')
        shutil.copy2(src_path, settings_filn)
    with open(settings_filn,
              mode='r', encoding='utf-8', errors='ignore') as f:
        txt = f.read()
        if raw:
            return txt
        else:
            return json.loads(txt)


def get_pandoc():
    settings = get_settings()
    guesses = [settings.get('path_to_pandoc', 'pandoc')]
    guesses.extend(['pandoc', '/usr/local/bin/pandoc', '/usr/bin/pandoc'])
    for attempt in guesses:
        if os.system(f'{attempt} --help') == 0:
            return attempt
    return None


# todo make QObject that emits settings changed / slot interface for eg Project class
