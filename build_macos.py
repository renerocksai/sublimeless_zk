from cx_Freeze import setup, Executable
from bundle_version import version
import sys
sys.path.append('src')

includes = ["atexit", "PyQt5.QtCore", "PyQt5.Qt", "PyQt5.QtGui",
            "PyQt5.QtWidgets", "PyQt5.Qsci",
]
includefiles = [
    ('themes/saved_searches.json', 'themes/saved_searches.json'),
    ('themes/search_results.json', 'themes/search_results.json'),
    ('themes/solarized_light.json', 'themes/solarized_light.json'),
    ('themes/monokai.json', 'themes/monokai.json'),
    ('saved_searches_default.md', 'saved_searches_default.md'),
    ('search_results_default.md', 'search_results_default.md'),
    ('sublimeless_zk-settings.json', 'sublimeless_zk-settings.json'),
    ('zettelkasten/201804141018 Welcome.md', 'zettelkasten/201804141018 Welcome.md'),
    ('zettelkasten/rene_shades.png', 'zettelkasten/rene_shades.png'),
    ('app_logo_64.png', 'app_logo_64.png'),
    ('app_picture.png', 'app_picture.png'),
]  #path_platforms

excludes = [
    '_gtkagg', '_tkagg', 'bsddb', 'curses', 'pywin.debugger',
    'pywin.debugger.dbgcon', 'pywin.dialogs', 'tcl',
    'Tkconstants', 'Tkinter', 'scipy', "numpy", "numpy.core"
]
packages = ["os", ]
path = []

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {
                     "includes":      includes,
                     "include_files": includefiles,
                     "excludes":      excludes,
                     "packages":      packages,
                     "path":          path
}

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
exe = None

sublimeless_zk = Executable(
      script="src/sublimeless_zk.py",
      initScript = None,
)

setup(
      name = "Sublimeless_ZK",
      version = version,
      author = 'Rene Schallner',
      description = "Sublimeless_ZK",
      options = {"build_exe": build_exe_options,
                 "bdist_mac": { "iconfile": "if_Note_Book_Alt_86976.icns",
                                "custom_info_plist": "Info.plist",
                                },
                 },
      executables = [sublimeless_zk],
)
