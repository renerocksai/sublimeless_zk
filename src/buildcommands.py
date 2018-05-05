import sys
import os
from subprocess import Popen, PIPE, STDOUT
import shutil
import traceback
from json import JSONDecodeError
import jstyleson

# Ensure we have a path, assume bash is in use
if sys.platform != 'win32':
    p = Popen('bash -l -i', stdin=PIPE, stdout=PIPE, shell=True)
    stdout, stderr = p.communicate(bytes('echo $PATH', 'utf-8'))
    stdout = stdout.decode('utf-8', errors='ignore')
    os.environ['PATH'] = stdout


class BuildCommands(object):
    F = 'build_commands.json'

    def __init__(self, home_path, templates_path):
        """
        home_path = settings path
        templates_path = frozen templates path
        """
        self.home_path = home_path
        self.templates_path = templates_path
        self.filn = os.path.join(home_path, self.F)
        self.commands = {}
        self.prepare()
        self.reload()

    def prepare(self):
        """
        Prepare the settings folder with a default file.
        """
        if not os.path.exists(self.filn):
            shutil.copy2(os.path.join(self.templates_path, self.F), self.filn)
        return

    def reload(self):
        """
        Reload the JSON file
        """
        try:
            with open(self.filn, mode='r', encoding='utf-8', errors='ignore') as f:
                ret = jstyleson.load(f)
        except JSONDecodeError as e:
            ret = {}
        self.commands = ret
        return ret

    def run_build_command(self, name, vars_dict):
        """
        Run the named build command with vars substituted by values in vars_dict
        Silently ignore non-existing commands
        """
        args = self.commands.get(name, dict())
        args = args.get('run', list())
        args = [a.format(**vars_dict) for a in args]
        return self._run_command(args, vars_dict)
        
    def _run_command(self, args, vars_dict):
        """
        Run program specified as args: [executable, arg, arg, arg, arg...]
        Replace all the {variable}s in args by their values in vars_dict
        """
        args = [arg.format(**vars_dict) for arg in args]
        stdout = 'error'
        returncode = -1
        path = os.environ['PATH']
        if args:
            try:
                p = Popen(args, stdin=None, stdout=PIPE, stderr=STDOUT)
                stdout, _ = p.communicate()
                stdout = stdout.decode('utf-8', errors='ignore').replace('\r', '')
                returncode = p.returncode
            except FileNotFoundError:
                stdout = f'Executable ({args[0]}) not found in {path}'
            except:
                stdout = traceback.format_exc()
        return returncode, stdout, args
