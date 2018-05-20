import sys
import os
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtCore import QObject, QTimer, QEventLoop, QThread, QMutexLocker, QMutex


class MyThread(QThread):
    def __init__(self, name):
        super().__init__()
        self.setObjectName(name)

    def run(self):
        print ("RUN Thread", QThread.currentThread().objectName())
        self.exec_()
        print ("EXIT Thread", QThread.currentThread().objectName())


class NotesWatcher(QObject):
    """
    Use like this:
        noteswatcher = NotesWatcher.create(1000)
        def aboutToQuit():
            noteswatcher.quit_thread()
            time.sleep(0.3)    # give it time to terminate
        app.aboutToQuit.connect(aboutToQuit)
        time.sleep(0.1)
        noteswatcher.keep_going()   # fire once to get things started
    """
    files_changed_on_disk = pyqtSignal(dict)

    def __init__(self, parent=None, timeout=1000):
        super().__init__(parent)
        self.file_modifications = {}
        self.blacklist = set()
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timeout = timeout
        self._thread = None
        self._mutex = QMutex()

    def start_thread(self):
        """
        This is called in the create method and starts up the thread
        """
        return self._thread.start()
    
    def quit_thread(self):
        """
        Connect this to your app's aboutToQuit handler
        """
        self._thread.quit()
        time.sleep(0.2)
    
    def keep_going(self):
        """
        You call this when you want the watcher to keep watching.
        Watching will start after timeout milliseconds.
        The delay is there so you can call this method immediately after 
        having received the files_changed_on_disk signal
        """
        self.timer.start(self.timeout)

    def thread_started(self):
        pass

    @staticmethod
    def create(timeout=1000):
        noteswatcher = NotesWatcher()
        noteswatcher._thread = MyThread("Watcher")
        noteswatcher.moveToThread(noteswatcher._thread)
        noteswatcher._thread.started.connect(noteswatcher.thread_started)
        noteswatcher.files_changed_on_disk.connect(watch_result)
        noteswatcher.timer.timeout.connect(noteswatcher.watch_open_files)
        noteswatcher.start_thread()
        return noteswatcher

    def on_file_open(self, file_name):
        """
        Add to watchlist with current mtime
        """
        #print(f'on_file_open {file_name} in', QThread.currentThread().objectName())
        mtime = self._mtime(file_name)
        if mtime:
            with QMutexLocker(self._mutex):
                self.file_modifications[file_name] = mtime
        else:
            self.on_file_closed(file_name)
    
    def on_file_closed(self, file_name):
        """
        Remove from watchlist
        """
        #print(f'on_file_closed {file_name} in', QThread.currentThread().objectName())
        with QMutexLocker(self._mutex):
            self.file_modifications = {fn: mt for fn, mt in self.file_modifications.items() if fn != file_name}
            self.blacklist = set([f for f in self.blacklist if f != file_name])

    def update_open_files(self, open_files):
        """
        Replace watched files by new set of files
        """
        #print(f'update_open_files {open_files} in', QThread.currentThread().objectName())
        self.reset()
        for fn in open_files:
            self.on_file_open(fn)

    def on_ignore_clicked(self, file_name):
        """
        Stop watching a single file until next save
        """
        #print(f'on_ignore_clicked {file_name} in', QThread.currentThread().objectName())
        with QMutexLocker(self._mutex):
            self.blacklist.add(file_name)

    def on_file_saved(self, file_name):
        """
        Remove file from blacklist, update mtime
        """
        #print(f'on_file_saved {file_name} in', QThread.currentThread().objectName())
        with QMutexLocker(self._mutex):
            self.blacklist = set([f for f in self.blacklist if f != file_name])
        self.on_file_open(file_name)
    
    def reset(self):
        with QMutexLocker(self._mutex):
            self.file_modifications = {}
            self.blacklist = set()

    def watch_open_files(self):
        """
        Call (via signal) once to get a dict of changed files with their mtimes
        Always emits files_changed_on_disk
        You can signal this from your receiving end again to continue watching
        Better yet, when receiving the signal, process it, and at the end start
        a QTimer connected to this slot
        """
        modified_files = {}
        #print('watching in', QThread.currentThread().objectName())
        with QMutexLocker(self._mutex):
            for filn, modtime in self.file_modifications.items():
                if filn in self.blacklist:
                    continue
                mtime = self._mtime(filn)
                #print(f'   mtime of {filn}: {mtime}')
                if mtime > modtime:
                    modified_files[filn] = mtime
        self.files_changed_on_disk.emit(modified_files)
        #print('   ', self.file_modifications)
        
    @staticmethod
    def _mtime(file_name):
        if os.path.exists(file_name):
            return os.path.getmtime(file_name)
        return 0


if __name__ == "__main__":
    import time
    from PyQt5.Qt import QApplication
    import tempfile
    
    app = QApplication([])
    QThread.currentThread().setObjectName("MAIN")

    counter = 0
    temp_fn = tempfile.mktemp()
    with open(temp_fn, 'wt') as f:
        f.write('line 1')

    def aboutToQuit():
        noteswatcher._thread.quit()
        time.sleep(0.3)
    
    def modify_tempfile(temp_fn, counter):
        with open(temp_fn, 'at') as f:
            f.write(f'\nline{counter}')
    
    def assert_empty(d):
        if d:
            sys.stderr.write('[ERROR] Expected: empty!\n')
        else:
            sys.stderr.write('[OK]\n')
        sys.stderr.flush()

    def assert_modified(d):
        if not d:
            sys.stderr.write('[ERROR] Expected: modified!\n')
        else:
            sys.stderr.write('[OK]\n')
        sys.stderr.flush()

    def watch_result(d):
        global counter
        global temp_fn
        counter += 1
        sys.stderr.write(f'Step {counter:2d}: ')
        if d:
            for k, v in d.items():
                sys.stderr.write(f'{k} : {v}   ')
        if counter == 10:
            assert_empty(d)
            app.quit()
            return
        elif counter == 1:
            assert_empty(d)
            noteswatcher.on_file_open(temp_fn)
        elif counter == 2:
            assert_empty(d)
            modify_tempfile(temp_fn, counter)
        elif counter == 3:
            assert_modified(d)
            noteswatcher.on_ignore_clicked(temp_fn)
        elif counter == 4:
            assert_empty(d)
            modify_tempfile(temp_fn, counter)
        elif counter == 5:
            assert_empty(d)
            noteswatcher.on_file_open(temp_fn)
            modify_tempfile(temp_fn, counter)
        elif counter == 6:
            # we didn't close but opened the open and ignored file again 
            # hence modifications are still ignored
            assert_empty(d)
            noteswatcher.on_file_closed(temp_fn)
        elif counter == 7:
            assert_empty(d)
            noteswatcher.on_file_open(temp_fn)
            modify_tempfile(temp_fn, counter)
        elif counter == 8:
            assert_modified(d)
            noteswatcher.on_file_saved(temp_fn)            
        elif counter == 9:
            assert_empty(d)
        noteswatcher.keep_going()

    noteswatcher = NotesWatcher.create(1000)
    app.aboutToQuit.connect(aboutToQuit)
    time.sleep(0.1)
    noteswatcher.keep_going()   # fire once to get things started
    sys.exit(app.exec_())

    