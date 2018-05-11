import os
from pathlib import Path
import jstyleson as json


class AppState:
    def __init__(self):
        self.recent_projects = []
        self.open_notes = {}
        self.home = str(Path.home())
        self.file_name = os.path.join(self.home, 'sublimeless_zk-state.json')
        self.load()

    def load(self):
        if not os.path.exists(self.file_name):
            self.recent_projects = [self.get_default_project_folder()]
            self.open_notes = {}
        else:
            with open(self.file_name,
                      mode='r', encoding='utf-8', errors='ignore') as f:
                txt = f.read()
                json_dict = json.loads(txt)
                self.recent_projects = json_dict.get('recent_projects')
                if not self.recent_projects:
                    self.recent_projects = [self.get_default_project_folder()]
                self.open_notes = json_dict.get('open_notes', {})
        self.save()

    def save(self):
        json_dict = {'recent_projects': self.recent_projects, 'open_notes': self.open_notes}
        with open(self.file_name, mode='w', encoding='utf-8', errors='ignore') as f:
            f.write(json.dumps(json_dict))

    def get_default_project_folder(self):
        return os.path.join(self.home, 'zettelkasten')
