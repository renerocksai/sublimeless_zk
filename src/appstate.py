import os
from pathlib import Path
import jstyleson as json


class AppState:
    def __init__(self, scratch=False):
        self.recent_projects = []
        self.home = str(Path.home())
        self.file_name = os.path.join(self.home, 'sublimeless_zk-state.json')
        self.homeless = True
        self.scratch = scratch
        if scratch:
            self.recent_projects = ['../zettelkasten']
        else:
            self.load()

    def load(self):
        if not os.path.exists(self.file_name):
            self.recent_projects = ['../zettelkasten']
        else:
            with open(self.file_name,
                      mode='r', encoding='utf-8', errors='ignore') as f:
                txt = f.read()
                json_dict = json.loads(txt)
                self.recent_projects = json_dict.get('recent_folders')
                if not self.recent_projects:
                    self.recent_projects = ['../zettelkasten']
                self.homeless = False


    def save(self):
        json_dict = {'recent_projects': self.recent_projects}
        with open(self.file_name, mode='w', encoding='utf-8', errors='ignore') as f:
            f.write(json.dumps(json_dict))

