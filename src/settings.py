import jstyleson as json


def get_settings(filn='../settings_default.json', raw=False):
    with open(filn,
              mode='r', encoding='utf-8', errors='ignore') as f:
        txt = f.read()
        if raw:
            return txt
        else:
            return json.loads(txt)

# todo make QObject that emits settings changed / slot interface for eg Project class