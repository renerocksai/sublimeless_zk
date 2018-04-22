#!/usr/bin/env python3
DEPLOY_DIR = '_deploy'

version = '0.0'
prefix = 'pre'
release_notes = '''
This release contains:

*

**New features:**

* 

See the [README](https://github.com/renerocksai/sublimeless_zk) for intstructions.

**Released files:**

* **macOS:** `sublimeless_zk-{prefix}-{version}-macOS.zip`
* **Windows 10:** `sublimeless_zk-{prefix}-{version}-win10.zip` 
'''.format(version=version, prefix=prefix)

# for bash scripts and windows .cmd
if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1].lower() == '--version':
            print(version)
        elif sys.argv[1].lower() == '--prefix':
            print(prefix)
        elif sys.argv[1].lower() == '--release-notes':
            print(release_notes)
        elif sys.argv[1].lower() == '--tag':
            print('sublimeless_zk-{}-{}'.format(prefix, version))
        elif sys.argv[1].lower() == '--init':
            import os
            import shutil
            if os.path.exists(DEPLOY_DIR):
                shutil.rmtree(DEPLOY_DIR)
            os.makedirs(DEPLOY_DIR)
        elif sys.argv[1].lower() == '--deploy-dir':
            print(DEPLOY_DIR)
        elif sys.argv[1].lower() == '--rename-dist':
            import os
            # effing windows is sloooow
            import time
            time.sleep(3)
            src = 'dist'
            dest = 'sublimeless_zk-{prefix}-{version}-win10'.format(version=version, prefix=prefix)
            os.rename(src, os.path.join(DEPLOY_DIR, dest))
    else:
        print(version, prefix)
